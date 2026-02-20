import uuid
from dataclasses import asdict
import datetime
import functools
import requests
from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    session,
    url_for,
    request,
    flash
)
from movie_library.forms import MovieForm, ExtendedMovieForm, RegisterForm, LoginForm, UserProfileForm
from movie_library.models import Movie, User
from movie_library.tmdb import get_featured_indian_movies, get_director
from movie_library import tmdb
from passlib.hash import pbkdf2_sha256


pages = Blueprint(
    "pages", __name__, template_folder="templates", static_folder="static"
)


def login_required(route):
    @functools.wraps(route)
    def route_wrapper(*args, **kwargs):
        if session.get("email") is None:
            return redirect(url_for(".login"))
        
        return route(*args, **kwargs)
    
    return route_wrapper


def fetch_featured_movies():
    api_key = tmdb.get_api_key()
    url = f"https://api.themoviedb.org/3/movie/now_playing?api_key={api_key}&language=en-US&page=1"

    response = requests.get(url).json().get("results", [])

    movies = []
    for movie in response[:8]:
        director = tmdb.get_director(movie["id"])

        movies.append({
            "id": movie["id"],
            "title": movie["title"],
            "poster_path": movie.get("poster_path"),
            "release_date": movie.get("release_date", "N/A"),
            "vote_average": movie.get("vote_average", 0.0),
            "director": director,
        })

    return movies


@pages.route("/")
def home():
    print("Fetching featured Indian movies...")

    data = get_featured_indian_movies()

    movies = []
    for movie in data:
        movie_id = movie["id"]

        movies.append({
            "id": movie_id,
            "title": movie.get("title", "No Title"),
            "poster_path": movie.get("poster_path"),
            "release_date": movie.get("release_date", ""),
            "vote_average": movie.get("vote_average", 0),
            "director": get_director(movie_id)  # TMDB director fetch
        })

    return render_template("home.html", movies=movies)

@pages.route("/index")
@login_required
def index():
    user_data= current_app.db.user.find_one({"email": session["email"]})
    user = User(**user_data)

    movie_data = current_app.db.movie.find({"_id": {"$in": user.movies}})
    movies = [Movie(**movie) for movie in movie_data]

    return render_template(
        "index.html",
        title="Movies Watchlist",
        movies_data=movies,
    )

@pages.route("/register", methods=["GET", "POST"])
def register():
    if session.get("email"):
        return redirect(url_for(".home"))
    
    form = RegisterForm()

    if form.validate_on_submit():
        user = User(
            _id=uuid.uuid4().hex,
            email=form.email.data,
            password=pbkdf2_sha256.hash(form.password.data)
        )

        current_app.db.user.insert_one(asdict(user))

        flash("User registered successfully", "success")

        return redirect(url_for(".login"))

    return render_template("register.html", title="Movies Watchlist - Register", form=form)


@pages.route("/login", methods=["GET", "POST"])
def login():
    if session.get("email"):
        return redirect(url_for(".home"))
    
    form = LoginForm()

    if form.validate_on_submit():
        user_data= current_app.db.user.find_one({"email": form.email.data})
        if not user_data:
            flash("Login credins=tials not correct", category="danger")
            return redirect(url_for(".login"))
        user = User(**user_data)

        if user and pbkdf2_sha256.verify(form.password.data, user.password):
            session["user_id"]= user._id
            session["email"]= user.email

            return redirect(url_for(".home"))
        
        flash("Login credins=tials not correct", category="danger")

    return render_template("login.html", title="Movie Watchelist - Login", form=form)


@pages.route("/logout")
def logout():
    current_theme = session.get("theme")
    session.clear()
    session["theme"] = current_theme
    return redirect(url_for(".login"))


@pages.route("/add", methods=["GET", "POST"])
@login_required
def add_movie():
    form = MovieForm()

    if form.validate_on_submit():
        movie = Movie(
            _id=uuid.uuid4().hex,
            title=form.title.data,
            director=form.director.data,
            year=form.year.data,
        )

        current_app.db.movie.insert_one(asdict(movie))
        current_app.db.user.update_one(
            {"_id": session["user_id"]}, {"$push": {"movies": movie._id}}
        )

        return redirect(url_for(".movie", _id=movie._id))

    return render_template(
        "new_movie.html", title="Movies Watchlist - Add Movie", form=form
    )

@pages.route("/edit/<string:_id>", methods= ["GET", "POST"])
@login_required
def edit_movie(_id: str):
    movie = Movie(**current_app.db.movie.find_one({"_id": _id}))
    form = ExtendedMovieForm(obj=movie)
    if form.validate_on_submit():
        movie.title = form.title.data
        movie.director = form.director.data
        movie.year = form.year.data
        movie.cast = form.cast.data
        movie.series = form.series.data
        movie.tags = form.tags.data
        movie.description = form.description.data
        movie.video_link = form.video_link.data

        current_app.db.movie.update_one(
            {"_id": movie._id},
            {"$set": asdict(movie)}
        )
        return redirect(url_for(".movie", _id=movie._id))
    return render_template("movie_form.html", movie=movie, form=form)

@pages.get("/movie/<string:_id>")
def movie(_id: str):
    movie = Movie(**current_app.db.movie.find_one({"_id": _id}))
    return render_template("movie_details.html", movie=movie)


@pages.get("/movie/<string:_id>/rate")
@login_required
def rate_movie(_id):
    rating = int(request.args.get("rating"))
    current_app.db.movie.update_one({"_id": _id}, {"$set": {"rating": rating}})

    return redirect(url_for(".movie", _id=_id))

@pages.get("/movie/<string:_id>/watch")
@login_required
def watch_today(_id):
    current_app.db.movie.update_one(
        {"_id": _id}, 
        {"$set": {"last_watched": datetime.datetime.today() }}
    )

    return redirect(url_for(".movie", _id=_id))

@pages.get("/toggle-theme")
def toggle_theme():
    current_theme = session.get("theme")
    if current_theme == "dark":
        session["theme"] = "light"
    else:
        session["theme"] = "dark"

    return redirect(request.args.get("current_page"))


@pages.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user_data = current_app.db.user.find_one({"email": session["email"]})
    
    # Ensure user data has all required fields
    if 'name' not in user_data:
        user_data['name'] = ''
    if 'bio' not in user_data:
        user_data['bio'] = ''
    if 'avatar_url' not in user_data:
        user_data['avatar_url'] = ''
    
    user = User(**user_data)
    form = UserProfileForm(obj=user)
    
    # Get movie count
    movie_count = len(user.movies) if user.movies else 0

    if request.method == "POST":
        # Update user profile from submitted form data
        updated_fields = {
            "name": request.form.get("name", "").strip(),
            "bio": request.form.get("bio", "").strip(),
            "avatar_url": request.form.get("avatar_url", "").strip(),
        }

        current_app.db.user.update_one(
            {"_id": user._id},
            {"$set": updated_fields},
        )

        # Also update the in-memory user and form so changes are visible immediately
        for key, value in updated_fields.items():
            setattr(user, key, value)
        form = UserProfileForm(obj=user)

        flash("Profile updated successfully!", "success")

    return render_template("profile.html", title="My Profile", form=form, user=user, movie_count=movie_count)


# ==================== TMDB API ROUTES ====================

@pages.route("/search")
@login_required
def search():
    """Search movies using TMDB API"""
    query = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    
    results = None
    if query:
        results = tmdb.search_movies(query, page)
    
    return render_template(
        "search.html",
        title="Search Movies",
        query=query,
        results=results
    )


@pages.route("/tmdb/movie/<int:movie_id>")
@login_required
def tmdb_movie(movie_id: int):
    """View detailed TMDB movie information"""
    movie_info = tmdb.get_full_movie_info(movie_id)
    
    if not movie_info:
        flash("Movie not found", "danger")
        return redirect(url_for(".search"))
    
    # Get director
    director = tmdb.get_director(movie_id)
    
    return render_template(
        "tmdb_movie.html",
        title=movie_info["movie"].title,
        movie=movie_info["movie"],
        cast=movie_info["cast"],
        trailer=movie_info["trailer"],
        director=director
    )


@pages.route("/add_from_tmdb/<int:movie_id>", methods=["POST"])
@login_required
def add_from_tmdb(movie_id: int):
    """Add a movie from TMDB to user's watchlist"""
    movie_info = tmdb.get_full_movie_info(movie_id)
    
    if not movie_info:
        flash("Movie not found", "danger")
        return redirect(url_for(".search"))
    
    tmdb_movie_data = movie_info["movie"]
    director = tmdb.get_director(movie_id)
    
    # Get trailer link if available
    video_link = ""
    if movie_info["trailer"] and movie_info["trailer"].youtube_url:
        video_link = movie_info["trailer"].youtube_url
    
    # Get cast names
    cast_names = [member.name for member in movie_info["cast"]]
    
    # Create movie entry
    movie = Movie(
        _id=uuid.uuid4().hex,
        title=tmdb_movie_data.title,
        director=director,
        year=tmdb_movie_data.year,
        cast=cast_names,
        tags=tmdb_movie_data.genres,
        description=tmdb_movie_data.overview,
        video_link=video_link
    )
    
    # Save to MongoDB
    current_app.db.movie.insert_one(asdict(movie))
    current_app.db.user.update_one(
        {"_id": session["user_id"]}, {"$push": {"movies": movie._id}}
    )
    
    flash(f"'{movie.title}' added to your watchlist!", "success")
    return redirect(url_for(".movie", _id=movie._id))

@pages.route("/add_featured/<int:movie_id>")
@login_required
def add_featured(movie_id):
    """Add featured TMDB movie directly from homepage"""
    movie_info = tmdb.get_full_movie_info(movie_id)

    if not movie_info:
        flash("Could not load movie details.", "danger")
        return redirect(url_for(".home"))

    tmdb_movie_data = movie_info["movie"]
    director = tmdb.get_director(movie_id)

    # Trailer
    trailer = movie_info.get("trailer")
    trailer_url = trailer.youtube_url if trailer else ""

    # Cast
    cast_names = [actor.name for actor in movie_info["cast"]]

    movie = Movie(
        _id=uuid.uuid4().hex,
        title=tmdb_movie_data.title,
        director=director,
        year=tmdb_movie_data.year,
        cast=cast_names,
        tags=tmdb_movie_data.genres,
        description=tmdb_movie_data.overview,
        video_link=trailer_url,
    )

    current_app.db.movie.insert_one(asdict(movie))
    current_app.db.user.update_one(
        {"_id": session["user_id"]}, {"$push": {"movies": movie._id}}
    )

    flash(f"{movie.title} added to your watchlist!", "success")
    return redirect(url_for(".watchlist"))

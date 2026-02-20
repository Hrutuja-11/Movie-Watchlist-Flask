import os
from flask import Flask, session
from dotenv import load_dotenv
from pymongo import MongoClient

from movie_library.routes import pages

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config["MONGODB_URI"] = os.environ.get("MONGODB_URI")
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "pf9Wkove4IKEAXvy-cQkeDPhv9Cb3Ag-wyJILbq_dFw"
    )
    app.db = MongoClient(app.config["MONGODB_URI"]).get_default_database()

    @app.context_processor
    def inject_user_data():
        user_data = None
        watchlist_count = 0
        if session.get("email"):
            user_data = app.db.user.find_one({"email": session["email"]})
            if user_data:
                # Ensure all fields exist
                user_data.setdefault('name', '')
                user_data.setdefault('avatar_url', '')
                user_data.setdefault('bio', '')
                user_data.setdefault('movies', [])
                watchlist_count = len(user_data['movies']) if isinstance(user_data['movies'], list) else 0
        return dict(current_user=user_data, watchlist_count=watchlist_count)

    app.register_blueprint(pages)
    return app


app = create_app()
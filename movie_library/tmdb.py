"""
TMDB API Utility Module
Provides functions to interact with The Movie Database (TMDB) API
"""

import os
import requests
from dataclasses import dataclass, field
from typing import Optional, List

# TMDB API Base URL
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p"


def get_api_key() -> str:
    """Get TMDB API key from environment variables"""
    api_key = os.environ.get("TMDB_API_KEY")
    if not api_key:
        raise ValueError("TMDB_API_KEY not found in environment variables")
    return api_key


@dataclass
class TMDBMovie:
    """Dataclass representing a movie from TMDB"""
    id: int
    title: str
    overview: str = ""
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    release_date: str = ""
    vote_average: float = 0.0
    vote_count: int = 0
    genre_ids: List[int] = field(default_factory=list)
    genres: List[str] = field(default_factory=list)
    runtime: int = 0
    tagline: str = ""
    
    @property
    def poster_url(self) -> Optional[str]:
        """Get full poster URL"""
        if self.poster_path:
            return f"{TMDB_IMAGE_BASE_URL}/w500{self.poster_path}"
        return None
    
    @property
    def backdrop_url(self) -> Optional[str]:
        """Get full backdrop URL"""
        if self.backdrop_path:
            return f"{TMDB_IMAGE_BASE_URL}/original{self.backdrop_path}"
        return None
    
    @property
    def year(self) -> int:
        """Extract year from release date"""
        if self.release_date:
            try:
                return int(self.release_date.split("-")[0])
            except (ValueError, IndexError):
                return 0
        return 0


@dataclass
class TMDBCastMember:
    """Dataclass representing a cast member"""
    id: int
    name: str
    character: str = ""
    profile_path: Optional[str] = None
    
    @property
    def profile_url(self) -> Optional[str]:
        """Get full profile image URL"""
        if self.profile_path:
            return f"{TMDB_IMAGE_BASE_URL}/w185{self.profile_path}"
        return None


@dataclass
class TMDBVideo:
    """Dataclass representing a video (trailer, teaser, etc.)"""
    id: str
    key: str
    name: str
    site: str
    type: str
    
    @property
    def youtube_url(self) -> Optional[str]:
        """Get YouTube embed URL if video is from YouTube"""
        if self.site.lower() == "youtube":
            return f"https://www.youtube.com/embed/{self.key}"
        return None


def search_movies(query: str, page: int = 1) -> dict:
    """
    Search for movies by title
    
    Args:
        query: Search query string
        page: Page number for pagination
        
    Returns:
        Dictionary containing search results and metadata
    """
    api_key = get_api_key()
    url = f"{TMDB_BASE_URL}/search/movie"
    
    params = {
        "api_key": api_key,
        "query": query,
        "page": page,
        "include_adult": False,
        "language": "en-US"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        movies = []
        for item in data.get("results", []):
            movie = TMDBMovie(
                id=item.get("id"),
                title=item.get("title", ""),
                overview=item.get("overview", ""),
                poster_path=item.get("poster_path"),
                backdrop_path=item.get("backdrop_path"),
                release_date=item.get("release_date", ""),
                vote_average=item.get("vote_average", 0.0),
                vote_count=item.get("vote_count", 0),
                genre_ids=item.get("genre_ids", [])
            )
            movies.append(movie)
        
        return {
            "movies": movies,
            "page": data.get("page", 1),
            "total_pages": data.get("total_pages", 1),
            "total_results": data.get("total_results", 0)
        }
    except requests.RequestException as e:
        print(f"Error searching movies: {e}")
        return {"movies": [], "page": 1, "total_pages": 1, "total_results": 0}


def get_movie_details(movie_id: int) -> Optional[TMDBMovie]:
    """
    Get detailed information about a specific movie
    
    Args:
        movie_id: TMDB movie ID
        
    Returns:
        TMDBMovie object with full details or None if not found
    """
    api_key = get_api_key()
    url = f"{TMDB_BASE_URL}/movie/{movie_id}"
    
    params = {
        "api_key": api_key,
        "language": "en-US"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        genres = [genre.get("name", "") for genre in data.get("genres", [])]
        
        movie = TMDBMovie(
            id=data.get("id"),
            title=data.get("title", ""),
            overview=data.get("overview", ""),
            poster_path=data.get("poster_path"),
            backdrop_path=data.get("backdrop_path"),
            release_date=data.get("release_date", ""),
            vote_average=data.get("vote_average", 0.0),
            vote_count=data.get("vote_count", 0),
            genres=genres,
            runtime=data.get("runtime", 0),
            tagline=data.get("tagline", "")
        )
        
        return movie
    except requests.RequestException as e:
        print(f"Error getting movie details: {e}")
        return None


def get_movie_credits(movie_id: int) -> List[TMDBCastMember]:
    """
    Get cast information for a movie
    
    Args:
        movie_id: TMDB movie ID
        
    Returns:
        List of TMDBCastMember objects
    """
    api_key = get_api_key()
    url = f"{TMDB_BASE_URL}/movie/{movie_id}/credits"
    
    params = {
        "api_key": api_key,
        "language": "en-US"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        cast = []
        for item in data.get("cast", [])[:10]:  # Limit to top 10 cast members
            member = TMDBCastMember(
                id=item.get("id"),
                name=item.get("name", ""),
                character=item.get("character", ""),
                profile_path=item.get("profile_path")
            )
            cast.append(member)
        
        return cast
    except requests.RequestException as e:
        print(f"Error getting movie credits: {e}")
        return []


def get_movie_videos(movie_id: int) -> List[TMDBVideo]:
    """
    Get videos (trailers, teasers) for a movie
    
    Args:
        movie_id: TMDB movie ID
        
    Returns:
        List of TMDBVideo objects
    """
    api_key = get_api_key()
    url = f"{TMDB_BASE_URL}/movie/{movie_id}/videos"
    
    params = {
        "api_key": api_key,
        "language": "en-US"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        videos = []
        for item in data.get("results", []):
            video = TMDBVideo(
                id=item.get("id", ""),
                key=item.get("key", ""),
                name=item.get("name", ""),
                site=item.get("site", ""),
                type=item.get("type", "")
            )
            videos.append(video)
        
        # Sort to prioritize trailers
        videos.sort(key=lambda v: (v.type != "Trailer", v.type != "Teaser"))
        
        return videos
    except requests.RequestException as e:
        print(f"Error getting movie videos: {e}")
        return []


def get_full_movie_info(movie_id: int) -> dict:
    """
    Get complete movie information including details, cast, and videos
    
    Args:
        movie_id: TMDB movie ID
        
    Returns:
        Dictionary containing movie details, cast, and videos
    """
    movie = get_movie_details(movie_id)
    if not movie:
        return None
    
    cast = get_movie_credits(movie_id)
    videos = get_movie_videos(movie_id)
    
    # Get the first trailer if available
    trailer = None
    for video in videos:
        if video.youtube_url:
            trailer = video
            break
    
    return {
        "movie": movie,
        "cast": cast,
        "videos": videos,
        "trailer": trailer
    }


def get_director(movie_id: int) -> str:
    """
    Get the director's name for a movie
    
    Args:
        movie_id: TMDB movie ID
        
    Returns:
        Director's name or empty string if not found
    """
    api_key = get_api_key()
    url = f"{TMDB_BASE_URL}/movie/{movie_id}/credits"
    
    params = {
        "api_key": api_key,
        "language": "en-US"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        for crew_member in data.get("crew", []):
            if crew_member.get("job") == "Director":
                return crew_member.get("name", "")
        
        return ""
    except requests.RequestException as e:
        print(f"Error getting director: {e}")
        return ""


def get_featured_indian_movies(limit=12):
    api_key = get_api_key()
    url = f"{TMDB_BASE_URL}/discover/movie"

    params = {
        "api_key": api_key,
        "language": "en-US",
        "sort_by": "popularity.desc",
        "with_origin_country": "IN",  # 🇮🇳 Only Indian movies
        "page": 1
    }

    try:
        response = requests.get(url, params=params).json()
        movies = response.get("results", [])
        return movies[:limit]
    except Exception as e:
        print("Error fetching Indian movies:", e)
        return []

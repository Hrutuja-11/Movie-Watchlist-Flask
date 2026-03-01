# 🎬 Movie Watchlist (Flask)

A Flask-based web application that allows users to browse movies and save them to a personal watchlist.  
This project integrates with **The Movie Database (TMDB) API** for movie data and offers a user-friendly interface to manage your favorite films.

---

## 💡 Overview

This web app lets users:
- Browse movies from TMDB
- Search for movies
- Add movies to a personal watchlist
- View and manage the watchlist

The UI is built using **HTML/CSS/Jinja templates** and the backend is powered by **Flask (Python)**.

---

## 🧠 Features

✔ Movie search using TMDB API  
✔ Add movies to a watchlist  
✔ View your watchlist  
✔ Easy navigation and clean UI  
✔ Runs locally with Flask

---

## 🔧 Technologies Used

| Technology | Purpose |
|------------|---------|
| Python | Backend logic |
| Flask | Web framework |
| TMDB API | Movie data |
| HTML/CSS | Frontend UI |
| Jinja templates | Dynamic rendering |
| MongoDB | Database |

---

## 🚀 Getting Started

### 📌 1. Clone the Repository
```bash
git clone https://github.com/Hrutuja-11/Movie-Watchlist-Flask.git
cd Movie-Watchlist-Flask
```
📌 2. Create & Activate Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate      # Mac / Linux
venv\Scripts\activate         # Windows
```
📌 3. Install Dependencies
```bash
pip install -r requirements.txt
```
📌 4. Configure Environment Variables

Create a file named .env in the root:
```bash
TMDB_API_KEY=your_tmdb_api_key
```
Get your free key from: https://www.themoviedb.org/

📌 5. Run the App
```bash
flask run
```
## 🚀 Live Demo

[![Live Demo](https://img.shields.io/badge/Live-Demo-green?style=for-the-badge)](https://watchvault-90ai.onrender.com)
> ⚠️ Note: The app may take 30–60 seconds to load initially due to free hosting cold start.

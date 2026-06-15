---
last_mapped_date: 2026-06-15
---

# 📂 Structure

## Root Directory
- `backend/`: Contains all Python server code, database files, extraction scripts, and HTML templates.
- `android_tv_app/`: Contains the Android native Kotlin project for the smart TV app.

## Backend Structure (`backend/`)
- `main.py`: Entry point for the FastAPI server.
- `database.py`: SQLAlchemy models and connection setup.
- `extractor.py`: High-level logic orchestrating the scraping and extraction processes.
- `*.js` & `extract_deobfuscator.py`: Specialized scripts for bypassing video player obfuscation.
- `test_*.py`: Various test scripts used during development for scraping targets.
- `templates/`: Jinja2 or plain HTML templates used for testing web players or serving static pages.
- `sports_tv.db`: Local SQLite database.

## Android TV App Structure (`android_tv_app/app/src/main/`)
- `java/com/sportstv/app/`: Kotlin source files.
  - `MainActivity.kt` / `MainFragment.kt`: Leanback entry points for rendering the media catalog.
  - `PlaybackActivity.kt`: Specialized ExoPlayer implementation for handling streams, custom MIME types, and proxy headers.
- `res/`: Android resources (layouts, drawables, strings).
  - `layout/activity_playback.xml`: Custom player overlay containing the news ticker.
  - `layout/activity_main.xml`: Root layout for Leanback fragment.

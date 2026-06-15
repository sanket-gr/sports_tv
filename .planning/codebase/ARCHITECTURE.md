---
last_mapped_date: 2026-06-15
---

# 🏛️ Architecture

## System Overview
The system follows a typical Client-Server architecture designed specifically for Android TV media consumption.
- **Backend (Python)**: Acts as an aggregator and proxy. It scrapes third-party sports streaming sites, defeats anti-bot measures using Playwright and JS evaluation, extracts raw HLS streams, and serves them via REST APIs.
- **Frontend (Android TV)**: A native Android application optimized for large screens (D-Pad navigation) that consumes the backend API and plays the media.

## Key Patterns
- **Headless Extraction Pipeline**: The backend (`extractor.py`, `main.py`) uses a series of scripts (`deobfuscator.js`, `decrypt_player.js`) to reverse engineer embedded video players and return clean `.m3u8` or raw text manifest URLs.
- **Proxying & Header Forgery**: To bypass Referer and Origin restrictions on external HLS streams, the Android app often relies on the backend to act as a proxy or uses native OkHttp interceptors.
- **Leanback UI**: The frontend adheres strictly to Android TV Leanback design guidelines, utilizing `BrowseSupportFragment` for the home catalog and custom `Activity` structures for ExoPlayer playback.
- **Database Abstraction**: `database.py` manages a SQLite store for caching, categories, and stream metadata using SQLAlchemy ORM.

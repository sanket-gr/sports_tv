---
last_mapped_date: 2026-06-15
---

# 🥞 Technology Stack

## Backend
- **Language**: Python 3
- **Framework**: FastAPI (async web framework)
- **Server**: Uvicorn
- **Database ORM**: SQLAlchemy
- **Database**: SQLite (local development), PostgreSQL (production-ready, via psycopg2-binary)
- **Templating**: Jinja2
- **Scraping & Automation**: Playwright, BeautifulSoup4, Requests
- **File Handling**: aiofiles, python-multipart

## Android TV App
- **Language**: Kotlin
- **SDK**: Android SDK (Min 21, Target 34)
- **UI Framework**: AndroidX Leanback (for TV interfaces)
- **Media Player**: Jetpack Media3 (ExoPlayer with HLS support)
- **Networking**: Retrofit2 with Gson converter, OkHttp3 Logging Interceptor
- **Image Loading**: Glide
- **Concurrency**: Kotlin Coroutines (kotlinx-coroutines-android)

## Deployment / Operations
- **Hosting**: Render (indicated by `render.yaml`)
- **Build System (Android)**: Gradle
- **Version Control**: Git

# 📺 Sports TV — Project Definition

> Single source of truth. Update this before changing direction.

---

## What Is This?

**Sports TV** is a two-part system for watching live sports streams on Android TV:

- A **Python/FastAPI backend** that scrapes third-party sports streaming sites, defeats anti-bot measures, extracts raw HLS (`.m3u8`) streams, and serves them via a REST API.
- A **native Android TV app** (Kotlin + Leanback) that consumes the API, displays a curated channel catalog, and plays streams via ExoPlayer.

---

## Core Goals

1. Reliable live sports stream playback on Android TV (D-Pad first, large screen).
2. Fast stream resolution — minimize Playwright overhead and startup latency.
3. Resilient scraping — survive minor DOM changes and anti-bot updates without full rewrites.
4. Clean, maintainable codebase that a single developer can iterate on quickly.

---

## What It Is NOT

- Not a licensed streaming service.
- Not a multi-user SaaS product.
- Not a general-purpose scraper framework.

---

## Stack Summary

| Layer        | Technology                                      |
|--------------|-------------------------------------------------|
| Backend      | Python 3, FastAPI, Uvicorn, SQLAlchemy, SQLite/PostgreSQL |
| Scraping     | Playwright, BeautifulSoup4, Requests            |
| Bypass Tools | deobfuscator.js, decrypt_player.js, execjs      |
| Android App  | Kotlin, AndroidX Leanback, ExoPlayer (Media3)   |
| Networking   | Retrofit2, OkHttp3                              |
| Hosting      | Render (render.yaml)                            |
| Build        | Gradle, Git                                     |

---

## Key Constraints

- Android TV Leanback UI must be D-Pad navigable at all times.
- Older TV hardware: no heavy animations, no client-side JS processing.
- ExoPlayer requires correct MIME types (`application/x-mpegURL`) — manual override in place.
- Playwright is slow — every optimization to reduce or cache browser sessions matters.

---

## Active Maintainer(s)

- Solo developer (update if team grows)

---

_Last updated: 2026-06-15_

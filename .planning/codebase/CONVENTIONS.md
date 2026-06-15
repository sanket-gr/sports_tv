---
last_mapped_date: 2026-06-15
---

# 📏 Conventions

## Backend (Python)
- **Formatting**: Adheres to standard PEP 8, though extraction scripts lean towards functional/scripting styles due to rapid iteration against changing scraper targets.
- **Asynchronous Execution**: Uses FastAPI `async def` routing and `playwright.async_api` to ensure non-blocking concurrent requests.
- **Error Handling**: Extensive `try/except` blocks are used when scraping to gracefully handle DOM changes, timeouts, or anti-bot blocks, returning default values or graceful errors to the client.

## Frontend (Kotlin/Android)
- **UI Paradigms**: Strict adherence to Android TV Leanback components (`BrowseSupportFragment`, `ArrayObjectAdapter`, `Presenter`).
- **Media Playback**: `PlaybackActivity` encapsulates ExoPlayer lifecycle events natively, preferring programmatic player configuration over complex XML layouts for the player view.
- **Concurrency**: `lifecycleScope.launch(Dispatchers.IO)` is used for all network I/O to keep the UI thread clear.
- **Error Handling**: Retrofit network failures and ExoPlayer playback errors are caught and surfaced via Toasts or custom error screens to prevent silent failures on the TV.

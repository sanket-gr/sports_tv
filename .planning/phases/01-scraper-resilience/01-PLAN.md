# Phase 1: Scraper Resilience

This phase focuses on improving the reliability of the scraping backend by adding health checks, fallback logic, Playwright session pooling, and source toggling.

## User Review Required
> [!IMPORTANT]
> - **Playwright Async Migration**: Moving to Playwright session pooling implies we should keep a persistent browser running. The cleanest way in FastAPI is using `async_playwright` inside the application `lifespan` and passing the browser context to the scrapers. This requires refactoring the scrapers (`watchmmafull`, `jokertvguide`) to be `async def` and changing `_run_extraction` to `async`.
> - **Fallback Logic**: Should a single Stream have multiple URLs (primary + fallback)? I plan to add a `fallback_url` column to the `Stream` table to support this. If extraction fails on `source_url`, it will automatically try `fallback_url`.

## Open Questions
- Is adding a single `fallback_url` column to the `Stream` model sufficient, or would you prefer a fully separate `StreamSource` table to handle an arbitrary number of fallbacks? (I recommend a single `fallback_url` for simplicity to start).

## Proposed Changes

### Database Layer
#### [MODIFY] [database.py](file:///d:/projects/sports_tv/backend/database.py)
- **New Table `SourceConfig`**: Add a table to track global scraper source health and toggles (e.g., `id`, `name`, `domain`, `is_active`, `last_health_status`).
- **Update `Stream` Model**: Add `fallback_url = Column(String(500), nullable=True)`.

### Scrapers & Extraction
#### [MODIFY] [scrapers/__init__.py](file:///d:/projects/sports_tv/backend/scrapers/__init__.py)
- Update `extract` to accept a Playwright `Browser` instance.
- Update to be an `async def extract(...)` function to support async Playwright.
- Add fallback logic: if `source_url` extraction returns an error, recursively call `extract` with the `fallback_url`.

#### [MODIFY] [scrapers/watchmmafull.py](file:///d:/projects/sports_tv/backend/scrapers/watchmmafull.py) & [scrapers/jokertvguide.py](file:///d:/projects/sports_tv/backend/scrapers/jokertvguide.py)
- Convert `_fetch_with_browser` and `_fetch_hls` to use the provided async `Browser` context rather than launching a new browser synchronously every time.

### API & Application
#### [MODIFY] [main.py](file:///d:/projects/sports_tv/backend/main.py)
- **Lifespan Manager**: Start an `async_playwright` Chromium browser on app startup and close it on shutdown. Keep it in app state.
- **Background Extraction**: Update `_run_extraction` to be `async` and use the persistent browser.
- **New Endpoint `/api/health/sources`**: Create a periodic background task or on-demand endpoint that tests connectivity to `sportsurge.ws`, `watchmmafull.com`, etc., and updates the `SourceConfig` table.
- **Admin Endpoints**: 
  - Update `POST /admin/streams` to accept a `fallback_url`.
  - Add endpoints to toggle a source's `is_active` status.

### Frontend (Admin Dashboard)
#### [MODIFY] [templates/admin.html](file:///d:/projects/sports_tv/backend/templates/admin.html)
- Add a "Sources Configuration" panel showing current health status (Online/Offline) and an ON/OFF toggle switch for each source.
- Update the "Add Stream" modal to include an optional "Fallback URL" input field.

## Verification Plan

### Automated Tests
- Run `pytest backend/tests/ -v` to ensure API routes and extraction routing don't break.
- Add a test for the `/api/health/sources` endpoint.

### Manual Verification
- **Admin Dashboard**: Verify that sources can be toggled on/off, and their health status is displayed correctly.
- **Session Pooling**: Monitor the server logs when adding a stream; Playwright startup time should drop to ~0 since the browser is already running.
- **Fallback**: Add a stream with a deliberately broken primary URL and a valid fallback URL. Confirm that the stream extraction succeeds using the fallback.

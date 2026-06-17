# Phase 2: Stream Performance

This phase focuses on caching resolved HLS links and implementing a background refresh loop to ensure stream links stay fresh without making the user wait for extraction.

## User Review Required
> [!IMPORTANT]
> **Android Proxy Interceptor Task**: In the original Phase 2 roadmap, there was a task to "profile OkHttp interceptor overhead on Android side". Since we moved the HLS proxy logic entirely to the FastAPI backend (`/api/proxy`) in a previous phase, this Android-specific optimization is no longer applicable. I will mark it as skipped or implicitly resolved.

## Open Questions
- **Refresh Frequency**: I propose a 15-minute TTL (Time To Live) for streams before they are automatically refreshed by the background job. Does 15 minutes sound reasonable, or would you prefer a shorter/longer interval?

## Proposed Changes

### Database Updates
#### [MODIFY] [database.py](file:///d:/projects/sports_tv/backend/database.py)
- **Update `Stream` Model**: Add `hls_updated_at = Column(DateTime, nullable=True)`. This will track when the `.m3u8` URL was last successfully extracted.

### Background Job & Caching
#### [MODIFY] [main.py](file:///d:/projects/sports_tv/backend/main.py)
- **Stream Refresh Loop**: Create a `stream_refresh_worker(app)` function that runs infinitely via `asyncio.create_task` during the application `lifespan`.
- The worker will wake up every 1 minute, find all streams where `is_live == True` and `hls_updated_at` is older than 15 minutes, and dispatch them to `_run_extraction`.
- **Extraction Updates**: Update `_run_extraction` to set `hls_updated_at = datetime.utcnow()` upon successful HLS extraction.

### Playwright / httpx Optimizations
- **Review**: The `sportsurge` and `vidplayer` scrapers were successfully converted to `httpx` and pure async processes in Phase 1. The `watchmmafull` and `jokertvguide` scrapers now use the persistent Playwright context pool, meaning startup latency is virtually zero. The remaining tasks here are fulfilled.

## Verification Plan

### Automated Tests
- Update SQLite mock databases in backend tests to support the new `hls_updated_at` column.
- Run `pytest backend/tests/ -v`.

### Manual Verification
- Add a new stream via the admin panel. Observe its `hls_updated_at` timestamp in the database.
- Temporarily modify the background refresh loop to run every 1 minute instead of 15, and verify the backend automatically triggers re-extraction without user intervention.
- Ensure the Android TV app correctly fetches the pre-resolved URLs instantly.

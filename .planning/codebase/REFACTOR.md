# 🔧 Refactor Backlog

> Prioritized list of code quality improvements. Pick from the top down.
> Each item should be a focused PR — one concern at a time.

---

## Priority 1 — Critical (Do First)

### 1.1 Modularize Scrapers
**Problem**: All scraping logic lives in `extractor.py` and loose scripts. One source change risks breaking everything.
**Fix**: Create `backend/scrapers/` directory. Each source gets its own module:
```
backend/scrapers/
  __init__.py
  base.py          # Abstract base class with .extract() interface
  watchmmafull.py
  vidplayer.py
  # add new sources here
```
**Effort**: Medium | **Impact**: High

---

### 1.2 Organize Test Scripts into pytest
**Problem**: `test_mma.py`, `test_requests_mma.py`, `test_decrypt.py` are ad-hoc scripts with `print()` and no assertions framework.
**Fix**:
```
backend/tests/
  __init__.py
  test_scrapers.py     # parametrized per source
  test_extractor.py
  test_api.py          # FastAPI TestClient
```
Run with: `pytest backend/tests/ -v`
**Effort**: Small | **Impact**: High (prevents regressions)

---

### 1.3 Add Structured Logging
**Problem**: Debugging relies on `print()` statements scattered across `extractor.py`, scrapers, and bypass scripts.
**Fix**: Replace with Python `logging` module. One config in `main.py`:
```python
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)
```
**Effort**: Small | **Impact**: Medium

---

## Priority 2 — Important (Do in Phase 1)

### 2.1 Playwright Session Pooling
**Problem**: A new Playwright browser instance is spun up per request — extremely slow.
**Fix**: Maintain a persistent browser context pool in `extractor.py`. Reuse contexts across requests with a semaphore for concurrency control.
**Effort**: Medium | **Impact**: High (stream load time improvement)

---

### 2.2 Stream URL Caching
**Problem**: Every stream request triggers a full Playwright extraction cycle even if the URL was resolved 2 minutes ago.
**Fix**: Cache resolved `.m3u8` URLs in SQLite with a TTL (e.g., 10–30 min). Check cache before running extraction.
```python
# pseudo-code
cached = db.get_stream_url(channel_id)
if cached and not expired(cached): return cached
url = await extract(channel_id)
db.save_stream_url(channel_id, url, ttl=1800)
```
**Effort**: Small | **Impact**: Very High

---

### 2.3 MIME Type Handling — Centralize Override Logic
**Problem**: MIME type override for `.txt`-extension HLS streams is hardcoded in `PlaybackActivity.kt`. Brittle.
**Fix**: The backend should normalize stream metadata and include a `mime_type` field in the API response. The Android app reads it from the response rather than guessing.
**Effort**: Small | **Impact**: Medium

---

## Priority 3 — Nice to Have (Phase 2+)

### 3.1 Replace `execjs` with Playwright for All JS Evaluation
**Problem**: Two different JS execution paths (`execjs` and Playwright) create maintenance overhead.
**Fix**: Standardize on Playwright for all JS evaluation. Remove `execjs` dependency.
**Effort**: Medium | **Impact**: Low-Medium

---

### 3.2 Android — Replace Toast Errors with Custom Error Screen
**Problem**: Network and playback errors surface as Toasts — easily missed on a TV.
**Fix**: Create a dedicated `ErrorFragment` or overlay that pauses playback and shows a clear message with a retry button.
**Effort**: Small | **Impact**: Medium (UX)

---

### 3.3 Remove Dead Test Files from Backend Root
**Problem**: `test_*.py` files clutter the `backend/` root alongside production code.
**Fix**: After migrating to `backend/tests/` (item 1.2), delete root-level test scripts.
**Effort**: Trivial | **Impact**: Low (cleanliness)

---

_Last updated: 2026-06-15_

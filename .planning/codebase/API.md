# 🔌 API Reference

> All backend REST endpoints consumed by the Android TV app.
> Fill in actual routes from `main.py` — placeholders marked with `[TODO]`.

---

## Base URL

| Environment | URL                              |
|-------------|----------------------------------|
| Local       | `http://localhost:8000`          |
| Production  | `https://<your-render-app>.onrender.com` |

---

## Endpoints

### GET `/streams` — Get Stream Catalog
Returns the full list of available channels/streams.

**Response:**
```json
[
  {
    "id": "mma-1",
    "name": "MMA Stream 1",
    "category": "MMA",
    "thumbnail_url": "https://...",
    "source": "watchmmafull"
  }
]
```

---

### GET `/stream/{id}` — Resolve Stream URL
Triggers extraction for a specific stream and returns the playable `.m3u8` URL.

**Parameters:**
| Param | Type   | Description       |
|-------|--------|-------------------|
| `id`  | string | Stream identifier |

**Response:**
```json
{
  "id": "mma-1",
  "url": "https://cdn.example.com/stream.m3u8",
  "mime_type": "application/x-mpegURL",
  "headers": {
    "Referer": "https://watchmmafull.com"
  }
}
```

**Notes:**
- This is the slow endpoint — triggers Playwright if not cached.
- Android app should show a loading state while waiting.

---

### GET `/health` — Health Check `[TODO: confirm exists]`
Basic liveness check for Render deployment.

**Response:**
```json
{ "status": "ok" }
```

---

### GET `/health/sources` — Source Health `[PLANNED — Phase 1]`
Returns per-source scraper status.

**Response:**
```json
{
  "watchmmafull": "healthy",
  "vidplayer": "degraded"
}
```

---

## Authentication

- Currently: **None** (open API, private deployment assumed)
- Future: Consider adding a simple API key header for production.

---

## Error Responses

| Status | Meaning                              |
|--------|--------------------------------------|
| 200    | Success                              |
| 404    | Stream not found                     |
| 500    | Extraction failed (scraper broke)    |
| 503    | Playwright unavailable / timed out   |

---

_Last updated: 2026-06-15 — [TODO: fill in actual routes from main.py]_

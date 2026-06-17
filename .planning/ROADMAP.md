# 🗺️ Roadmap

> Phases are sequential. Do not start a phase until the previous one is marked ✅ Done.
> Each phase gets its own `PLAN.md` before any code is written.

---

## Current Status: Phase 5 — Mobile Project Scaffolding & Basic UI Layout

---

## Phase 0: Stabilize & Organize `[DONE]`
> Goal: Get the house in order before adding anything new.

- [x] Create `PROJECT.md`, `ROADMAP.md`, `GIT-WORKFLOW.md`
- [x] Restructure backend folder (see `FOLDER-STRUCTURE.md`)
- [x] Migrate ad-hoc test scripts to `pytest` structure
- [x] Resolve top 3 items in `REFACTOR.md`
- [x] Set up Git branching strategy (see `GIT-WORKFLOW.md`)
- [x] Document all existing API endpoints in `API.md`

---

## Phase 1: Scraper Resilience `[DONE]`
> Goal: Stop scraper breakage from killing the whole app.

- [x] Abstract each scraping target into its own `scrapers/source_name.py` module
- [x] Add per-source health checks (`/health/sources` endpoint)
- [x] Implement source fallback logic (if source A fails, try source B)
- [x] Add Playwright session pooling to reduce startup latency
- [x] Create a lightweight admin dashboard (HTML/Jinja2) to toggle sources on/off

---

## Phase 2: Stream Performance `[DONE]`
> Goal: Faster stream start times, better reliability.

- [x] Cache resolved `.m3u8` URLs with TTL (avoid re-running Playwright on every request)
- [x] Add background refresh job (pre-resolve streams before user requests)
- [x] Evaluate replacing Playwright with targeted `curl-cffi` or `httpx` for simpler sources
- [x] Proxy optimization: profile OkHttp interceptor overhead on Android side

---

## Phase 3: Android TV UX Polish `[DONE]`
> Goal: Polished, stable TV experience.

- [x] Custom error screen for failed streams (not just a Toast)
- [x] Loading/buffering overlay with channel name
- [x] EPG (Electronic Program Guide) — basic schedule per channel
- [x] Favorites row on home screen
- [x] Deep link support (`sportstv://watch/<channel_id>`)

---

## Phase 4: Ops & Deployment `[DONE]`
> Goal: Production-grade reliability.

- [x] Migrate from SQLite to PostgreSQL fully
- [x] Add structured logging (replace print debugging)
- [x] Set up Render health check alerts
- [x] CI/CD pipeline: lint + test on push via GitHub Actions
- [x] Automated scraper health monitoring (daily cron, alert on failure)

---

## Milestone v2.0: Android Mobile App

### Phase 5: Mobile Project Scaffolding & Basic UI Layout
**Goal:** Bootstrap the Android mobile project and implement the main touch-navigation screens in portrait mode.
**Requirements:** TEST-01, UI-01, UI-02, UI-03
**Depends on:** Phase 4
**Plans:** 1/1 plans complete

Plans:
- [x] TBD (run /gsd-plan-phase 5 to break down) (completed 2026-06-17)

### Phase 6: Retrofit API Client Integration
**Goal:** Wire Retrofit client calls to fetch live categories and streams from the FastAPI backend.
**Requirements:** NET-01, NET-02
**Depends on:** Phase 5
**Plans:** 1/1 plans complete

Plans:
- [x] TBD (run /gsd-plan-phase 6 to break down) (completed 2026-06-17)

### Phase 7: Mobile ExoPlayer Playback Integration
**Goal:** Implement Media3 ExoPlayer for HLS stream playback with overlay touch controls.
**Requirements:** PLAY-01, PLAY-02, PLAY-03
**Depends on:** Phase 6
**Plans:** 1/1 plans complete

Plans:
- [x] TBD (run /gsd-plan-phase 7 to break down) (completed 2026-06-17)

### Phase 8: Local Favorites Persistence & Testing
**Goal:** Implement persistent favorite channel lists locally on mobile and perform end-to-end testing.
**Requirements:** FAV-01, FAV-02, FAV-03, TEST-02
**Depends on:** Phase 7
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd-plan-phase 8 to break down)

---

## Icebox (Future Ideas, Not Committed)

- Multi-language stream support
- Android TV search functionality
- Stream quality selector (auto/1080p/720p)

---

_Last updated: 2026-06-17_

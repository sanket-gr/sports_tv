# 🗺️ Roadmap

> Phases are sequential. Do not start a phase until the previous one is marked ✅ Done.
> Each phase gets its own `PLAN.md` before any code is written.

---

## Current Status: Phase 1 — Scraper Resilience

---

## Phase 0 — Stabilize & Organize `[DONE]`
> Goal: Get the house in order before adding anything new.

- [x] Create `PROJECT.md`, `ROADMAP.md`, `GIT-WORKFLOW.md`
- [x] Restructure backend folder (see `FOLDER-STRUCTURE.md`)
- [x] Migrate ad-hoc test scripts to `pytest` structure
- [x] Resolve top 3 items in `REFACTOR.md`
- [x] Set up Git branching strategy (see `GIT-WORKFLOW.md`)
- [x] Document all existing API endpoints in `API.md`

---

## Phase 1 — Scraper Resilience `[DONE]`
> Goal: Stop scraper breakage from killing the whole app.

- [ ] Abstract each scraping target into its own `scrapers/source_name.py` module
- [ ] Add per-source health checks (`/health/sources` endpoint)
- [ ] Implement source fallback logic (if source A fails, try source B)
- [ ] Add Playwright session pooling to reduce startup latency
- [ ] Create a lightweight admin dashboard (HTML/Jinja2) to toggle sources on/off

---

## Phase 2 — Stream Performance `[DONE]`
> Goal: Faster stream start times, better reliability.

- [ ] Cache resolved `.m3u8` URLs with TTL (avoid re-running Playwright on every request)
- [ ] Add background refresh job (pre-resolve streams before user requests)
- [ ] Evaluate replacing Playwright with targeted `curl-cffi` or `httpx` for simpler sources
- [ ] Proxy optimization: profile OkHttp interceptor overhead on Android side

---

## Phase 3 — Android TV UX Polish `[DONE]`
> Goal: Polished, stable TV experience.

- [ ] Custom error screen for failed streams (not just a Toast)
- [ ] Loading/buffering overlay with channel name
- [ ] EPG (Electronic Program Guide) — basic schedule per channel
- [ ] Favorites row on home screen
- [ ] Deep link support (`sportstv://watch/<channel_id>`)

---

## Phase 4 — Ops & Deployment `[DONE]`
> Goal: Production-grade reliability.

- [ ] Migrate from SQLite to PostgreSQL fully
- [ ] Add structured logging (replace print debugging)
- [ ] Set up Render health check alerts
- [ ] CI/CD pipeline: lint + test on push via GitHub Actions
- [ ] Automated scraper health monitoring (daily cron, alert on failure)

---

## Icebox (Future Ideas, Not Committed)

- Multi-language stream support
- Android TV search functionality
- Mobile companion app (phone remote / schedule viewer)
- Stream quality selector (auto/1080p/720p)

---

_Last updated: 2026-06-15_

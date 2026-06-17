# 📺 Sports TV — Project Definition

> Single source of truth. Update this before changing direction.

---

## What This Is

**Sports TV** is a two-part system for watching live sports streams on Android TV:

- A **Python/FastAPI backend** that scrapes third-party sports streaming sites, defeats anti-bot measures, extracts raw HLS (`.m3u8`) streams, and serves them via a REST API.
- A **native Android TV app** (Kotlin + Leanback) that consumes the API, displays a curated channel catalog, and plays streams via ExoPlayer.

---

## Core Value

Reliable live sports stream playback on Android TV.

---

## Requirements

### Validated

- [x] Reliable live sports stream playback on Android TV
- [x] Python/FastAPI scraping backend with Playwright async pooling
- [x] Cached stream URL resolution with TTL and background worker refresh
- [x] Leanback Android TV application with ExoPlayer integration
- [x] SQLite database storage and Render deployment config

### Active

- [ ] Native Android mobile phone UI layout (adapted for touch/portrait navigation)
- [ ] Retrofit client integration with the FastAPI backend (reusing ApiClient)
- [ ] ExoPlayer playback with mobile touch controls (play/pause, volume, full screen)
- [ ] Mobile favorites screen/list with local persistence
- [ ] Deep link support for mobile streams
- [ ] Gradle build and emulator run verified in Android Studio

### Out of Scope

- [ ] Multi-language stream support
- [ ] Stream quality selector

---

## Context

**Sports TV** is built to run on older TV hardware, so client-side overhead must be kept to a minimum. Scraping is slow, making backend caching and browser session optimization critical.

---

## Constraints

- **Leanback UI**: Must be D-Pad navigable at all times.
- **Hardware**: Older TV hardware means no heavy animation or JS processing.
- **ExoPlayer MIME types**: Must manually override stream MIME types to `application/x-mpegURL`.
- **Scraper performance**: Playwright startup overhead requires background pooling.

---

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Playwright async lifespan | Shared browser instance in FastAPI reduces startup times | ✓ Good |
| MIME override for ExoPlayer | ExoPlayer fails to play raw HLS without `application/x-mpegURL` | ✓ Good |

---

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
_Last updated: 2026-06-17_

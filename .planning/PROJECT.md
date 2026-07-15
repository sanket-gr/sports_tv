# 📺 Sports TV — Project Definition

> Single source of truth. Update this before changing direction.

---

## What This Is

**Sports TV** is a two-part system for watching live sports streams on Android devices (TV and Mobile):

- A **Python/FastAPI backend** that scrapes third-party sports streaming sites, defeats anti-bot measures, extracts raw HLS (`.m3u8`) streams, and serves them via a REST API.
- A **native Android app** (Kotlin + Leanback for TV, Material UI for Mobile) that consumes the API, displays a curated channel catalog, and plays streams via ExoPlayer.

---

## Core Value

Reliable live sports stream playback on Android TV and Android Mobile phones.

---

## Current Milestone: v3.0 UX Polish & Deep Linking

**Goal:** Polish player UX, support deep linking, and consolidate shared client-side logic.

**Target features:**
- **Deep Linking:** Launch mobile/TV stream views directly from standard URLs.
- **Stream Quality Selector:** Auto/1080p/720p/480p manual selection in the player overlay.
- **Code Consolidation:** Unify shared player setup, network configuration, and utility logic.

---

## Requirements

### Validated

- ✓ Reliable live sports stream playback on Android TV — v1.0
- ✓ Python/FastAPI scraping backend with Playwright async pooling — v1.0
- ✓ Cached stream URL resolution with TTL and background worker refresh — v1.0
- ✓ Leanback Android TV application with ExoPlayer integration — v1.0
- ✓ SQLite database storage and Render deployment config — v1.0
- ✓ Native Android mobile phone UI layout (adapted for touch/portrait navigation) — v2.0
- ✓ Retrofit client integration with the FastAPI backend (reusing ApiClient) — v2.0
- ✓ ExoPlayer playback with mobile touch controls (play/pause, volume, full screen) — v2.0
- ✓ Mobile favorites screen/list with local persistence — v2.0
- ✓ Gradle build and emulator run verified in Android Studio — v2.0
- ✓ Closed MainActivity-StreamDetailBottomSheet integration gap — v2.0
- ✓ Low-latency live stream optimizations (bigger buffers, auto-retry, proxy segment cache) — v2.0

### Active

- [ ] Deep link support for mobile streams

### Out of Scope

- [ ] Multi-language stream support
- [ ] Stream quality selector

---

## Context

Shipped v2.0 Android Mobile App milestone with 5 completed phases and post-audit streaming stability optimizations.
**Sports TV** is built to run on older TV hardware and standard Android phones, so client-side overhead must be kept to a minimum. Scraping is slow, making backend caching and browser session optimization critical.

---

## Constraints

- **Leanback UI**: Must be D-Pad navigable at all times on TV.
- **Hardware**: Older TV hardware means no heavy animation or JS processing.
- **ExoPlayer MIME types**: Must manually override stream MIME types to `application/x-mpegURL`.
- **Scraper performance**: Playwright startup overhead requires background pooling.

---

## Key Decisions

- Decision: Shared browser instance in FastAPI | Rationale: Reduces startup times | Outcome: ✓ Good
- Decision: Override stream MIME types | Rationale: ExoPlayer fails to play raw HLS without `application/x-mpegURL` | Outcome: ✓ Good
- Decision: DynamicHeaderDataSourceFactory | Rationale: Needed for dynamic header injection for domain-restricted HLS on mobile | Outcome: ✓ Good
- Decision: Material Components NoActionBar | Rationale: Immersive mobile app experience without standard toolbars | Outcome: ✓ Good

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
_Last updated: 2026-07-15 after v2.0 milestone completion_

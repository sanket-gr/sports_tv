# 🗺️ Roadmap

> Phases are sequential. Do not start a phase until the previous one is marked ✅ Done.
> Each phase gets its own `PLAN.md` before any code is written.

---

## Milestones

- ✅ **v1.0 MVP** — Phases 0-4 (shipped YYYY-MM-DD)
- ✅ **v2.0 Android Mobile App** — Phases 5-8.1 (shipped 2026-07-15)
- 🚧 **v3.0 UX Polish & Deep Linking** — Phases 9-11 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 0-4) — SHIPPED PREVIOUSLY</summary>

- [x] Phase 0: Stabilize & Organize
- [x] Phase 1: Scraper Resilience
- [x] Phase 2: Stream Performance
- [x] Phase 3: Android TV UX Polish
- [x] Phase 4: Ops & Deployment

</details>

<details>
<summary>✅ v2.0 Android Mobile App (Phases 5-8.1) — SHIPPED 2026-07-15</summary>

- [x] Phase 5: Mobile Scaffolding & Layout (1/1 plans) — completed 2026-06-17
- [x] Phase 6: Retrofit API Client Integration (1/1 plans) — completed 2026-06-17
- [x] Phase 7: Mobile ExoPlayer Playback (1/1 plans) — completed 2026-06-17
- [x] Phase 8: Local Favorites Persistence (1/1 plans) — completed 2026-06-17
- [x] Phase 08.1: Close MainActivity-StreamDetailBottomSheet gap (1/1 plans) — completed 2026-07-15

</details>

### 🚧 v3.0 UX Polish & Deep Linking (In Progress)

### Phase 9: Deep Link Integration
**Goal**: Implement D-Link URL scheme launching for Mobile & TV PlaybackActivity.
**Depends on**: Phase 8.1
**Plans**: 1 plan

Plans:
- [ ] 09-01: Intent Filter configuration and Deep Link routing

### Phase 10: Stream Quality Selector Menu
**Goal**: Parse and switch dynamic stream bitrates/resolutions manually via player control overlays.
**Depends on**: Phase 9
**Plans**: 1 plan

Plans:
- [ ] 10-01: Dynamic track parsing and Quality UI selection

### Phase 11: Common Code Consolidation
**Goal**: Refactor shared utility helpers, factories, and OkHttp builders to unified packages.
**Depends on**: Phase 10
**Plans**: 1 plan

Plans:
- [ ] 11-01: Codebase refactoring and common package scaffolding

---

## Icebox (Future Ideas, Not Committed)

- Multi-language stream support
- Android TV search functionality
- Chromecast/Google Cast integration

---

_Last updated: 2026-07-15_

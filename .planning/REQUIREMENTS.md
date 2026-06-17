# Requirements: Sports TV Mobile App

**Defined:** 2026-06-17
**Core Value:** Reliable live sports stream playback on Android devices (TV and Mobile)

## v1 Requirements

Requirements for the initial Android Mobile App release.

### Layout & UI

- [x] **UI-01**: Mobile-friendly portrait-first layout (no Leanback TV components)
- [x] **UI-02**: Bottom navigation bar or tabbed view for browsing channel categories by touch
- [x] **UI-03**: Detail sheet/screen with channel info, favorites toggle, and playback trigger

### Network & API

- [x] **NET-01**: Retrieve categories list from backend via Retrofit client (reusing `ApiClient`)
- [x] **NET-02**: Retrieve stream URLs and headers (Referer/User-Agent) from backend

### Playback

- [x] **PLAY-01**: Integrate Media3 ExoPlayer for HLS stream playback
- [x] **PLAY-02**: Touch controls overlay (Play/Pause, volume, screen ratio toggle)
- [x] **PLAY-03**: Handle player backgrounding, rotation, and lifecycle

### Favorites

- [x] **FAV-01**: Toggle channel favorite status
- [x] **FAV-02**: Display favorites list/row on the main screen
- [x] **FAV-03**: Persist favorites locally on the phone (e.g., SharedPreferences)

### Testing & Integration

- [x] **TEST-01**: Set up standard Android mobile Gradle project in Android Studio
- [x] **TEST-02**: Verify building and testing on Android phone emulators

## v2 Requirements

Deferred to future releases.

### Quality & Performance

- **QUAL-01**: Stream quality selector (Auto / 1080p / 720p / 480p)
- **QUAL-02**: Cast stream support (Chromecast / Google Cast integration)
- **QUAL-03**: Offline scheduling (set calendar notifications for upcoming matches)

## Out of Scope

Explicitly excluded to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Multi-language streams | High scraping complexity, defer for future scope |
| Real-time chat | Outside core value of simple media playback |
| User accounts / Cloud sync | Local storage is sufficient; keep system serverless/anonymous |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| UI-01 | Phase 5 | Complete |
| UI-02 | Phase 5 | Complete |
| UI-03 | Phase 5 | Complete |
| NET-01 | Phase 6 | Complete |
| NET-02 | Phase 6 | Complete |
| PLAY-01 | Phase 7 | Complete |
| PLAY-02 | Phase 7 | Complete |
| PLAY-03 | Phase 7 | Complete |
| FAV-01 | Phase 8 | Complete |
| FAV-02 | Phase 8 | Complete |
| FAV-03 | Phase 8 | Complete |
| TEST-01 | Phase 5 | Complete |
| TEST-02 | Phase 8 | Complete |

**Coverage:**
- v1 requirements: 13 total
- Mapped to phases: 13
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-17*
*Last updated: 2026-06-17 after initial definition*

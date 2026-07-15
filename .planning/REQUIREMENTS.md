# Requirements: Sports TV UX Polish, Quality Selector & Deep Linking

**Defined:** 2026-07-15
**Core Value:** Seamless UX with quick link launching, high-quality stream selection, and clean shared codebase.

## v1 Requirements

Requirements for the v3.0 release.

### Deep Linking

- [ ] **DL-01**: Support intent-filter URL schemes (e.g. `sportstv://play?stream_id={id}` or HTTPS App Links) on mobile and TV apps.
- [ ] **DL-02**: Automatically resolve and launch stream player directly when opening a deep link.

### Quality Selector

- [ ] **QS-01**: Extract available video track bitrates/resolutions from master HLS playlists dynamically.
- [ ] **QS-02**: Add a Stream Quality Selector button/menu to player controls on mobile and TV apps.
- [ ] **QS-03**: Support dynamic track selection switches using ExoPlayer track selection parameters.

### Code Consolidation & Tech Debt

- [ ] **REF-01**: Consolidate duplicate player source builders, cleanReferer helpers, and datasource factories into a common shared package.
- [ ] **REF-02**: Standardize ExoPlayer configuration, buffers, and timeouts across mobile and TV.

## Future Requirements

Deferred to future releases.

- **DL-03**: Support web-to-app routing from browser searches.
- **QS-04**: Save preferred stream quality option locally (e.g., SharedPreferences).

## Out of Scope

- Cloud-based sync of player settings.
- Custom custom-renderer support for unsupported codecs.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DL-01 | Phase 9 | Pending |
| DL-02 | Phase 9 | Pending |
| QS-01 | Phase 10 | Pending |
| QS-02 | Phase 10 | Pending |
| QS-03 | Phase 10 | Pending |
| REF-01 | Phase 11 | Pending |
| REF-02 | Phase 11 | Pending |

**Coverage:**
- v1 requirements: 7 total
- Mapped to phases: 7
- Unmapped: 0 ✓

---
*Requirements defined: 2026-07-15*

# Phase 3: Android TV UX Polish

This phase focuses on taking the Android TV app from a basic stream viewer to a polished, stable, and user-friendly product. We will enhance the UI, add convenience features like Favorites, and implement deep linking.

## User Review Required
> [!IMPORTANT]
> **EPG / Schedule Limitations**: Since our backend relies on scraping active streams (which usually don't post URLs until minutes before kickoff), we don't have a true Electronic Program Guide schedule database. I plan to build a simplified "Upcoming/Offline Streams" row on the home screen to act as the schedule for streams that have been added by the admin but aren't live yet. Please confirm if this approach is acceptable.

## Open Questions
- **Favorites Toggle Mechanism**: On Android TV, we don't have touch controls. I plan to use a **Long-Press (Hold 'OK' button)** on a stream card to add/remove it from Favorites. Is this intuitive, or would you prefer a separate "Details Screen" with a Favorite button before playback starts? (Long-press is much faster to implement and use).

## Proposed Changes

### 1. Custom Error Screen & Buffering Overlay
#### [MODIFY] `activity_playback.xml` & `PlaybackActivity.kt`
- Replace the basic emoji error screen with a stylized overlay using proper icons and typography.
- Implement an **auto-retry countdown** (e.g., "Retrying in 5...").
- Add the **Match/Channel Title** above the loading spinner so users know exactly what is buffering.

### 2. Favorites Row
#### [MODIFY] `MainFragment.kt` & `CardPresenter.kt`
- Implement local `SharedPreferences` to store a set of favorited `stream_id`s.
- Create an `OnItemViewLongClickedListener` on the leanback grid to toggle a stream's favorite status.
- Dynamically build a "⭐ Favorites" row at the very top of the Home Screen containing the saved streams.
- Add a visual indicator (like a heart or star emoji) to the `CardPresenter` if the item is favorited.

### 3. Basic EPG (Upcoming Streams)
#### [MODIFY] `MainFragment.kt`
- Fetch streams with `live_only=False` from the backend.
- Filter out streams without an active `hls_url` and place them in a dedicated "📅 Upcoming / Offline" row at the bottom of the home screen to serve as a basic program guide.

### 4. Deep Link Support
#### [MODIFY] `AndroidManifest.xml` & `MainActivity.kt`
- Add an `<intent-filter>` for the scheme `sportstv://` and host `watch`.
- Update `MainActivity` to intercept `sportstv://watch/<stream_id>`.
- If a deep link is detected, the app will make a quick API call to fetch the stream details and immediately launch `PlaybackActivity`.

## Verification Plan

### Automated Tests
- Run Android unit tests (if any exist for the presenters).
- Build the APK successfully via Gradle to ensure no compilation errors.

### Manual Verification
- **Favorites**: Long-press a stream card, verify it appears in the top Favorites row, and verify it persists after restarting the app.
- **Deep Linking**: Use `adb shell am start -W -a android.intent.action.VIEW -d "sportstv://watch/1" com.sportstv.app` to verify the app opens directly into playback.
- **Error Screen**: Hardcode a broken URL, wait for the error, and verify the auto-retry countdown functions correctly.

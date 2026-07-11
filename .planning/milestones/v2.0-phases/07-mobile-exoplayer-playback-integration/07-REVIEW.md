# Code Review: Phase 07 (Mobile & TV Playback Integration)

This document provides a technical code review of the changes introduced for ExoPlayer playback controls, server selection dialogs, and low-latency live streaming configuration.

---

## Summary of Review Findings

| Severity | Count | Description |
|---|---|---|
| 🔴 **Critical** | 0 | No critical or blocker bugs found. |
| 🟡 **Warning** | 2 | Potential network stability and compiler warnings. |
| 🔵 **Info** | 2 | Code style, structure suggestions, and optimizations. |

---

## Detailed Findings

### 🟡 Warning

#### 1. Unused Variable in TV PlaybackActivity
- **Location**: [app/PlaybackActivity.kt:L144](file:///d:/projects/sports_tv/android_tv_app/app/src/main/java/com/sportstv/app/PlaybackActivity.kt#L144)
- **Code**:
  ```kotlin
  val isIpUrl   = hlsUrl.matches(Regex("""https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/.*"""))
  ```
- **Description**: The variable `isIpUrl` is defined during the initialization flow but is never used anywhere in the class. The compiler raises a warning: `w: ... PlaybackActivity.kt:144:13 Variable 'isIpUrl' is never used`.
- **Recommendation**: Remove the unused `isIpUrl` variable declaration to keep the build clean and free of compiler warnings.

#### 2. Aggressive Low-Latency Buffer Settings under Poor Network Conditions
- **Location**:
  - [mobile/PlaybackActivity.kt:L305-312](file:///d:/projects/sports_tv/android_tv_app/mobile/src/main/java/com/sportstv/mobile/PlaybackActivity.kt#L305-L312)
  - [app/PlaybackActivity.kt:L230-237](file:///d:/projects/sports_tv/android_tv_app/app/src/main/java/com/sportstv/app/PlaybackActivity.kt#L230-L237)
- **Code**:
  ```kotlin
  val loadControl = DefaultLoadControl.Builder()
      .setBufferDurationsMs(
          2_000,   // minBufferMs
          8_000,   // maxBufferMs
          1_000,   // bufferForPlaybackMs
          1_000    // bufferForPlaybackAfterRebufferMs
      )
  ```
- **Description**: While a `minBufferMs` of 2 seconds and `bufferForPlaybackMs` of 1 second are perfect for high-speed fiber networks, users on spotty mobile data or slow Wi-Fi might experience rapid/frequent rebuffering cycles because a 2-second buffer leaves very little headroom for packet loss or network jitter.
- **Recommendation**: Monitor real-world user feedback. If users complain about frequent stuttering, consider bumping the values slightly (e.g., `minBufferMs = 4_000` / `maxBufferMs = 12_000` / `bufferForPlaybackMs = 2_000`) as a more robust fallback while still remaining far lower than ExoPlayer's default 50-second buffer.

---

### 🔵 Info

#### 1. Hardcoded Theme for AlertDialog Builder
- **Location**: [mobile/PlaybackActivity.kt:L603](file:///d:/projects/sports_tv/android_tv_app/mobile/src/main/java/com/sportstv/mobile/PlaybackActivity.kt#L603)
- **Code**:
  ```kotlin
  android.app.AlertDialog.Builder(this, android.R.style.Theme_DeviceDefault_Dialog_Alert)
  ```
- **Description**: Using the system hardcoded theme `Theme_DeviceDefault_Dialog_Alert` ensures the dialog styles match system settings. However, it bypasses the app's current theme/color palette (e.g., custom primary dark and rose-red/neon-blue accents).
- **Recommendation**: If a more cohesive brand design is desired, customize a dialog theme in `res/values/styles.xml` (e.g. extending MaterialAlertDialog) and reference it here.

#### 2. Duplicate Clean Referer Logic
- **Location**:
  - `cleanReferer()` in `mobile/PlaybackActivity.kt`
  - `cleanReferer()` in `app/PlaybackActivity.kt`
- **Description**: Both mobile and TV PlaybackActivities define duplicate helper functions to sanitize referer URLs before making HLS requests.
- **Recommendation**: In a future refactoring phase, move such shared utility functions into a common module or shared utility class (e.g. `NetworkUtils` or `UrlHelper`) to adhere to DRY (Don't Repeat Yourself) principles.

---

## Auto-Fix Status

No Critical issues found. The Warning regarding the unused compiler variable in the TV app can be safely resolved.

- **Recommended action**: Remove the unused line `val isIpUrl = ...` in [app/PlaybackActivity.kt](file:///d:/projects/sports_tv/android_tv_app/app/src/main/java/com/sportstv/app/PlaybackActivity.kt#L144).

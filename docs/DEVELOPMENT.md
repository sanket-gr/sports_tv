<!-- generated-by: gsd-doc-writer -->
# Development Guide

This document outlines the local setup, build commands, coding standards, and workflows for developing the Sports TV App project.

## Local Setup

To prepare the repository for active development:
1. Follow the installation steps in [GETTING-STARTED.md](GETTING-STARTED.md).
2. Set up your local environment variables in `backend/.env` if you need custom database paths or overrides (see [CONFIGURATION.md](CONFIGURATION.md)).
3. Enable developer mode on your target TV or phone testing devices.

---

## Build and Run Commands

The project uses Gradle for the Android clients and standard Python tooling for the FastAPI backend.

| Scope | Command | Description |
|-------|---------|-------------|
| **Backend** | `uvicorn main:app --reload` | Starts the local backend development server with hot-reload. |
| **Backend** | `alembic revision --autogenerate -m "..."` | Generates a new database migration file. |
| **Backend** | `alembic upgrade head` | Runs pending database migrations. |
| **Android TV** | `gradlew :app:assembleDebug` | Compiles the Android TV debug APK. |
| **Android TV** | `gradlew :app:assembleRelease` | Compiles the Android TV signed release APK. |
| **Android Mobile** | `gradlew :mobile:assembleDebug` | Compiles the Android Mobile debug APK. |
| **Android Mobile** | `gradlew :mobile:assembleRelease` | Compiles the Android Mobile signed release APK. |

---

## Code Style & Formatting

### Kotlin (Android TV & Mobile)
* **IDE Setup:** Code formatting is managed by Android Studio's built-in formatter. Always run code formatting (`Ctrl+Alt+L` on Windows/Linux or `Cmd+Option+L` on macOS) before committing.
* **Network Call:** All network calls to `ApiClient` must be made inside coroutines using `lifecycleScope.launch` or similar coroutine builders.
* **Screen State:** Video player screens (`PlaybackActivity`) must keep the screen awake using `window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)` during active playback.

### Python (Backend)
* **Formatting:** Follow PEP 8 guidelines. Standard tools like `black` or `autopep8` can be used.
* **Playwright Async:** All Playwright scraping methods are asynchronous. Ensure proper usage of `await` on page elements and network interception hooks.

---

## Branching & PR Conventions

1. **Main Branch:** The `main` branch is the default branch. It should always remain in a compilable and deployable state.
2. **Feature Branches:** Create a feature branch for new developments:
   * Pattern: `feat/feature-name` (for new features)
   * Pattern: `fix/bug-name` (for bug fixes)
3. **Commit Messages:** Use descriptive commit messages. (e.g. `Fix database auto-creation and volume directory mounting on startup`).
4. **Pull Requests:** Before opening a PR or merging code:
   * Verify the Android app compiles successfully without errors.
   * Verify that the backend starts up without any database crashes or unresolved migrations.

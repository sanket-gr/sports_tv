<!-- generated-by: gsd-doc-writer -->
# Testing Guide

This document explains the testing strategies, frameworks, and commands for validating the Sports TV App project.

## Testing Frameworks

### Android Client (app & mobile)
* **Unit Testing:** JUnit 4/5 is used for local unit tests (testing API model parsing, helper utility functions).
* **Instrumented/UI Testing:** AndroidX Test and Espresso are configured for testing UI activities on devices or emulators.

### Backend
* **Scraper Testing:** Manual script execution is preferred for verifying scraper extraction selectors (since live streaming portals frequently change their HTML structure).
* **API Testing:** Manual API validation can be performed using Postman or Python `requests` calls against localhost/AWS endpoints.

---

## Running Tests

### Running Android Unit Tests
To run unit tests across both `app` and `mobile` modules from the command line:
```bash
cd android_tv_app
./gradlew test
```
Or right-click the `src/test/` directory in Android Studio and select **Run 'Tests in...'**.

### Running Android Instrumented Tests
To execute instrumented UI tests (requires an active emulator or connected device):
```bash
cd android_tv_app
./gradlew connectedAndroidTest
```

### Running Local Scraper Tests
You can test the Playwright extraction logic in isolation by writing simple scratch scripts that import the scraper module. For example, create a temporary script `test_scraper.py` in the `backend/` directory:
```python
import asyncio
from scrapers import extract_async
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        # Test SportSurge URL extraction
        res = await extract_async("https://sportsurge.ws/some-match-link", browser)
        print("Scraper result:", res)
        await browser.close()

asyncio.run(test())
```
Run this script with:
```bash
python test_scraper.py
```

---

## Manual Verification Checklist

Before releasing or deploying code changes, perform these manual verification steps:

1. **Backend Startup:** Run the FastAPI backend locally or via Docker and verify `http://localhost:8000/admin` loads without database errors.
2. **Stream Extraction:** Submit a live stream link on the Admin Panel and check that:
   * A stream record is created.
   * Scraper runs in the background and resolves the direct HLS url.
   * No `[ERROR]` is appended to the stream title.
3. **App Stream List:** Open the Android TV app, navigate categories, and verify that the newly added stream appears on the list.
4. **ExoPlayer Playback:** Click the stream card in the app and verify:
   * Video starts playing within 5-10 seconds.
   * Play/pause controls work.
   * Aspect ratio toggles function.
   * Screen remains awake (no screensaver activates during playback).

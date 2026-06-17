<!-- generated-by: gsd-doc-writer -->
# Sports TV App

An Android TV and mobile application that extracts and streams live sports events from online platforms using a Python FastAPI backend.

## Overview

Sports TV App consists of two main parts:
1. **FastAPI Backend:** Containerized Python service that scrapes live sports streaming portals (Sportsurge, watchmmafull, jokertvguide, etc.) using Playwright to extract raw HLS (.m3u8) stream URLs. It includes a web-based Admin Panel to add/delete categories and streams.
2. **Android TV & Mobile Clients:** A Native Kotlin application optimized for both Android TV (Leanback interface) and Android Mobile devices. It communicates with the FastAPI backend to fetch streams and play them back using ExoPlayer.

## Installation

### Prerequisites
* Python 3.10+ (for backend)
* Docker & Docker Compose (for backend deployment)
* Android Studio (for compiling Android clients)

### Backend Installation (Local Setup)
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Playwright browsers:
   ```bash
   playwright install chromium
   ```

### Android Clients
1. Open the `android_tv_app` directory in Android Studio.
2. Allow Gradle to sync dependencies.

## Quick Start

### 1. Start the Backend
From the `backend/` directory, run:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Access the Admin Panel at `http://localhost:8000/admin`.

### 2. Run the Android Apps
1. Open Android Studio.
2. In the run configuration dropdown, select:
   * **`app`** to run on an Android TV emulator or physical TV.
   * **`mobile`** to run on a mobile device or phone emulator.
3. Click **Run** (green play icon ▶️).

## Usage Examples

### Adding a Stream on Admin Panel
1. Navigate to `http://localhost:8000/admin`.
2. Select a sport category (e.g. UFC, Football).
3. Paste the streaming source URL (e.g. Sportsurge match portal).
4. Hit **Add Stream**. The backend will run the background scraper using Playwright, resolve the direct HLS stream link, and make it available to the TV app automatically.

### API Endpoints
The Android TV/Mobile client requests data using these endpoints:
* `GET /api/categories` - Returns JSON list of all categories.
* `GET /api/streams` - Returns JSON list of all active streams.
* `GET /api/streams/{id}/refresh` - Force re-scrapes the live stream to fetch a fresh token.

## License

Private Repository / Proprietary. All rights reserved.

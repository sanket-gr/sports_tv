<!-- generated-by: gsd-doc-writer -->
# Configuration Guide

This document lists the environment variables and configurations used in the Sports TV App backend and client projects.

## Environment Variables

The backend service is configured primarily using environment variables. These can be set directly in your shell or defined in the `environment` section of your `docker-compose.yml`.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Optional | `sqlite:///./sports_tv.db` | The SQLAlchemy connection string. Supports SQLite and PostgreSQL. |
| `ENVIRONMENT` | Optional | `development` | Setting this to `production` enables JSON formatting for logs instead of standard plain-text logs. |
| `PYTHONUNBUFFERED` | Optional | `1` | Ensures python console logs print instantly without buffering. |

<!-- VERIFY: Production PostgreSQL connection string if deploying to Render/AWS RDS -->

## Required vs. Optional Settings

* **Database Connection:** By default, if no `DATABASE_URL` is provided, the backend will initialize a local SQLite database (`sports_tv.db`) inside the directory structure. In production Docker setups, `DATABASE_URL` is configured to output inside a persistent directory mount (`sqlite:///./db/sports_tv.db`).
* **Playwright Environment:** Playwright requires a valid Chromium browser installation. In the Docker container, this is pre-installed in the base image. For local development on Windows, Playwright must be manually installed using `playwright install`.

## Android Client Configuration

The Android application needs to point to the correct backend server IP address to retrieve streams.

### URL Settings (`ApiClient.kt`)
Each module (`app` and `mobile`) has its own `ApiClient.kt` file.

File locations:
* Android TV: `android_tv_app/app/src/main/java/com/sportstv/app/ApiClient.kt`
* Android Mobile: `android_tv_app/mobile/src/main/java/com/sportstv/mobile/ApiClient.kt`

Modify the `BASE_URL` constant in both files:
```kotlin
// Change this to your deployed AWS server IP
const val BASE_URL = "http://13.126.62.185/"
```

<!-- VERIFY: Deployed AWS EC2 public IPv4 address -->

## Per-Environment Configuration

### Local Development (Windows / macOS)
* Logging: Plain text format with timestamps.
* Database: Standard local file `sports_tv.db` in the backend root.
* Android: pointing to your laptop's local IP address (e.g. `http://192.168.100.104:8000/`).

### Production (Docker / AWS EC2)
* Logging: Structured JSON formatting (standard for CloudWatch or Docker logs).
* Database: SQLite database located in a mounted volume directory (`/app/db/sports_tv.db`) to persist data across container rebuilds.
* Android: Pointing to the public EC2 IP (`http://13.126.62.185/`).

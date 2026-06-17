<!-- generated-by: gsd-doc-writer -->
# Getting Started

Follow this guide to set up your local development environment and run the Sports TV App backend and client applications.

## Prerequisites

Before starting, ensure you have the following installed on your machine:
* **Python 3.10+**
* **Node.js** (optional, useful for GSD tooling)
* **Android Studio** (Koala or newer recommended)
* **Java Development Kit (JDK) 17** (Embedded in Android Studio)
* **Git**

---

## Installation Steps

### 1. Clone the Repository
Clone the project to your local machine:
```bash
git clone https://github.com/sanket-gr/sports_tv.git
cd sports_tv
```

### 2. Set Up the Backend
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Install Playwright browser binaries:
   ```bash
   playwright install chromium
   ```

### 3. Set Up the Android Project
1. Launch **Android Studio**.
2. Click **Open** and select the `android_tv_app` directory.
3. Gradle will begin syncing dependencies. Wait for the sync to complete.

---

## First Run

### 1. Launch the Backend
From the `backend/` directory (with virtual environment activated):
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Open `http://localhost:8000/admin` in your web browser. You should see the Admin Panel.

### 2. Run the Android Client App
1. In Android Studio, connect your physical Android phone (with USB Debugging enabled) or start an Android TV emulator.
2. Select either **`app`** (TV app) or **`mobile`** (Mobile app) from the run configurations dropdown.
3. Click the green **Run** ▶️ button.

---

## Common Setup Issues

### Issue 1: Playwright OS dependencies missing (Linux / Docker)
If you run the backend on a bare Linux server and get Playwright browser launch errors:
* **Solution:** Install browser system dependencies:
  ```bash
  playwright install-deps chromium
  ```
  *(Or run the application inside the provided Docker container which comes with all dependencies pre-installed).*

### Issue 2: App fails to connect to local backend ("Cannot connect" error)
If the Android emulator or device cannot reach your local backend:
* **Solution:** 
  1. Check your PC's local IP address (run `ipconfig` on Windows or `ifconfig` on Mac).
  2. Open `ApiClient.kt` in the respective module and set `BASE_URL` to `http://<YOUR_PC_IP>:8000/`.
  3. Ensure both the PC and the testing phone/TV are on the exact same WiFi network.

### Issue 3: SQLite Database Table Missing on Clean Run
If the backend crashes on start with `no such table: categories`:
* **Solution:** Ensure `create_tables()` is uncommented in `lifespan` inside `main.py` so SQLAlchemy can initialize tables. (This has been resolved in the codebase).

---

## Next Steps
* Learn more about coding conventions, build scripts, and formatting in [DEVELOPMENT.md](DEVELOPMENT.md).
* Find out how to run backend unit tests and integration tests in [TESTING.md](TESTING.md).
* See the deployment guide to push to AWS in [DEPLOYMENT.md](DEPLOYMENT.md).

# 📂 Folder Structure

> Current state vs recommended clean structure. Migrate gradually — one PR per section.

---

## Current Structure (As-Is)

```
/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── extractor.py
│   ├── deobfuscator.js          ← JS bypass scripts loose in root
│   ├── decrypt_player.js        ← JS bypass scripts loose in root
│   ├── extract_deobfuscator.py  ← mixed with production code
│   ├── test_mma.py              ← test scripts loose in root
│   ├── test_requests_mma.py     ← test scripts loose in root
│   ├── test_decrypt.py          ← test scripts loose in root
│   ├── templates/
│   ├── sports_tv.db             ← SQLite DB committed to repo
│   └── render.yaml
│
└── android_tv_app/
    └── app/src/main/
        ├── java/com/sportstv/app/
        │   ├── MainActivity.kt
        │   ├── MainFragment.kt
        │   └── PlaybackActivity.kt
        └── res/
            ├── layout/activity_playback.xml
            └── layout/activity_main.xml
```

---

## Recommended Structure (To-Be)

```
/
├── .planning/                      ← GSD planning docs (this folder)
│   └── codebase/
│       ├── PROJECT.md
│       ├── ROADMAP.md
│       ├── REFACTOR.md
│       ├── GIT-WORKFLOW.md
│       ├── FOLDER-STRUCTURE.md
│       └── API.md
│
├── backend/
│   ├── main.py                     ← FastAPI entry point
│   ├── database.py                 ← SQLAlchemy models
│   ├── extractor.py                ← High-level extraction orchestrator
│   │
│   ├── scrapers/                   ← NEW: one file per source
│   │   ├── __init__.py
│   │   ├── base.py                 ← Abstract scraper interface
│   │   ├── watchmmafull.py
│   │   └── vidplayer.py
│   │
│   ├── bypass/                     ← NEW: group all obfuscation tools
│   │   ├── deobfuscator.js
│   │   ├── decrypt_player.js
│   │   └── extract_deobfuscator.py
│   │
│   ├── tests/                      ← NEW: proper pytest structure
│   │   ├── __init__.py
│   │   ├── test_scrapers.py
│   │   ├── test_extractor.py
│   │   └── test_api.py
│   │
│   ├── templates/                  ← Jinja2 / HTML templates (unchanged)
│   ├── render.yaml
│   └── requirements.txt
│
├── android_tv_app/
│   └── app/src/main/
│       ├── java/com/sportstv/app/
│       │   ├── MainActivity.kt
│       │   ├── MainFragment.kt
│       │   ├── PlaybackActivity.kt
│       │   └── model/              ← NEW: data classes / API models
│       │       └── Stream.kt
│       └── res/
│           ├── layout/
│           │   ├── activity_main.xml
│           │   └── activity_playback.xml
│           └── values/
│
├── .gitignore
└── README.md
```

---

## Migration Checklist

### Backend
- [ ] Create `backend/scrapers/` and move scraper logic out of `extractor.py`
- [ ] Create `backend/bypass/` and move `deobfuscator.js`, `decrypt_player.js`, `extract_deobfuscator.py`
- [ ] Create `backend/tests/` and migrate `test_*.py` files
- [ ] Add `sports_tv.db` to `.gitignore` (do not commit local DBs)
- [ ] Ensure `requirements.txt` is complete and up to date

### Android
- [ ] Create `model/` package for data classes (keep `Stream`, `Channel` etc. separate from Activities)

### Root
- [ ] Add/update `.gitignore` (exclude `*.db`, `__pycache__`, `.env`, `node_modules`)
- [ ] Add `README.md` with setup instructions for both backend and Android

---

## .gitignore Additions

```gitignore
# Database
*.db
*.sqlite

# Python
__pycache__/
*.pyc
.env
venv/
.venv/

# Android
*.apk
*.aab
.gradle/
local.properties
android_tv_app/.idea/

# Node (for bypass scripts)
node_modules/

# OS
.DS_Store
Thumbs.db
```

---

_Last updated: 2026-06-15_

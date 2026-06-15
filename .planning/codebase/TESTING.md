---
last_mapped_date: 2026-06-15
---

# 🧪 Testing

## Backend Testing
- **Script-Based Unit Tests**: Testing is primarily performed via individual scripts located in `backend/` (e.g., `test_mma.py`, `test_requests_mma.py`, `test_decrypt.py`).
- **Scraper Validation**: These test scripts directly hit target websites and validate that the obfuscation bypasses are successfully extracting valid HLS (m3u8) URLs before integrating them into `main.py` or `extractor.py`.
- **Framework**: Standard `assert` statements and ad-hoc print debugging rather than a structured framework like `pytest` or `unittest`.

## Frontend Testing
- **Manual Verification**: Currently, testing Android TV applications heavily relies on manual User Acceptance Testing (UAT) either on an emulator or physical devices via ADB.
- **No Automated Test Suites**: The `android_tv_app/` lacks structured `androidTest` or unit test suites, which is typical for fast-iterating UI-heavy media apps in prototype stages.

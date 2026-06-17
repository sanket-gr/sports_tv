# Phase 4: Ops & Deployment

This is the final phase of the roadmap. The goal is to make the backend production-ready by finalizing the PostgreSQL migration infrastructure and implementing structured JSON logging for better observability in production environments (like AWS, Render, or GCP).

## User Review Required
> [!IMPORTANT]
> **Database Migrations**: Currently, the backend uses `Base.metadata.create_all()` which is great for SQLite local dev but dangerous for production PostgreSQL. I will introduce **Alembic** to manage database schema migrations moving forward. If you already have a production PostgreSQL database running, this will establish the baseline schema.

## Proposed Changes

### 1. Database Migrations (Alembic)
#### [MODIFY] `requirements.txt`
- Add `alembic` to the dependencies.

#### [NEW] `alembic/` & `alembic.ini`
- Initialize Alembic using `alembic init alembic`.
- Configure `alembic/env.py` to import `database.Base` and read the `DATABASE_URL` environment variable.
- Generate the initial baseline migration script (`alembic revision --autogenerate -m "Initial schema"`).

#### [MODIFY] `main.py`
- Remove the automatic `create_tables()` call on startup, as production systems should apply migrations explicitly via Alembic before the app boots.

### 2. Structured JSON Logging
#### [MODIFY] `requirements.txt`
- Add `python-json-logger` to format logs as structured JSON.

#### [MODIFY] `main.py` & `scrapers.py`
- Configure the standard Python `logging` module to use `python-json-logger.jsonlogger.JsonFormatter` when deployed.
- This will convert standard `logger.info("message")` calls into parsable JSON objects containing timestamps, log levels, and request context, making it much easier to debug production issues in cloud log viewers.

## Verification Plan

### Automated Tests
- Run `pytest` to ensure the testing database (SQLite) still functions perfectly with the new logging logic.

### Manual Verification
- **Logging**: Run the backend server locally and verify that console logs are output as structured JSON objects.
- **Alembic**: Inspect the generated Alembic migration file to ensure all models (`Category`, `Stream`, `SourceConfig`) are mapped correctly.

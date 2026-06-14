"""
main.py  –  FastAPI backend for Sports TV App.

Endpoints:
  Admin dashboard:
    GET  /admin              ->  admin panel HTML
    POST /admin/categories   ->  add a category
    POST /admin/streams      ->  submit a URL (triggers extraction), add a stream
    DELETE /admin/streams/{id}  ->  remove a stream
    DELETE /admin/categories/{id} -> remove a category

  TV App API (JSON):
    GET  /api/categories     ->  list all categories
    GET  /api/streams        ->  list all live streams
    GET  /api/streams/{id}   ->  single stream detail
"""
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Depends, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db, create_tables, Category, Stream
import extractor

# ---------------------------------------------------------------------------
TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_tables()
    db = next(get_db())
    if db.query(Category).count() == 0:
        defaults = [
            Category(name="Football",    icon="⚽", sort_order=1),
            Category(name="Basketball",  icon="🏀", sort_order=2),
            Category(name="Tennis",      icon="🎾", sort_order=3),
            Category(name="Cricket",     icon="🏏", sort_order=4),
            Category(name="Rugby",       icon="🏉", sort_order=5),
            Category(name="MMA",         icon="🥊", sort_order=6),
            Category(name="Hockey",      icon="🏒", sort_order=7),
            Category(name="Golf",        icon="⛳", sort_order=8),
        ]
        db.add_all(defaults)
        db.commit()
    db.close()
    yield  # App runs here
    # Shutdown (nothing needed)


app = FastAPI(title="Sports TV Admin API", version="1.0.0", lifespan=lifespan)

# ===========================================================================
# ADMIN  –  HTML dashboard
# ===========================================================================

@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    categories = db.query(Category).order_by(Category.sort_order).all()
    streams    = db.query(Stream).order_by(Stream.created_at.desc()).all()
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={"categories": categories, "streams": streams},
    )


@app.post("/admin/categories")
def add_category(
    name:       str = Form(...),
    icon:       str = Form("🏆"),
    sort_order: int = Form(99),
    db: Session = Depends(get_db),
):
    existing = db.query(Category).filter_by(name=name).first()
    if not existing:
        db.add(Category(name=name, icon=icon, sort_order=sort_order))
        db.commit()
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/categories/{cat_id}/delete")
def delete_category(cat_id: int, db: Session = Depends(get_db)):
    cat = db.query(Category).filter_by(id=cat_id).first()
    if cat:
        db.delete(cat)
        db.commit()
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/streams")
def add_stream(
    background_tasks: BackgroundTasks,
    category_id:  int = Form(...),
    source_url:   str = Form(...),
    db: Session = Depends(get_db),
):
    """Submit a stream URL. Extraction runs in the background."""
    cat = db.query(Category).filter_by(id=category_id).first()
    if not cat:
        return RedirectResponse("/admin?error=category_not_found", status_code=303)

    # Create placeholder immediately so admin can see it
    stream = Stream(
        category_id  = category_id,
        title        = "Extracting...",
        source_url   = source_url,
        is_live      = True,
    )
    db.add(stream)
    db.commit()
    db.refresh(stream)
    stream_id = stream.id

    # Run extraction in background to avoid blocking the request
    background_tasks.add_task(_run_extraction, stream_id, source_url)

    return RedirectResponse("/admin", status_code=303)


def _run_extraction(stream_id: int, source_url: str):
    """Background task: extract metadata + HLS link and update the DB record."""
    db = next(get_db())
    stream = db.query(Stream).filter_by(id=stream_id).first()
    if not stream:
        return
    # Initialize progress
    stream.progress = 0
    db.commit()
    try:
        # Step 1: fetch page and parse metadata
        data = extractor.extract(source_url)
        # Update after metadata extraction (approx 30%)
        stream.progress = 30
        db.commit()
        # Update fields
        stream.title = data.get("title", "Unknown")
        stream.sport = data.get("sport", "")
        stream.participants = data.get("participants", "")
        stream.iframe_url = data.get("iframe_url", "")
        stream.hls_url = data.get("hls_url", "")
        stream.thumbnail_url = data.get("thumbnail_url", "")
        # Update after iframe handling (approx 60%)
        stream.progress = 60
        db.commit()
        # Final step: mark completed
        stream.progress = 100
        db.commit()
    except Exception as e:
        stream.title = f"[ERROR] {e}"
        stream.progress = 100
        db.commit()
    finally:
        db.close()


@app.post("/admin/streams/{stream_id}/delete")
def delete_stream(stream_id: int, db: Session = Depends(get_db)):
    stream = db.query(Stream).filter_by(id=stream_id).first()
    if stream:
        db.delete(stream)
        db.commit()
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/streams/{stream_id}/refresh")
def refresh_stream(
    stream_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Re-run extraction for an existing stream (e.g., to get a fresh token)."""
    stream = db.query(Stream).filter_by(id=stream_id).first()
    if stream:
        stream.title = "Re-extracting..."
        db.commit()
        background_tasks.add_task(_run_extraction, stream_id, stream.source_url)
    return RedirectResponse("/admin", status_code=303)


# ===========================================================================
# TV APP API  –  JSON endpoints consumed by the Android app
# ===========================================================================

@app.get("/api/categories")
def api_categories(db: Session = Depends(get_db)):
    cats = db.query(Category).order_by(Category.sort_order).all()
    return [
        {
            "id":         c.id,
            "name":       c.name,
            "icon":       c.icon,
            "sort_order": c.sort_order,
        }
        for c in cats
    ]


@app.get("/api/streams")
def api_streams(
    category_id: Optional[int] = None,
    live_only:   bool = True,
    db: Session = Depends(get_db),
):
    q = db.query(Stream)
    if live_only:
        q = q.filter(Stream.is_live == True)
    if category_id:
        q = q.filter(Stream.category_id == category_id)
    streams = q.order_by(Stream.created_at.desc()).all()
    return [_stream_to_dict(s) for s in streams]


@app.get("/api/streams/{stream_id}")
def api_stream_detail(stream_id: int, db: Session = Depends(get_db)):
    s = db.query(Stream).filter_by(id=stream_id).first()
    if not s:
        return JSONResponse(status_code=404, content={"detail": "Stream not found"})
    return _stream_to_dict(s)


@app.get("/api/streams/{stream_id}/refresh")
def api_stream_refresh(
    stream_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Re-extract HLS URL for a stream (called by TV app when token expires).
    Triggers background extraction and returns the current stream data immediately.
    The TV app should poll /api/streams/{id} after a few seconds for the fresh URL."""
    s = db.query(Stream).filter_by(id=stream_id).first()
    if not s:
        return JSONResponse(status_code=404, content={"detail": "Stream not found"})
    # Only re-extract if we have a source URL
    if s.source_url:
        s.progress = 0
        db.commit()
        background_tasks.add_task(_run_extraction, stream_id, s.source_url)
    return _stream_to_dict(s)


def _stream_to_dict(s: Stream) -> dict:
    return {
        "id":            s.id,
        "category_id":   s.category_id,
        "category_name": s.category.name if s.category else "",
        "category_icon": s.category.icon if s.category else "",
        "title":         s.title,
        "participants":  s.participants,
        "sport":         s.sport,
        "source_url":    s.source_url,
        "iframe_url":    s.iframe_url,
        "hls_url":       s.hls_url,
        "thumbnail_url": s.thumbnail_url,
        "is_live":       s.is_live,
        "created_at":    s.created_at.isoformat() if s.created_at else "",
    }


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

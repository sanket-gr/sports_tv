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
import asyncio
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    # Playwright requires the proactor event loop on Windows to spawn subprocesses
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Any

from fastapi import FastAPI, Depends, Request, Form, BackgroundTasks, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import secrets
from sqlalchemy.orm import Session
import asyncio
import httpx
from playwright.async_api import async_playwright

from database import get_db, create_tables, Category, Stream, SourceConfig, WatchAnalytics
from scrapers import extract_async as run_scrapers_extract

import logging
import os
from pythonjsonlogger import jsonlogger

logger = logging.getLogger(__name__)

# Setup JSON logging for production, standard formatting for local dev
logHandler = logging.StreamHandler()
if os.environ.get("ENVIRONMENT") == "production":
    formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
else:
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logHandler.setFormatter(formatter)

# Remove default handlers and add our own
logging.basicConfig(level=logging.INFO, handlers=[logHandler], force=True)

# ---------------------------------------------------------------------------
TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


async def stream_refresh_worker(app: FastAPI):
    """Background task to refresh stale streams."""
    while True:
        try:
            await asyncio.sleep(60) # Wake up every 1 minute
            db = next(get_db())
            
            # Find live streams that haven't been updated in 15 minutes, or never updated
            now = datetime.utcnow()
            stale_streams = db.query(Stream).filter(
                Stream.is_live == True,
                Stream.source_url != ""
            ).all()
            
            for stream in stale_streams:
                # Skip direct HLS links
                if stream.source_url == stream.hls_url or (stream.source_url and ".m3u8" in stream.source_url.lower()):
                    continue
                # If it's missing updated_at, or it's been > 15 minutes
                if not stream.hls_updated_at or (now - stream.hls_updated_at).total_seconds() > 900:
                    logger.info(f"Auto-refreshing stale stream {stream.id}: {stream.title}")
                    browser = getattr(app.state, "browser", None)
                    # Use asyncio.create_task to run concurrently without blocking the worker
                    asyncio.create_task(_run_extraction(stream.id, stream.source_url, stream.fallback_url or "", browser))
                    
            db.close()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in stream_refresh_worker: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # In production, migrations should be applied via Alembic (e.g. `alembic upgrade head`)
    # For local SQLite development, we can still call create_tables if we want, but letting Alembic handle it is better.
    # We leave this commented out to enforce Alembic migrations.
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
    
    # Ensure UFC category exists
    ufc_cat = db.query(Category).filter_by(name="UFC").first()
    if not ufc_cat:
        db.add(Category(name="UFC", icon="🥊", sort_order=9))
        db.commit()

    # Seed initial SourceConfigs if missing
    if db.query(SourceConfig).count() == 0:
        sources = [
            SourceConfig(name="Sportsurge", domain="sportsurge.ws"),
            SourceConfig(name="WatchMMAFull", domain="watchmmafull.com"),
            SourceConfig(name="JokerTVGuide", domain="jokertvguide.sx"),
            SourceConfig(name="Vidplayer", domain="vidplayer.com")
        ]
        db.add_all(sources)
        db.commit()

    db.close()
    
    # Launch persistent playwright session
    try:
        app.state.playwright = await async_playwright().start()
        launch_kwargs = {"headless": True}
        scraper_proxy = os.environ.get("SCRAPER_PROXY")
        if scraper_proxy:
            from scrapers import parse_playwright_proxy
            launch_kwargs["proxy"] = parse_playwright_proxy(scraper_proxy)
            logger.info(f"Using scraper proxy for persistent browser session: {scraper_proxy}")
        app.state.browser = await app.state.playwright.chromium.launch(**launch_kwargs)
    except Exception as e:
        logger.error(f"Failed to start playwright pooling: {e}")
        app.state.playwright = None
        app.state.browser = None

    refresh_task = asyncio.create_task(stream_refresh_worker(app))

    admin_username = os.environ.get("ADMIN_USERNAME")
    admin_password = os.environ.get("ADMIN_PASSWORD")
    if not admin_username or not admin_password:
        logger.warning("WARNING: Admin panel is running WITHOUT authentication. Set ADMIN_USERNAME and ADMIN_PASSWORD env variables to secure it.")

    yield  # App runs here
    
    # Shutdown
    refresh_task.cancel()
    try:
        if getattr(app.state, "browser", None):
            await app.state.browser.close()
        if getattr(app.state, "playwright", None):
            await app.state.playwright.stop()
    except Exception as e:
        logger.warning(f"Error during playwright shutdown: {e}")


app = FastAPI(title="Sports TV Admin API", version="1.0.0", lifespan=lifespan)

# Serve APKs statically
APKS_DIR = Path(__file__).parent / "apks"
app.mount("/apks", StaticFiles(directory=str(APKS_DIR)), name="apks")

security = HTTPBasic(auto_error=False)

def get_current_admin(credentials: Optional[HTTPBasicCredentials] = Depends(security)):
    admin_username = os.environ.get("ADMIN_USERNAME")
    admin_password = os.environ.get("ADMIN_PASSWORD")
    if not admin_username or not admin_password:
        return True
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized access",
            headers={"WWW-Authenticate": "Basic"},
        )
    correct_username = secrets.compare_digest(credentials.username, admin_username)
    correct_password = secrets.compare_digest(credentials.password, admin_password)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True

# ===========================================================================
# USER CLIENT  –  Web player dashboard
# ===========================================================================

@app.get("/", response_class=HTMLResponse)
def index_page(
    request: Request,
    db: Session = Depends(get_db),
):
    categories = db.query(Category).order_by(Category.sort_order).all()
    streams    = db.query(Stream).filter(Stream.is_live == True).order_by(Stream.created_at.desc()).all()
    sources    = db.query(SourceConfig).filter(SourceConfig.is_active == True).all()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "categories": categories,
            "streams": streams,
            "sources": sources,
        },
    )

# ===========================================================================
# ADMIN  –  HTML dashboard
# ===========================================================================

from sqlalchemy.sql import func

@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    authenticated: bool = Depends(get_current_admin),
):
    categories = db.query(Category).order_by(Category.sort_order).all()
    streams    = db.query(Stream).order_by(Stream.created_at.desc()).all()
    sources    = db.query(SourceConfig).all()
    
    total_seconds = db.query(func.sum(WatchAnalytics.duration_seconds)).scalar() or 0
    total_hours = round(total_seconds / 3600, 1)
    
    # Calculate source health metrics for dashboard
    online_sources = sum(1 for s in sources if s.last_health_status == "Online")
    total_sources = len(sources)
    
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "categories": categories, 
            "streams": streams, 
            "sources": sources,
            "total_hours": total_hours,
            "online_sources": online_sources,
            "total_sources": total_sources
        },
    )


@app.post("/admin/categories")
def add_category(
    name:       str = Form(...),
    icon:       str = Form("🏆"),
    sort_order: int = Form(99),
    db: Session = Depends(get_db),
    authenticated: bool = Depends(get_current_admin),
):
    existing = db.query(Category).filter_by(name=name).first()
    if not existing:
        db.add(Category(name=name, icon=icon, sort_order=sort_order))
        db.commit()
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/categories/{cat_id}/delete")
def delete_category(
    cat_id: int,
    db: Session = Depends(get_db),
    authenticated: bool = Depends(get_current_admin),
):
    cat = db.query(Category).filter_by(id=cat_id).first()
    if cat:
        db.delete(cat)
        db.commit()
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/streams")
def add_stream(
    request: Request,
    background_tasks: BackgroundTasks,
    category_id:  int = Form(...),
    source_url:   str = Form(""),
    fallback_url: str = Form(""),
    title:        str = Form(""),
    hls_url:      str = Form(""),
    db: Session = Depends(get_db),
    authenticated: bool = Depends(get_current_admin),
):
    """Submit a stream URL. Extraction runs in the background, or added manually."""
    cat = db.query(Category).filter_by(id=category_id).first()
    if not cat:
        return RedirectResponse("/admin?error=category_not_found", status_code=303)

    # If direct HLS URL is provided, bypass Playwright scraper
    if hls_url:
        stream = Stream(
            category_id  = category_id,
            title        = title or "Manual Stream",
            source_url   = source_url or hls_url,
            fallback_url = fallback_url,
            hls_url      = hls_url,
            hls_updated_at = datetime.utcnow(),
            is_live      = True,
        )
        db.add(stream)
        db.commit()
        return RedirectResponse("/admin", status_code=303)

    if not source_url:
        return RedirectResponse("/admin?error=missing_source_url", status_code=303)

    # Create placeholder immediately so admin can see it
    stream = Stream(
        category_id  = category_id,
        title        = title or "Extracting...",
        source_url   = source_url,
        fallback_url = fallback_url,
        is_live      = True,
    )
    db.add(stream)
    db.commit()
    db.refresh(stream)
    stream_id = stream.id

    # Run extraction in background
    browser = getattr(request.app.state, "browser", None)
    background_tasks.add_task(_run_extraction, stream_id, source_url, fallback_url, browser)

    return RedirectResponse("/admin", status_code=303)


async def _run_extraction(stream_id: int, source_url: str, fallback_url: str, browser: Any):
    """Background task to extract HLS url and update DB."""
    db: Session = next(get_db())
    try:
        results = await run_scrapers_extract(source_url, browser)
        
        # Fallback logic
        if (not results or (isinstance(results, dict) and results.get("title", "").startswith("[ERROR]"))) and fallback_url:
            logger.info(f"Source URL failed, trying fallback: {fallback_url}")
            results = await run_scrapers_extract(fallback_url, browser)
            
        # If it's a single dict, convert to list
        if isinstance(results, dict):
            results = [results]
            
        if not results:
            stream = db.query(Stream).filter(Stream.id == stream_id).first()
            if stream:
                stream.title = "[ERROR] Extraction failed"
            db.commit()
            return
            
        # Update original stream with the first result
        stream = db.query(Stream).filter(Stream.id == stream_id).first()
        if not stream:
            return
            
        first_data = results[0]
        stream.title = first_data.get("title", "Unknown")
        stream.sport = first_data.get("sport", "")
        stream.participants = first_data.get("participants", "")
        if first_data.get("thumbnail_url"):
            stream.thumbnail_url = first_data["thumbnail_url"]
        
        stream.source_url = first_data.get("source_url", source_url)
        stream.iframe_url = first_data.get("iframe_url", "")
        stream.hls_url = first_data.get("hls_url", "")
        stream.cf_domain = first_data.get("cf_domain", "")
        
        # Determine is_live based on HLS
        if stream.hls_url:
            stream.is_live = True
            stream.hls_updated_at = datetime.utcnow()
        else:
            stream.is_live = False
            
        db.commit()
        
        # Create additional streams for the remaining results (Server 2, etc.)
        for extra_data in results[1:]:
            new_stream = Stream(
                category_id=stream.category_id,
                title=extra_data.get("title", "Unknown"),
                sport=extra_data.get("sport", ""),
                participants=extra_data.get("participants", ""),
                thumbnail_url=stream.thumbnail_url,
                source_url=extra_data.get("source_url", source_url),
                iframe_url=extra_data.get("iframe_url", ""),
                hls_url=extra_data.get("hls_url", ""),
                hls_updated_at=datetime.utcnow() if extra_data.get("hls_url") else None,
                cf_domain=extra_data.get("cf_domain", ""),
                is_live=bool(extra_data.get("hls_url")),
                progress=100
            )
            db.add(new_stream)
            
        db.commit()
    except Exception as e:
        stream = db.query(Stream).filter(Stream.id == stream_id).first()
        if stream:
            stream.title = f"[ERROR] {e}"
            stream.progress = 100
            db.commit()
    finally:
        db.close()


@app.post("/admin/streams/{stream_id}/delete")
def delete_stream(
    stream_id: int,
    db: Session = Depends(get_db),
    authenticated: bool = Depends(get_current_admin),
):
    stream = db.query(Stream).filter_by(id=stream_id).first()
    if stream:
        db.delete(stream)
        db.commit()
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/streams/bulk-delete")
async def bulk_delete_streams(
    request: Request,
    db: Session = Depends(get_db),
    authenticated: bool = Depends(get_current_admin),
):
    """Delete multiple streams at once."""
    form_data = await request.form()
    stream_ids = [int(x) for x in form_data.getlist("stream_ids") if str(x).isdigit()]
    if stream_ids:
        db.query(Stream).filter(Stream.id.in_(stream_ids)).delete(synchronize_session=False)
        db.commit()
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/streams/refresh-all")
def refresh_all_streams(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    authenticated: bool = Depends(get_current_admin),
):
    """Re-run extraction for all streams."""
    streams = db.query(Stream).filter(Stream.source_url != "").all()
    browser = getattr(request.app.state, "browser", None)
    for stream in streams:
        # Skip direct HLS links
        if stream.source_url == stream.hls_url or (stream.source_url and ".m3u8" in stream.source_url.lower()):
            continue
        stream.title = "Re-extracting..."
        background_tasks.add_task(_run_extraction, stream.id, stream.source_url, stream.fallback_url or "", browser)
    db.commit()
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/streams/{stream_id}/refresh")
def refresh_stream(
    stream_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    authenticated: bool = Depends(get_current_admin),
):
    """Re-run extraction for an existing stream (e.g., to get a fresh token)."""
    stream = db.query(Stream).filter_by(id=stream_id).first()
    if stream:
        if stream.source_url == stream.hls_url or (stream.source_url and ".m3u8" in stream.source_url.lower()):
            # For direct streams, refresh simply updates hls_updated_at to keep it fresh
            stream.hls_updated_at = datetime.utcnow()
            db.commit()
            return RedirectResponse("/admin", status_code=303)
            
        stream.title = "Re-extracting..."
        db.commit()
        browser = getattr(request.app.state, "browser", None)
        background_tasks.add_task(_run_extraction, stream_id, stream.source_url, stream.fallback_url or "", browser)
    return RedirectResponse("/admin", status_code=303)


# ===========================================================================
# TV APP API  –  JSON endpoints consumed by the Android app
# ===========================================================================


import urllib.parse
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@app.get("/api/proxy")
async def hls_proxy(
    request: Request,
    url: str,
    referer: str = "",
    db: Session = Depends(get_db),
):
    """
    HLS reverse-proxy: fetches the given CDN URL server-side (ignoring SSL errors
    for IP-based hosts) and rewrites relative segment URLs to route through this
    proxy endpoint. The Android app can therefore always connect to the trusted
    backend over plain HTTP on the local network.
    """
    import requests as req_lib
    import socket
    import ipaddress
    import re
    from fastapi.responses import PlainTextResponse

    # 1. Parse URL & validate format
    try:
        parsed_url = urllib.parse.urlparse(url)
        if parsed_url.scheme not in ("http", "https"):
            return PlainTextResponse("Forbidden: Invalid scheme", status_code=403)
        hostname = parsed_url.hostname
        if not hostname:
            return PlainTextResponse("Forbidden: Invalid host", status_code=400)
    except Exception:
        return PlainTextResponse("Forbidden: Malformed URL", status_code=400)

    # 2. Check if the IP is private (SSRF block)
    try:
        ip_addresses = socket.getaddrinfo(hostname, None)
        for addr in ip_addresses:
            ip_str = addr[4][0]
            # Strip scope ID if present in IPv6 address
            if "%" in ip_str:
                ip_str = ip_str.split("%")[0]
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return PlainTextResponse("Forbidden: Private IP access is blocked", status_code=403)
    except Exception as e:
        # Host name resolution failure will naturally fail on request.get, but if it resolves to local, block it.
        pass

    # 3. Check domain whitelist from DB SourceConfigs
    try:
        active_sources = db.query(SourceConfig).filter(SourceConfig.is_active == True).all()
        allowed_domains = ["hereisman.net", "aapmains.net", "sportsurge.ws", "watchmmafull.com", "jokertvguide.sx", "vidplayer.com", "vidplayer.live", "silverpathgardens.space", "virtualinfrastructure.space", "embed.st", "strmd.st", "cloudflarestorage.com"]
        for src in active_sources:
            if src.domain:
                allowed_domains.append(src.domain.lower())
        
        hostname_lower = hostname.lower()
        is_allowed = False
        is_raw_ip = bool(re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', hostname))
        
        if is_raw_ip:
            is_allowed = True
        else:
            for domain in allowed_domains:
                if hostname_lower == domain or hostname_lower.endswith("." + domain):
                    is_allowed = True
                    break
            
            # Allow kamfir domains (used by Sportsurge CDN providers)
            if not is_allowed and re.search(r'\bkamfir\d*\.space$', hostname_lower):
                is_allowed = True
        
        if not is_allowed:
            return PlainTextResponse("Forbidden: Domain not whitelisted", status_code=403)
    except Exception as e:
        logger.error(f"Error validating proxy URL domain: {e}")

    if not referer:
        parsed = urllib.parse.urlparse(url)
        referer = f"{parsed.scheme}://{parsed.netloc}/"

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 11; TV) AppleWebKit/537.36 Chrome/119 Safari/537.36",
        "Referer":    referer,
        "Origin":     referer.rstrip("/"),
        "Accept":     "*/*",
    }

    # 4. Conditional SSL verification: only False for raw IP-based URLs
    verify_ssl = not _needs_proxy(url)
    try:
        resp = req_lib.get(url, headers=headers, verify=verify_ssl, timeout=15, stream=True)
    except Exception as e:
        return PlainTextResponse(f"Proxy error: {e}", status_code=502)

    content_type = resp.headers.get("Content-Type", "application/octet-stream")

    # For HLS playlist files, rewrite URLs to route through this proxy
    if "mpegurl" in content_type.lower() or url.endswith(".m3u8") or url.endswith(".txt") or "playlist" in url.lower():
        body = resp.text
        base_url = url.rsplit("/", 1)[0] + "/"
        server_base = str(request.base_url)  # e.g. http://192.168.100.61:8000/

        lines = body.splitlines()
        rewritten = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                # It's a URI line – make it absolute then proxy it
                if stripped.startswith("http://") or stripped.startswith("https://"):
                    abs_url = stripped
                else:
                    abs_url = base_url + stripped
                proxy_url = f"{server_base}api/proxy?url={urllib.parse.quote(abs_url, safe='')}&referer={urllib.parse.quote(referer, safe='')}"
                rewritten.append(proxy_url)
            else:
                rewritten.append(line)

        from fastapi.responses import Response
        return Response(
            content="\n".join(rewritten),
            media_type="application/vnd.apple.mpegurl",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "no-cache",
            },
        )

    # For binary media segments – stream through
    from fastapi.responses import StreamingResponse

    def _stream():
        for chunk in resp.iter_content(chunk_size=65536):
            yield chunk

    return StreamingResponse(
        _stream(),
        media_type=content_type,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "no-cache",
        },
    )



@app.get("/api/version")
def api_version(request: Request, platform: str = "tv"):
    base_url = str(request.base_url)
    apk_filename = "tv.apk" if platform == "tv" else "mobile.apk"
    return {
        "version_code": 2,
        "version_name": "1.1",
        "apk_url": f"{base_url}apks/{apk_filename}",
        "release_notes": "In-app self-update checker added."
    }

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
    request: Request,
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
    return [_stream_to_dict(s, request) for s in streams]


@app.get("/api/streams/{stream_id}")
def api_stream_detail(stream_id: int, request: Request, db: Session = Depends(get_db)):
    s = db.query(Stream).filter_by(id=stream_id).first()
    if not s:
        return JSONResponse(status_code=404, content={"detail": "Stream not found"})
    return _stream_to_dict(s, request)


@app.get("/api/streams/{stream_id}/refresh")
def api_stream_refresh(
    stream_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Re-extract HLS URL for a stream (called by TV app when token expires)."""
    s = db.query(Stream).filter_by(id=stream_id).first()
    if not s:
        return JSONResponse(status_code=404, content={"detail": "Stream not found"})
    if s.source_url:
        s.progress = 0
        db.commit()
        browser = getattr(request.app.state, "browser", None)
        background_tasks.add_task(_run_extraction, stream_id, s.source_url, s.fallback_url or "", browser)
    return _stream_to_dict(s, request)


def _needs_proxy(hls_url: str) -> bool:
    """Returns True if the HLS URL points to a raw IP (self-signed cert, needs proxy)."""
    import re
    if not hls_url:
        return False
    try:
        host = urllib.parse.urlparse(hls_url).hostname or ""
        return bool(re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', host))
    except Exception:
        return False


def _stream_to_dict(s: Stream, request: Request = None) -> dict:
    hls_url = s.hls_url or ""
    iframe_url = s.iframe_url or ""

    # Wrap IP-based HLS URLs through the local proxy to avoid SSL cert errors on TV
    if request and hls_url and _needs_proxy(hls_url):
        referer = urllib.parse.urlparse(iframe_url)
        ref_str = f"{referer.scheme}://{referer.netloc}/" if referer.netloc else "https://www.google.com/"
        proxy_url = (
            f"{request.base_url}api/proxy"
            f"?url={urllib.parse.quote(hls_url, safe='')}"
            f"&referer={urllib.parse.quote(ref_str, safe='')}"
        )
    else:
        proxy_url = hls_url

    return {
        "id":            s.id,
        "category_id":   s.category_id,
        "category_name": s.category.name if s.category else "",
        "category_icon": s.category.icon if s.category else "",
        "title":         s.title,
        "participants":  s.participants,
        "sport":         s.sport,
        "source_url":    s.source_url,
        "iframe_url":    iframe_url,
        "hls_url":       proxy_url,          # proxied URL for TV app
        "hls_url_raw":   hls_url,            # raw CDN URL (for reference)
        "cf_domain":     s.cf_domain,
        "thumbnail_url": s.thumbnail_url,
        "is_live":       s.is_live,
        "created_at":    s.created_at.isoformat() if s.created_at else "",
    }


from pydantic import BaseModel

class WatchTimeRequest(BaseModel):
    stream_id: int
    duration_seconds: int

@app.post("/api/analytics/watch_time")
def add_watch_time(data: WatchTimeRequest, db: Session = Depends(get_db)):
    """Record watch time from the mobile/TV app clients."""
    # Ensure stream exists
    stream = db.query(Stream).filter_by(id=data.stream_id).first()
    if stream and data.duration_seconds > 0:
        analytics = WatchAnalytics(
            stream_id=data.stream_id,
            duration_seconds=data.duration_seconds
        )
        db.add(analytics)
        db.commit()
        return {"status": "success", "recorded": data.duration_seconds}
    return JSONResponse(status_code=400, content={"detail": "Invalid stream or duration"})


@app.post("/admin/sources/toggle/{source_id}")
def toggle_source(
    source_id: int,
    request: Request,
    db: Session = Depends(get_db),
    authenticated: bool = Depends(get_current_admin),
):
    source = db.query(SourceConfig).filter_by(id=source_id).first()
    if source:
        source.is_active = not source.is_active
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)


@app.get("/api/health/sources")
async def health_check_sources(db: Session = Depends(get_db)):
    """Check connectivity to all sources and update SourceConfig table."""
    sources = db.query(SourceConfig).all()
    results = []
    
    async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
        for source in sources:
            url = f"https://{source.domain}"
            status = "Offline"
            try:
                resp = await client.head(url, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code < 500:
                    status = "Online"
            except Exception as e:
                logger.warning(f"Health check failed for {source.domain}: {e}")
                
            source.last_health_status = status
            source.last_checked_at = datetime.utcnow()
            results.append({"name": source.name, "domain": source.domain, "status": status})
            
    db.commit()
    return {"sources": results}


@app.get("/download/tv")
def download_tv_apk():
    """Download the updated Android TV app APK directly."""
    from fastapi.responses import FileResponse
    import os
    apk_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "apks", "tv.apk")
    if not os.path.exists(apk_path):
        raise HTTPException(status_code=404, detail="TV APK not found. Please compile and upload it.")
    return FileResponse(
        path=apk_path,
        media_type="application/vnd.android.package-archive",
        filename="SportsTv_Leanback.apk"
    )


@app.get("/download/mobile")
def download_mobile_apk():
    """Download the updated Android Mobile app APK directly."""
    from fastapi.responses import FileResponse
    import os
    apk_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "apks", "mobile.apk")
    if not os.path.exists(apk_path):
        raise HTTPException(status_code=404, detail="Mobile APK not found. Please compile and upload it.")
    return FileResponse(
        path=apk_path,
        media_type="application/vnd.android.package-archive",
        filename="SportsTv_Mobile.apk"
    )


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

"""
extractor.py  –  Playwright-based extraction of HLS links from jokertvguide.sx pages.

Reuses the proven technique:
  1. Open partner URL in headless Chromium (bypasses Cloudflare JS challenge).
  2. Parse __NEXT_DATA__ JSON for match metadata + iframe URL.
  3. Fetch the iframe URL with a spoofed Referer header to get the .m3u8 link.
"""
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import json
import re
from typing import Any, Dict, Optional

import requests
from bs4 import BeautifulSoup

REFERER    = "https://partner.nonamejose.sx/"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


# ---------------------------------------------------------------------------
# Step 1  –  headless browser fetch (Cloudflare bypass)
# ---------------------------------------------------------------------------
def _fetch_with_browser(url: str) -> str:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent=USER_AGENT,
            extra_http_headers={"Referer": REFERER},
        )
        page = ctx.new_page()
        # Block the anti-devtool script
        page.route(
            "**cdn.jsdelivr.net/npm/disable-devtool**",
            lambda route, _: route.abort(),
        )
        try:
            page.goto(url, wait_until="networkidle", timeout=30_000)
        except PWTimeout:
            page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        html = page.content()
        browser.close()
    return html


# ---------------------------------------------------------------------------
# Step 2  –  parse __NEXT_DATA__ for metadata + iframe URL
# ---------------------------------------------------------------------------
def _parse_next_data(html: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {}

    m = re.search(r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*>(.+?)</script>', html, re.S)
    if not m:
        return result
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return result

    props = data.get("props", {}).get("pageProps", {})
    if "match" in props or "stream" in props:
        page_data = props
    else:
        page_data = props.get("data", props)   # some builds nest under "data"

    # --- title ---
    match_obj = page_data.get("match", {}) or {}
    result["title"] = (
        match_obj.get("title") or
        match_obj.get("event_title") or
        page_data.get("title") or ""
    )

    # --- sport ---
    sport_obj = match_obj.get("sport", {}) or {}
    result["sport"] = sport_obj.get("name") or page_data.get("sport", {}).get("name", "")

    # --- participants ---
    home_obj = match_obj.get("participantHome", {}) or {}
    away_obj = match_obj.get("participantAway", {}) or {}
    home = home_obj.get("name", "")
    away = away_obj.get("name", "")
    if home and away:
        result["participants"] = f"{home} vs {away}"

    # --- thumbnail ---
    og_img = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
    if og_img:
        result["thumbnail_url"] = og_img.group(1)

    # --- iframe / stream URL ---
    stream_val = page_data.get("stream", "")
    if stream_val:
        if stream_val.lower().startswith("<iframe"):
            src_m = re.search(r'src=["\']([^"\']+)["\']', stream_val, re.I)
            if src_m:
                stream_val = src_m.group(1)
        if stream_val.startswith("http") or stream_val.startswith("//"):
            result["iframe_url"] = stream_val

    return result


# ---------------------------------------------------------------------------
# Step 3  –  fetch iframe page for .m3u8 using Playwright (JS-rendered player)
# ---------------------------------------------------------------------------
def _fetch_hls(iframe_url: str) -> str:
    """
    Many embed pages build the video player entirely in JavaScript, so a plain
    HTTP GET never sees the m3u8 URL.  We use Playwright to:
      a) intercept every network request and grab any .m3u8 URL, OR
      b) fall back to scanning the fully-rendered page source.
    """
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    captured: list = []

    def _on_request(request):
        url = request.url
        if ".m3u8" in url:
            captured.append(url)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent=USER_AGENT,
            extra_http_headers={"Referer": REFERER},
        )
        page = ctx.new_page()
        page.on("request", _on_request)
        try:
            page.goto(iframe_url, wait_until="networkidle", timeout=25_000)
        except PWTimeout:
            pass  # networkidle timed out but JS may have already fired requests
        # Give JS player a moment to initialise and fire the m3u8 request
        page.wait_for_timeout(4000)
        html = page.content()
        browser.close()

    # Best: intercepted a live network request for the m3u8
    if captured:
        return captured[0]

    # Fallback: scan the rendered HTML for any m3u8 reference
    m = re.search(r'file\s*[:=]\s*["\'](?P<url>https?://[^"\']+\.m3u8[^"\']*)["\']', html)
    if m:
        return m.group("url")
    m2 = re.search(r'(?P<url>https?://[^"\'>\s]+\.m3u8[^"\'>\s]*)', html)
    if m2:
        return m2.group("url")

    return ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def extract(url: str) -> Dict[str, Any]:
    """
    Full extraction pipeline for a single jokertvguide.sx / partner URL.

    Returns a dict with:
        title, sport, participants, thumbnail_url,
        source_url, iframe_url, hls_url

    If the stream page is dead/expired (no iframe found), the title will be
    prefixed with [ERROR] so the admin dashboard shows an error badge.
    """
    result: Dict[str, Any] = {"source_url": url, "iframe_url": "", "hls_url": ""}

    # 1. Get page via browser
    html = _fetch_with_browser(url)

    # 2. Parse metadata
    meta = _parse_next_data(html)
    result.update(meta)

    # Fallback title from <title> tag
    if not result.get("title"):
        soup = BeautifulSoup(html, "html.parser")
        if soup.title:
            result["title"] = soup.title.string.strip() if soup.title.string else ""

    # 3. If no iframe_url found, this stream page is dead/expired
    iframe_url = result.get("iframe_url", "")
    if not iframe_url:
        # Try to find any iframe in the raw HTML as a last resort
        m = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', html, re.I)
        if m:
            iframe_url = m.group(1)
            result["iframe_url"] = iframe_url

    if not iframe_url:
        current_title = result.get("title", "")
        if current_title and not current_title.startswith("[ERROR]"):
            result["title"] = f"[ERROR] Stream expired/offline – {current_title}"
        else:
            result["title"] = "[ERROR] Stream page returned no embed – link may be dead"
        result["hls_url"] = ""
        return result

    # 4. Get HLS link from the iframe
    try:
        result["hls_url"] = _fetch_hls(iframe_url)
        if not result["hls_url"]:
            # Iframe loaded but no m3u8 found inside
            current_title = result.get("title", "")
            if not current_title.startswith("[ERROR]"):
                result["title"] = f"[ERROR] No HLS link found in embed – {current_title}"
    except Exception as e:
        result["hls_url"] = ""
        current_title = result.get("title", "")
        if not current_title.startswith("[ERROR]"):
            result["title"] = f"[ERROR] {e} – {current_title}"
        result["extract_error"] = str(e)

    return result

"""
extract_via_browser.py
----------------------
Extracts HLS stream links from partner.nonamejose.sx (JokerTVGuide partner) pages
by navigating Chrome (which has a real session that bypasses Cloudflare) and 
capturing network requests for .m3u8 files.

Usage:
    python extract_via_browser.py <partner_url> [--add-to-db] [--title "Match Title"] [--category-id 1]

Example:
    python extract_via_browser.py https://partner.nonamejose.sx/88abfb11/36ff7822/4a86def3
    python extract_via_browser.py https://partner.nonamejose.sx/88abfb11/36ff7822/4a86def3 --add-to-db --title "Portugal vs Uzbekistan"
"""

import asyncio
import sys
import argparse
import sqlite3
import datetime
import os

async def extract_hls_from_partner(url: str, wait_seconds: int = 8) -> dict:
    """
    Open the partner URL in a visible Chrome browser and capture HLS network requests.
    Returns dict with keys: hls_url, iframe_url, title, source_url
    """
    from playwright.async_api import async_playwright
    
    captured = {"hls_urls": [], "iframe_url": "", "title": "", "source_url": url}
    
    async with async_playwright() as p:
        # Launch a VISIBLE browser (not headless) to bypass Cloudflare/Turnstile
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        # Hide webdriver flag
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        # Stub ConsoleBan before it executes
        await context.add_init_script("""
            window.ConsoleBan = { init: function() {} };
            window.DisableDevtool = function() {};
            window.DisableDevtool.launch = function() {};
        """)
        
        page = await context.new_page()
        
        # Capture all network requests for .m3u8
        def on_request(request):
            u = request.url
            if ".m3u8" in u and u not in captured["hls_urls"]:
                captured["hls_urls"].append(u)
                print(f"\n✅ HLS CAPTURED: {u}\n")
        
        page.on("request", on_request)
        
        print(f"🌐 Opening: {url}")
        print("⏳ Waiting for page and stream to load...")
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        except Exception as e:
            print(f"Navigation warning: {e}")
        
        # Try to get title from NEXT_DATA
        try:
            title_js = await page.evaluate("""
                () => {
                    try {
                        const d = JSON.parse(document.getElementById('__NEXT_DATA__').textContent);
                        const m = d.props?.pageProps?.match;
                        return m?.event_title || m?.title || document.title;
                    } catch(e) { return document.title; }
                }
            """)
            captured["title"] = title_js
        except:
            pass
        
        # Try to get iframe URL from NEXT_DATA
        try:
            iframe_js = await page.evaluate("""
                () => {
                    try {
                        const d = JSON.parse(document.getElementById('__NEXT_DATA__').textContent);
                        const stream = d.props?.pageProps?.stream || d.props?.pageProps?.data?.stream || '';
                        const match = stream.match(/src=["']([^"']+)["']/);
                        return match ? match[1] : '';
                    } catch(e) { return ''; }
                }
            """)
            captured["iframe_url"] = iframe_js
        except:
            pass
        
        # Wait for HLS requests to arrive
        for i in range(wait_seconds):
            await asyncio.sleep(1)
            if captured["hls_urls"]:
                print(f"  Found {len(captured['hls_urls'])} HLS link(s) after {i+1}s")
                break
            if i % 3 == 0:
                print(f"  Waiting... {wait_seconds - i}s remaining")
        
        await browser.close()
    
    return captured


def add_to_database(db_path: str, data: dict, title: str, category_id: int) -> int:
    """Insert stream into sports_tv.db backend database"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # If category_id not provided, find Soccer/Football
    if not category_id:
        c.execute("SELECT id FROM categories WHERE name LIKE ?", ("%Soccer%",))
        cat = c.fetchone()
        if not cat:
            c.execute("SELECT id FROM categories WHERE name LIKE ?", ("%Football%",))
            cat = c.fetchone()
        category_id = cat[0] if cat else 1
    
    hls_url = data["hls_urls"][0] if data["hls_urls"] else ""
    iframe_url = data.get("iframe_url", "")
    source_url = data.get("source_url", "")
    match_title = title or data.get("title", "Unknown Match")
    
    c.execute(
        """INSERT INTO streams (category_id, title, participants, sport, source_url, iframe_url, hls_url, is_live, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (category_id, match_title, match_title, "Soccer",
         source_url, iframe_url, hls_url, 1,
         datetime.datetime.now().isoformat())
    )
    conn.commit()
    stream_id = c.lastrowid
    conn.close()
    return stream_id


async def main():
    parser = argparse.ArgumentParser(description="Extract HLS stream from partner URL")
    parser.add_argument("url", help="Partner URL (e.g. https://partner.nonamejose.sx/...)")
    parser.add_argument("--add-to-db", action="store_true", help="Add found stream to the backend database")
    parser.add_argument("--title", default="", help="Match title for the database entry")
    parser.add_argument("--category-id", type=int, default=0, help="Category ID in the database")
    parser.add_argument("--wait", type=int, default=10, help="Seconds to wait for stream (default: 10)")
    parser.add_argument("--db", default="sports_tv.db", help="Path to the SQLite database")
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎬 Sports TV HLS Stream Extractor (Browser Method)")
    print("=" * 60)
    
    result = await extract_hls_from_partner(args.url, wait_seconds=args.wait)
    
    print("\n" + "=" * 60)
    print("📋 EXTRACTION RESULTS")
    print("=" * 60)
    print(f"  Source URL:  {result['source_url']}")
    print(f"  Title:       {result['title']}")
    print(f"  Iframe URL:  {result['iframe_url']}")
    
    if result["hls_urls"]:
        print(f"\n  ✅ HLS Links Found ({len(result['hls_urls'])}):")
        for i, url in enumerate(result["hls_urls"], 1):
            print(f"    {i}. {url}")
        
        if args.add_to_db:
            db_path = args.db
            if not os.path.isabs(db_path):
                db_path = os.path.join(os.path.dirname(__file__), db_path)
            stream_id = add_to_database(db_path, result, args.title, args.category_id)
            print(f"\n  ✅ Added to database as stream id={stream_id}")
    else:
        print("\n  ❌ No HLS links found. Possible reasons:")
        print("     - Cloudflare challenge was not passed (check if browser opened)")
        print("     - Stream is offline or expired")
        print("     - Video was not played (try clicking play in the browser window)")
    
    print("=" * 60)
    return result


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())

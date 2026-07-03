"""
extract_hls.py — Capture HLS stream from partner.nonamejose.sx
--------------------------------------------------------------
Uses a local mitmproxy-style approach with a real visible Chrome.
No DevTools attached (avoids disable-devtool detection).

Usage:
    python backend/extract_hls.py "https://partner.nonamejose.sx/88abfb11/36ff7822/4a86def3"
    python backend/extract_hls.py "https://partner.nonamejose.sx/88abfb11/36ff7822/4a86def3" --add-to-db --title "Portugal vs Uzbekistan"
"""

import asyncio
import sys
import argparse
import sqlite3
import datetime
import os
import json


async def extract_hls(url: str, wait_seconds: int = 15) -> dict:
    """
    Use a CDP-connected browser with devtools turned off at the page level.
    We intercept requests via a separate chrome instance with --headless=new
    but using a persistent profile that has existing cookies.
    """
    from playwright.async_api import async_playwright

    captured = {"hls_urls": [], "iframe_url": "", "title": "", "source_url": url}

    async with async_playwright() as p:
        # Use a persistent context to inherit cookies from user's Chrome profile
        # This is what lets it pass Cloudflare -- it sees a returning browser with history
        user_data = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Google", "Chrome", "User Data")
        
        # Try to use the real Chrome user data if it exists, otherwise use default
        if os.path.isdir(user_data):
            context = await p.chromium.launch_persistent_context(
                user_data_dir=user_data + "_playwright_copy",
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-first-run",
                    "--no-default-browser-check",
                    # KEY: don't expose DevTools to the page
                    "--disable-extensions",
                ],
                ignore_default_args=["--enable-automation"],
                channel="chrome",  # Use real Chrome, not Chromium
            )
            page = context.pages[0] if context.pages else await context.new_page()
        else:
            # Fallback: regular launch
            browser = await p.chromium.launch(
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
                ignore_default_args=["--enable-automation"],
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

        # Inject stubs BEFORE any page script runs
        await context.add_init_script("""
            // Prevent disable-devtool from detecting automation
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            // Prevent ConsoleBan redirect
            window.ConsoleBan = { init: function() {} };
        """)

        # Capture .m3u8 requests
        def on_request(request):
            u = request.url
            if ".m3u8" in u and u not in captured["hls_urls"]:
                captured["hls_urls"].append(u)
                print(f"\n[FOUND] HLS URL: {u}\n")

        page.on("request", on_request)

        print(f"[*] Opening: {url}")
        print("[*] Chrome window opened. If you see a security check, please pass it.")
        print(f"[*] Waiting up to {wait_seconds}s for stream to load...")

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        except Exception as e:
            print(f"[!] Navigation warning: {e}")

        # Extract title from NEXT_DATA
        try:
            title_js = await page.evaluate("""() => {
                try {
                    const d = JSON.parse(document.getElementById('__NEXT_DATA__').textContent);
                    const m = d.props?.pageProps?.match;
                    return m?.event_title || m?.title || document.title;
                } catch(e) { return document.title; }
            }""")
            captured["title"] = title_js
        except:
            captured["title"] = ""

        # Extract iframe URL from NEXT_DATA
        try:
            iframe_js = await page.evaluate("""() => {
                try {
                    const d = JSON.parse(document.getElementById('__NEXT_DATA__').textContent);
                    const stream = d.props?.pageProps?.stream
                                || d.props?.pageProps?.data?.stream || '';
                    const m = stream.match(/src=["']([^"']+)["']/);
                    return m ? m[1] : '';
                } catch(e) { return ''; }
            }""")
            captured["iframe_url"] = iframe_js
            if iframe_js:
                print(f"[*] Iframe URL: {iframe_js}")
        except:
            pass

        # Wait for .m3u8 requests
        for i in range(wait_seconds):
            await asyncio.sleep(1)
            if captured["hls_urls"]:
                print(f"[+] Got HLS after {i+1}s")
                break
            if (i + 1) % 5 == 0:
                print(f"[*] Still waiting... {wait_seconds - i - 1}s left")

        await context.close()

    return captured


def add_to_db(db_path: str, data: dict, title: str, category_id: int) -> int:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    if not category_id:
        c.execute("SELECT id FROM categories WHERE name LIKE ?", ("%Soccer%",))
        cat = c.fetchone()
        if not cat:
            c.execute("SELECT id FROM categories WHERE name LIKE ?", ("%Football%",))
            cat = c.fetchone()
        category_id = cat[0] if cat else 1

    hls = data["hls_urls"][0] if data["hls_urls"] else ""
    match_title = title or data.get("title", "Unknown Match")

    c.execute(
        """INSERT INTO streams
           (category_id, title, participants, sport, source_url, iframe_url, hls_url, is_live, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (category_id, match_title, match_title, "Soccer",
         data["source_url"], data.get("iframe_url", ""), hls, 1,
         datetime.datetime.now().isoformat())
    )
    conn.commit()
    sid = c.lastrowid
    conn.close()
    return sid


async def main():
    parser = argparse.ArgumentParser(description="Extract HLS stream from JokerTVGuide partner URL")
    parser.add_argument("url", help="Partner URL")
    parser.add_argument("--add-to-db", action="store_true")
    parser.add_argument("--title", default="")
    parser.add_argument("--category-id", type=int, default=0)
    parser.add_argument("--wait", type=int, default=15)
    parser.add_argument("--db", default="sports_tv.db")
    args = parser.parse_args()

    print("=" * 60)
    print("Sports TV HLS Stream Extractor")
    print("=" * 60)

    result = await extract_hls(args.url, wait_seconds=args.wait)

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"  Title:      {result['title']}")
    print(f"  Iframe URL: {result['iframe_url']}")
    print(f"  Source:     {result['source_url']}")

    if result["hls_urls"]:
        print(f"\n  [OK] {len(result['hls_urls'])} HLS link(s) found:")
        for i, u in enumerate(result["hls_urls"], 1):
            print(f"    {i}. {u}")

        if args.add_to_db:
            db_path = args.db
            if not os.path.isabs(db_path):
                db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_path)
            sid = add_to_db(db_path, result, args.title, args.category_id)
            print(f"\n  [DB] Saved as stream id={sid}")
    else:
        print("\n  [FAIL] No HLS links found.")
        print("  Reasons:")
        print("   - Cloudflare challenge shown but not passed")
        print("   - Stream is offline/expired")
        print("   - Try increasing --wait seconds")

    print("=" * 60)
    return result


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())

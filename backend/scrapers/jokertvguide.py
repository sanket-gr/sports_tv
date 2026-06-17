import re
import json
import logging
import asyncio
from bs4 import BeautifulSoup
from typing import Any, Dict, List, Union
from .base import BaseScraper

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
REFERER = "https://partner.nonamejose.sx/"

class JokerTvGuideScraper(BaseScraper):
    async def _fetch_with_browser(self, url: str, browser: Any) -> str:
        from playwright.async_api import TimeoutError as PWTimeout

        ctx = await browser.new_context(
            user_agent=USER_AGENT,
            extra_http_headers={"Referer": REFERER},
        )
        page = await ctx.new_page()
        await page.route(
            "**cdn.jsdelivr.net/npm/disable-devtool**",
            lambda route, _: asyncio.create_task(route.abort()),
        )
        try:
            await page.goto(url, wait_until="networkidle", timeout=30_000)
        except PWTimeout:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        html = await page.content()
        await ctx.close()
        return html

    def _parse_next_data(self, html: str) -> Dict[str, Any]:
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
            page_data = props.get("data", props)

        match_obj = page_data.get("match", {}) or {}
        result["title"] = (
            match_obj.get("title") or
            match_obj.get("event_title") or
            page_data.get("title") or ""
        )

        sport_obj = match_obj.get("sport", {}) or {}
        result["sport"] = sport_obj.get("name") or page_data.get("sport", {}).get("name", "")

        home_obj = match_obj.get("participantHome", {}) or {}
        away_obj = match_obj.get("participantAway", {}) or {}
        home = home_obj.get("name", "")
        away = away_obj.get("name", "")
        if home and away:
            result["participants"] = f"{home} vs {away}"

        og_img = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        if og_img:
            result["thumbnail_url"] = og_img.group(1)

        stream_val = page_data.get("stream", "")
        if stream_val:
            if stream_val.lower().startswith("<iframe"):
                src_m = re.search(r'src=["\']([^"\']+)["\']', stream_val, re.I)
                if src_m:
                    stream_val = src_m.group(1)
            if stream_val.startswith("http") or stream_val.startswith("//"):
                result["iframe_url"] = stream_val

        return result

    async def _fetch_hls(self, iframe_url: str, browser: Any) -> str:
        from playwright.async_api import TimeoutError as PWTimeout

        captured: list = []

        async def _on_request(request):
            url = request.url
            if ".m3u8" in url:
                captured.append(url)

        ctx = await browser.new_context(
            user_agent=USER_AGENT,
            extra_http_headers={"Referer": REFERER},
        )
        page = await ctx.new_page()
        page.on("request", _on_request)
        try:
            await page.goto(iframe_url, wait_until="networkidle", timeout=25_000)
        except PWTimeout:
            pass
        await page.wait_for_timeout(4000)
        html = await page.content()
        await ctx.close()

        if captured:
            return captured[0]

        m = re.search(r'file\s*[:=]\s*["\'](?P<url>https?://[^"\']+\.m3u8[^"\']*)["\']', html)
        if m:
            return m.group("url")
        m2 = re.search(r'(?P<url>https?://[^"\'>\s]+\.m3u8[^"\'>\s]*)', html)
        if m2:
            return m2.group("url")

        return ""

    async def extract(self, url: str, browser: Any = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        import asyncio
        from playwright.async_api import async_playwright
        
        local_playwright = None
        current_browser = browser
        
        if not current_browser:
            local_playwright = await async_playwright().start()
            current_browser = await local_playwright.chromium.launch(headless=True)
            
        try:
            result: Dict[str, Any] = {"source_url": url, "iframe_url": "", "hls_url": ""}

            html = await self._fetch_with_browser(url, current_browser)
            meta = self._parse_next_data(html)
            result.update(meta)

            if not result.get("title"):
                soup = BeautifulSoup(html, "html.parser")
                if soup.title:
                    result["title"] = soup.title.string.strip() if soup.title.string else ""

            iframe_url = result.get("iframe_url", "")
            if not iframe_url:
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

            try:
                result["hls_url"] = await self._fetch_hls(iframe_url, current_browser)
                if not result["hls_url"]:
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
        finally:
            if local_playwright:
                await current_browser.close()
                await local_playwright.stop()

import re
import json
import logging
import asyncio
from bs4 import BeautifulSoup
from typing import Any, Dict, List, Optional, Tuple, Union
from .base import BaseScraper
from .flaresolverr_client import playwright_cookies, try_get_cf_clearance

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
REFERER = "https://partner.nonamejose.sx/"

class JokerTvGuideScraper(BaseScraper):
    async def _get_cf_cookies(
        self, url: str
    ) -> Tuple[Optional[List[dict]], Optional[str], Optional[str]]:
        """
        Try to get Cloudflare clearance cookies from FlareSolverr.
        Returns (pw_cookies, user_agent, pre_fetched_html) or (None, None, None).
        """
        result = await try_get_cf_clearance(url)
        if result is None:
            return None, None, None
        raw_cookies, user_agent, html = result
        pw_cookies = playwright_cookies(raw_cookies)
        logger.info(
            f"[JokerTvGuide] FlareSolverr gave {len(pw_cookies)} cookie(s) for {url}"
        )
        return pw_cookies, user_agent or USER_AGENT, html

    async def _fetch_with_browser(
        self,
        url: str,
        browser: Any,
        cf_cookies: Optional[List[dict]] = None,
        cf_ua: Optional[str] = None,
    ) -> str:
        from playwright.async_api import TimeoutError as PWTimeout
        from .base import create_stealth_context

        effective_ua = cf_ua or USER_AGENT
        ctx = await create_stealth_context(browser, effective_ua, REFERER)

        # Pre-seed Cloudflare clearance cookies so the challenge is skipped
        if cf_cookies:
            try:
                await ctx.add_cookies(cf_cookies)
                logger.debug(f"[JokerTvGuide] Injected {len(cf_cookies)} CF cookie(s)")
            except Exception as e:
                logger.warning(f"[JokerTvGuide] Failed to inject CF cookies: {e}")

        page = await ctx.new_page()

        # Block bot-detection scripts before they load
        async def _block_route(route, request):
            await route.abort()
        await page.route("**/cdn.jsdelivr.net/npm/disable-devtool**", _block_route)
        await page.route("**/whos.amung.us/**", _block_route)
        await page.route("**consoleban**", _block_route)

        try:
            await page.goto(url, wait_until="networkidle", timeout=30_000)
        except PWTimeout:
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            except Exception:
                pass

        # Wait up to 15 seconds for __NEXT_DATA__ to appear (Cloudflare resolved)
        try:
            await page.wait_for_selector("script#__NEXT_DATA__", timeout=15_000)
        except Exception:
            pass

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

    async def _fetch_hls(
        self,
        iframe_url: str,
        browser: Any,
        cf_cookies: Optional[List[dict]] = None,
        cf_ua: Optional[str] = None,
    ) -> str:
        from playwright.async_api import TimeoutError as PWTimeout
        from .base import create_stealth_context

        captured: list = []

        async def _on_request(request):
            url = request.url
            if ".m3u8" in url:
                captured.append(url)

        effective_ua = cf_ua or USER_AGENT
        ctx = await create_stealth_context(browser, effective_ua, REFERER)

        # Re-use the same CF cookies in the embed player context
        if cf_cookies:
            try:
                await ctx.add_cookies(cf_cookies)
            except Exception as e:
                logger.warning(f"[JokerTvGuide] _fetch_hls cookie inject failed: {e}")

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
        m2 = re.search(r'(?P<url>https?://[^"\'<>\s]+\.m3u8[^"\'<>\s]*)', html)
        if m2:
            return m2.group("url")

        return ""

    async def extract(self, url: str, browser: Any = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        import asyncio
        from playwright.async_api import async_playwright

        local_playwright = None
        current_browser = browser

        if not current_browser:
            import os
            from .base import parse_playwright_proxy
            local_playwright = await async_playwright().start()
            launch_kwargs = {"headless": True}
            scraper_proxy = os.environ.get("SCRAPER_PROXY")
            if scraper_proxy:
                launch_kwargs["proxy"] = parse_playwright_proxy(scraper_proxy)
            current_browser = await local_playwright.chromium.launch(**launch_kwargs)

        try:
            result: Dict[str, Any] = {"source_url": url, "iframe_url": "", "hls_url": ""}

            # ── Step 1: Try FlareSolverr to get Cloudflare clearance cookies ──
            cf_cookies, cf_ua, pre_html = await self._get_cf_cookies(url)

            # ── Step 2: Fetch the stream page (cookies pre-seeded if available) ──
            # If FlareSolverr already returned the HTML, we can use it directly
            # and skip an extra Playwright navigation when __NEXT_DATA__ is present.
            if pre_html and "__NEXT_DATA__" in pre_html:
                logger.info("[JokerTvGuide] Using FlareSolverr pre-fetched HTML")
                html = pre_html
            else:
                html = await self._fetch_with_browser(
                    url, current_browser, cf_cookies=cf_cookies, cf_ua=cf_ua
                )

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

            # ── Step 3: Fetch HLS from the embed player (reuse CF cookies) ──
            try:
                result["hls_url"] = await self._fetch_hls(
                    iframe_url, current_browser, cf_cookies=cf_cookies, cf_ua=cf_ua
                )
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

import re
import logging
import asyncio
from bs4 import BeautifulSoup
from typing import Any, Dict, List, Union
from .base import BaseScraper, create_stealth_context, parse_playwright_proxy

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

class EmbedStScraper(BaseScraper):
    async def extract(self, url: str, browser: Any = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        import asyncio
        from playwright.async_api import async_playwright, TimeoutError as PWTimeout
        
        local_playwright = None
        current_browser = browser
        
        if not current_browser:
            import os
            local_playwright = await async_playwright().start()
            launch_kwargs = {"headless": True}
            scraper_proxy = os.environ.get("SCRAPER_PROXY")
            if scraper_proxy:
                launch_kwargs["proxy"] = parse_playwright_proxy(scraper_proxy)
            current_browser = await local_playwright.chromium.launch(**launch_kwargs)
            
        try:
            result = {"source_url": url, "iframe_url": url, "hls_url": ""}
            
            # Intercept network requests
            captured = []
            async def _on_request(request):
                req_url = request.url
                if ".m3u8" in req_url:
                    captured.append(req_url)
            
            ctx = await create_stealth_context(current_browser, USER_AGENT)
            page = await ctx.new_page()
            page.on("request", _on_request)
            
            try:
                # Load page
                await page.goto(url, wait_until="domcontentloaded", timeout=25000)
                await page.wait_for_timeout(3000)
                
                # Fetch page title
                title = await page.title()
                if title:
                    result["title"] = title.strip()
                
                # Attempt to click play to trigger stream load
                try:
                    # Look for button or click center of page
                    await page.click("button", timeout=5000)
                except Exception:
                    # Fallback to clicking center of viewport
                    viewport = page.viewport_size or {"width": 1280, "height": 720}
                    await page.mouse.click(viewport["width"] / 2, viewport["height"] / 2)
                
                # Wait for the HLS stream request to populate
                await page.wait_for_timeout(5000)
                
                if captured:
                    result["hls_url"] = captured[0]
                    # Parse CDN domain for segment referer
                    try:
                        from urllib.parse import urlparse
                        result["cf_domain"] = urlparse(captured[0]).hostname or ""
                    except Exception:
                        pass
                
            except Exception as e:
                logger.error(f"Error extracting from embed.st: {e}")
                result["extract_error"] = str(e)
            finally:
                await ctx.close()
                
            if not result.get("hls_url"):
                result["title"] = f"[ERROR] No HLS stream found - {result.get('title', 'Embed.st Stream')}"
                
            return result
            
        finally:
            if local_playwright:
                await current_browser.close()
                await local_playwright.stop()

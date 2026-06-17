import logging
from bs4 import BeautifulSoup
from typing import Any, Dict, List, Union
from .base import BaseScraper
from .vidplayer import VidplayerScraper

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

class WatchMmaFullScraper(BaseScraper):
    async def extract(self, url: str, browser: Any = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        import asyncio
        from playwright.async_api import async_playwright
        
        html = ""
        local_playwright = None
        current_browser = browser
        
        if not current_browser:
            local_playwright = await async_playwright().start()
            current_browser = await local_playwright.chromium.launch(headless=True)
            
        ctx = await current_browser.new_context(user_agent=USER_AGENT)
        page = await ctx.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(8000)
            html = await page.content()
        except Exception as e:
            logger.error(f"Error loading watchmmafull page: {e}")
        finally:
            await ctx.close()
            if local_playwright:
                await current_browser.close()
                await local_playwright.stop()
                
        if not html:
            return {"source_url": url, "title": "[ERROR] Failed to load watchmmafull page", "hls_url": ""}
            
        soup = BeautifulSoup(html, "html.parser")
        title = ""
        h1 = soup.find("h1")
        if h1:
            title = h1.text.strip()
        else:
            title = soup.title.string.strip() if soup.title else "UFC Fight"
            
        grid = soup.find(class_="watch-link-grid")
        if not grid:
            return {"source_url": url, "title": f"[ERROR] No watch links grid found - {title}", "hls_url": ""}
            
        links = []
        for a in grid.find_all("a"):
            href = a.get("href")
            if not href:
                continue
            server_name = "Unknown Server"
            meta_span = a.find(class_="link-meta")
            if meta_span:
                span_name = meta_span.find("span")
                if span_name:
                    server_name = span_name.text.strip()
            links.append((server_name, href))
            
        if not links:
            return {"source_url": url, "title": f"[ERROR] No stream buttons found - {title}", "hls_url": ""}
            
        results = []
        vidplayer = VidplayerScraper()
        
        for name, href in links:
            decrypted = await vidplayer.extract(href, browser)
            if isinstance(decrypted, dict) and decrypted.get("hls_url"):
                results.append({
                    "source_url": url,
                    "title": f"{decrypted['title']} ({name})",
                    "sport": "UFC",
                    "iframe_url": href,
                    "hls_url": decrypted["hls_url"],
                    "cf_domain": decrypted.get("cf_domain", ""),
                })
                
        if not results:
            return {"source_url": url, "title": f"[ERROR] Failed to decrypt any video server - {title}", "hls_url": ""}
            
        return results if len(results) > 1 else results[0]

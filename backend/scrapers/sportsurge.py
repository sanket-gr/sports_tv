import re
import base64
import httpx
from bs4 import BeautifulSoup
from typing import Any, Dict, List, Union
from .base import BaseScraper

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

class SportsurgeScraper(BaseScraper):
    async def extract(self, url: str, browser: Any = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        from urllib.parse import urlparse, parse_qs
        
        parsed_url = urlparse(url)
        qs = parse_qs(parsed_url.query)
        target_server_id = qs.get("server_id", [None])[0]
        
        base_url = url.split("?")[0]
        result = {"source_url": url, "iframe_url": "", "hls_url": ""}
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, headers={"User-Agent": USER_AGENT})
                html = resp.text
                soup = BeautifulSoup(html, "html.parser")
                
                h1 = soup.find("h1")
                if h1:
                    result["title"] = h1.text.strip()
                    
                dt_league = soup.find("dt", string=re.compile("League", re.I))
                if dt_league:
                    dd_league = dt_league.find_next_sibling("dd")
                    if dd_league:
                        result["sport"] = dd_league.text.strip()
                        
                # Find all server buttons
                server_btns = soup.find_all("div", id=re.compile(r"^stream-btn-\d+"))
                
                if not target_server_id and len(server_btns) > 1:
                    # Main extraction with multiple servers: return a list of results
                    results = []
                    for btn in server_btns:
                        server_name = btn.text.strip()
                        m_id = re.search(r"stream-btn-(\d+)", btn["id"])
                        if m_id:
                            sid = m_id.group(1)
                            # Recursively extract this specific server
                            server_url = f"{base_url}?server_id={sid}"
                            server_result = await self.extract(server_url, browser)
                            if isinstance(server_result, dict):
                                server_result["title"] = f"{result.get('title', 'Event')} ({server_name})"
                                results.append(server_result)
                    if results:
                        return results

                # Single server extraction
                iframe_url = ""
                if target_server_id:
                    iframe_url = f"https://gooz.aapmains.net/new-stream-embed/{target_server_id}"
                else:
                    iframe = soup.find("iframe", id="cx-iframe")
                    if iframe and iframe.has_attr("src"):
                        iframe_url = iframe["src"]

                if iframe_url:
                    result["iframe_url"] = iframe_url
                    
                    if iframe_url.endswith("/new-stream-embed/"):
                        result["title"] = f"[NOT STARTED] {result.get('title', 'Event')}"
                        result["hls_url"] = ""
                    else:
                        iframe_resp = await client.get(iframe_url, headers={"User-Agent": USER_AGENT, "Referer": "https://sportsurge.ws/"})
                        m = re.search(r"window\.atob\(['\"]([^'\"]+)['\"]\)", iframe_resp.text)
                        if m:
                            result["hls_url"] = base64.b64decode(m.group(1)).decode('utf-8')
        except Exception as e:
            result["extract_error"] = str(e)
            if not result.get("title"):
                result["title"] = f"[ERROR] {e}"
                
        if not result["iframe_url"]:
            result["title"] = f"[ERROR] Stream expired or no iframe found"
        elif not result["hls_url"] and not result["title"].startswith("[NOT STARTED]"):
            result["title"] = f"[ERROR] Could not decode HLS URL from iframe"
            
        return result

import re
import base64
import logging
import httpx
from typing import Any, Dict, List, Union
from .base import BaseScraper

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

def decode_base64_url(s: str) -> str:
    s = s.replace('-', '+').replace('_', '/')
    while len(s) % 4 != 0:
        s += '='
    try:
        decoded_bytes = base64.b64decode(s)
        return decoded_bytes.decode('utf-8')
    except Exception:
        try:
            return decoded_bytes.decode('latin1')
        except Exception:
            return ""

class CdnLiveTvScraper(BaseScraper):
    async def extract(self, url: str, browser: Any = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        result = {"source_url": url, "iframe_url": "", "hls_url": ""}
        
        try:
            async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
                resp = await client.get(url, headers={"User-Agent": USER_AGENT})
                html = resp.text
                
                # Try to extract the title from HTML
                m_title = re.search(r"<title>([^<]+)</title>", html, re.I)
                if m_title:
                    result["title"] = m_title.group(1).strip()
                
                # Extract all variable assignments of the form var name='value';
                var_assignments = re.findall(r"var\s+(\w+)\s*=\s*['\"]([^'\"]+)['\"];", html)
                var_map = {name: val for name, val in var_assignments}
                
                # Look for the combination line (GtlpmtvgfT or similar decoding function)
                m_concat = re.search(r"var\s+\w+\s*=\s*([A-Za-z0-9_]+\(\w+\)\+\s*)+[A-Za-z0-9_]+\(\w+\);", html)
                if not m_concat:
                    # Generic search for any sequence of decoded concat vars
                    m_concat = re.search(r"var\s+\w+\s*=\s*([a-zA-Z0-9_]+\(\w+\)[+\s]*)+;", html)
                
                hls_url = ""
                if m_concat:
                    concat_expr = m_concat.group(0)
                    var_names = re.findall(r"[a-zA-Z0-9_]+\((\w+)\)", concat_expr)
                    decoded_parts = []
                    for name in var_names:
                        if name in var_map:
                            decoded_parts.append(decode_base64_url(var_map[name]))
                    hls_url = "".join(decoded_parts)
                
                if hls_url and hls_url.startswith("http"):
                    result["hls_url"] = hls_url
                    result["iframe_url"] = url # Since it is self-contained
                else:
                    # Fallback check for raw un-obfuscated m3u8 in javascript/html
                    m_raw = re.search(r"['\"](https?://[^'\"]+\.m3u8[^'\"]*)['\"]", html)
                    if m_raw:
                        result["hls_url"] = m_raw.group(1)
                        result["iframe_url"] = url
        except Exception as e:
            result["extract_error"] = str(e)
            if not result.get("title"):
                result["title"] = f"[ERROR] {e}"
        
        if not result["hls_url"]:
            result["title"] = "[ERROR] Could not decode HLS URL from player page"
            
        return result

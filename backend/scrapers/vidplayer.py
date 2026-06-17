import asyncio
import json
import os
import logging
from typing import Any, Dict, List, Union
from .base import BaseScraper

logger = logging.getLogger(__name__)

class VidplayerScraper(BaseScraper):
    async def extract(self, url: str, browser: Any = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        js_path = os.path.join(current_dir, "bypass", "decrypt_player.js")
        
        try:
            process = await asyncio.create_subprocess_exec(
                "node", js_path, url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            if process.returncode != 0:
                raise Exception("Node script failed")
            output = stdout.decode().strip()
            if output:
                decrypted = json.loads(output)
                if decrypted and decrypted.get("source"):
                    title = decrypted.get("title", "UFC Stream")
                    if title.endswith(".mp4"):
                        title = title[:-4]
                    metric = decrypted.get("metric", {})
                    cf_domain = metric.get("cfDomain", "")
                    if not cf_domain:
                        cf_url = decrypted.get("cf", "")
                        if cf_url:
                            try:
                                from urllib.parse import urlparse as _up
                                cf_domain = _up(cf_url).hostname or ""
                            except Exception:
                                pass
                    return {
                        "source_url": url,
                        "title": title,
                        "sport": "UFC",
                        "iframe_url": url,
                        "hls_url": decrypted["source"],
                        "cf_domain": cf_domain,
                    }
        except Exception as e:
            logger.error(f"Decryption failed for {url}: {e}")
        
        return {"source_url": url, "title": "[ERROR] Decryption failed", "hls_url": ""}

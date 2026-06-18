from abc import ABC, abstractmethod
from typing import Any, Dict, Union, List

class BaseScraper(ABC):
    """
    Abstract base class for all stream scrapers.
    """
    
    @abstractmethod
    async def extract(self, url: str, browser: Any = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Extract stream metadata and HLS URL from the given source URL.
        Returns a dictionary or a list of dictionaries (if multiple servers exist).
        """
        pass

def parse_playwright_proxy(proxy_url: str) -> dict:
    if not proxy_url:
        return {}
    if not proxy_url.startswith("http://") and not proxy_url.startswith("https://") and not proxy_url.startswith("socks5://"):
        proxy_url = "http://" + proxy_url
    
    from urllib.parse import urlparse
    try:
        parsed = urlparse(proxy_url)
        server_str = f"{parsed.scheme}://{parsed.hostname}"
        if parsed.port:
            server_str += f":{parsed.port}"
        
        proxy_config = {"server": server_str}
        if parsed.username:
            proxy_config["username"] = parsed.username
        if parsed.password:
            proxy_config["password"] = parsed.password
        return proxy_config
    except Exception:
        return {"server": proxy_url}

async def create_stealth_context(browser: Any, user_agent: str, referer: str = None) -> Any:
    extra_headers = {}
    if referer:
        extra_headers["Referer"] = referer
    
    ctx = await browser.new_context(
        user_agent=user_agent,
        viewport={"width": 1280, "height": 720},
        device_scale_factor=1,
        is_mobile=False,
        has_touch=False,
        locale="en-US",
        timezone_id="America/New_York",
        extra_http_headers=extra_headers,
    )
    # Hide webdriver flag
    await ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return ctx

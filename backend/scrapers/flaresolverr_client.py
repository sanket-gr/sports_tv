"""
flaresolverr_client.py
----------------------
Thin wrapper around the FlareSolverr v1 API.

FlareSolverr is a free, open-source proxy server that uses an
undetected browser (Selenium + UC-Chrome) to solve Cloudflare
challenges, then hands back the page HTML, cookies, and User-Agent.

We use those cookies to pre-seed a Playwright browser context so the
subsequent navigation bypasses the Cloudflare challenge entirely.

Configuration
-------------
Set the FLARESOLVERR_URL environment variable to point at your
FlareSolverr instance (defaults to http://localhost:8191).

Docker (sidecar):
    docker run -d --name flaresolverr -p 8191:8191 \\
        ghcr.io/flaresolverr/flaresolverr:latest
"""

import os
import logging
from typing import Optional, Tuple, List

import httpx

logger = logging.getLogger(__name__)

# Default to localhost; override with env var in production
FLARESOLVERR_URL = os.environ.get("FLARESOLVERR_URL", "http://localhost:8191")
_DEFAULT_TIMEOUT = 90  # seconds — CF challenges can take 30-60s


class FlareSolverrError(Exception):
    """Raised when FlareSolverr returns a non-ok status."""


async def get_cf_clearance(
    url: str,
    timeout: int = _DEFAULT_TIMEOUT,
) -> Tuple[List[dict], str, str]:
    """
    Ask FlareSolverr to solve any Cloudflare challenge for *url*.

    Returns
    -------
    cookies : list[dict]
        Each dict has at minimum: name, value, domain, path, httpOnly, secure.
        Pass directly to Playwright's ``context.add_cookies()``.
    user_agent : str
        The User-Agent string FlareSolverr's browser used.
        Must be passed to Playwright's context so the cookie domain matches.
    html : str
        The full page HTML after the challenge was solved.
        Can be used to skip the first Playwright navigation entirely.

    Raises
    ------
    FlareSolverrError
        If FlareSolverr is reachable but returned a non-ok status.
    httpx.ConnectError / httpx.TimeoutException
        If FlareSolverr is not running or unreachable — caller should
        handle these and fall back to direct Playwright navigation.
    """
    endpoint = f"{FLARESOLVERR_URL.rstrip('/')}/v1"
    payload = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": timeout * 1000,  # FlareSolverr uses ms
    }

    logger.info(f"[FlareSolverr] Requesting CF clearance for: {url}")

    async with httpx.AsyncClient(timeout=timeout + 10) as client:
        resp = await client.post(endpoint, json=payload)
        resp.raise_for_status()
        data = resp.json()

    if data.get("status") != "ok":
        msg = data.get("message", "Unknown error")
        raise FlareSolverrError(f"FlareSolverr returned non-ok status: {msg}")

    solution = data["solution"]
    cookies: List[dict] = solution.get("cookies", [])
    user_agent: str = solution.get("userAgent", "")
    html: str = solution.get("response", "")

    logger.info(
        f"[FlareSolverr] Got {len(cookies)} cookie(s), "
        f"UA={user_agent[:60]}..."
    )
    return cookies, user_agent, html


def playwright_cookies(raw_cookies: List[dict], fallback_domain: str = "") -> List[dict]:
    """
    Convert FlareSolverr cookies to the format Playwright's
    ``browser_context.add_cookies()`` expects.

    Playwright requires: name, value, domain, path.
    Optional: httpOnly, secure, sameSite, expires.
    """
    out = []
    for c in raw_cookies:
        domain = c.get("domain", fallback_domain)
        # Playwright wants the domain without leading dot for exact match,
        # but with leading dot for sub-domain matching.
        # FlareSolverr already returns them correctly, so pass as-is.
        entry = {
            "name": c.get("name", ""),
            "value": c.get("value", ""),
            "domain": domain,
            "path": c.get("path", "/"),
        }
        if "httpOnly" in c:
            entry["httpOnly"] = bool(c["httpOnly"])
        if "secure" in c:
            entry["secure"] = bool(c["secure"])
        if "sameSite" in c and c["sameSite"] in ("Strict", "Lax", "None"):
            entry["sameSite"] = c["sameSite"]
        if "expirationDate" in c:
            entry["expires"] = float(c["expirationDate"])
        out.append(entry)
    return out


async def try_get_cf_clearance(
    url: str,
    timeout: int = _DEFAULT_TIMEOUT,
) -> Optional[Tuple[List[dict], str, str]]:
    """
    Best-effort wrapper: returns ``(cookies, user_agent, html)`` on success,
    or ``None`` if FlareSolverr is unavailable / not configured.

    This lets callers gracefully fall back to plain Playwright navigation
    when FlareSolverr is not running (e.g. local dev without Docker).
    """
    try:
        return await get_cf_clearance(url, timeout=timeout)
    except (httpx.ConnectError, httpx.ConnectTimeout):
        logger.warning(
            "[FlareSolverr] Not reachable at %s — falling back to direct Playwright",
            FLARESOLVERR_URL,
        )
        return None
    except httpx.TimeoutException:
        logger.warning("[FlareSolverr] Request timed out — falling back to direct Playwright")
        return None
    except FlareSolverrError as e:
        logger.warning(f"[FlareSolverr] {e} — falling back to direct Playwright")
        return None
    except Exception as e:
        logger.warning(f"[FlareSolverr] Unexpected error: {e} — falling back to direct Playwright")
        return None

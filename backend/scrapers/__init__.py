from typing import Any
from .base import parse_playwright_proxy
from .jokertvguide import JokerTvGuideScraper
from .sportsurge import SportsurgeScraper
from .watchmmafull import WatchMmaFullScraper
from .vidplayer import VidplayerScraper
from .embedst import EmbedStScraper
from .cdnlivetv import CdnLiveTvScraper

def extract(url: str) -> Any:
    pass # Keep for sync fallback if needed

async def extract_async(url: str, browser: Any = None) -> Any:
    """
    Full extraction pipeline routing to modular scrapers.
    Returns a dict with metadata, OR a list of dicts if multiple servers are found.
    """
    if "cdnlivetv.tv" in url:
        return await CdnLiveTvScraper().extract(url, browser)

    if "sportsurge.ws" in url:
        return await SportsurgeScraper().extract(url, browser)

    if "watchmmafull.com" in url:
        return await WatchMmaFullScraper().extract(url, browser)

    if "embed.st" in url:
        return await EmbedStScraper().extract(url, browser)

    # Direct player URLs
    if "#" in url and not any(d in url for d in ["sportsurge.ws", "jokertvguide.sx", "nonamejose.sx"]):
        return await VidplayerScraper().extract(url, browser)

    # Fallback to JokerTvGuide style (jokertvguide.sx, nonamejose.sx)
    return await JokerTvGuideScraper().extract(url, browser)

import asyncio
import sys
from scrapers.jokertvguide import JokerTvGuideScraper
from playwright.async_api import async_playwright

async def main():
    url = "https://partner.nonamejose.sx/712a74b1/9f0cfc35/887b9fdf"
    print(f"Testing URL: {url}")
    
    scraper = JokerTvGuideScraper()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            print("Running extraction...")
            result = await scraper.extract(url, browser)
            print("Result:")
            print(result)
        finally:
            await browser.close()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())

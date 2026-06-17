import time
from playwright.sync_api import sync_playwright

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False)
    page = browser.new_page(user_agent=USER_AGENT)
    page.goto("https://watchmmafull.com/ufc-freedom-250-ilia-topuria-vs-justin-gaethje-jun-14-2026.html")
    time.sleep(15)
    with open("mma_page_headful.html", "w", encoding="utf-8") as f:
        f.write(page.content())
    print("Page Title:", page.title())
    browser.close()

"""Measure landing card heights and capture the landing screenshot."""

from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent / "screenshots"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    page.goto("http://localhost:8511", wait_until="networkidle")
    page.wait_for_selector("text=Upload GL transaction detail", timeout=30000)
    page.wait_for_timeout(2500)

    up = page.locator(".st-key-upload_card").bounding_box()
    bn = page.locator(".st-key-benefits_card").bounding_box()
    print("upload_card:", up)
    print("benefits_card:", bn)

    page.screenshot(path=str(OUT / "1_landing.png"), full_page=True)
    print("landing captured")
    browser.close()

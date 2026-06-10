"""Drive the Streamlit app headlessly: screenshot landing, upload demo CSV,
screenshot Close Health Check tab."""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8511"
OUT = Path(__file__).parent / "screenshots"
OUT.mkdir(exist_ok=True)
DEMO = Path(__file__).parent.parent / "sample_data" / "gl_transactions_demo.csv"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_selector("text=Upload GL transaction detail", timeout=30000)
    page.wait_for_timeout(2500)  # let fonts/CSS settle
    page.screenshot(path=str(OUT / "1_landing.png"), full_page=True)
    print("landing captured")

    page.set_input_files('input[type="file"]', str(DEMO))
    page.wait_for_selector("text=Close Health Check", timeout=60000)
    page.wait_for_timeout(3000)
    page.screenshot(path=str(OUT / "2_loaded.png"), full_page=True)
    print("loaded state captured")

    page.get_by_role("tab", name="Close Health Check").click()
    page.wait_for_timeout(4000)
    page.screenshot(path=str(OUT / "3_close_health.png"), full_page=True)
    print("close health captured")

    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.wait_for_timeout(500)
    print("console errors:", errors if errors else "none")
    browser.close()

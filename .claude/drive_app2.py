"""Second verification pass: remaining tabs, close-health bottom, filters."""

from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8511"
OUT = Path(__file__).parent / "screenshots"
DEMO = Path(__file__).parent.parent / "sample_data" / "gl_transactions_demo.csv"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 1100})
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_selector("text=Upload GL transaction detail", timeout=30000)
    page.set_input_files('input[type="file"]', str(DEMO))
    page.wait_for_selector("text=Close Health Check", timeout=60000)
    page.wait_for_timeout(2500)

    page.get_by_role("tab", name="Profit & Loss", exact=True).click()
    page.wait_for_timeout(2500)
    page.screenshot(path=str(OUT / "4_pnl.png"))
    print("pnl captured")

    page.get_by_role("tab", name="Periodised P&L").click()
    page.wait_for_timeout(3000)
    page.screenshot(path=str(OUT / "5_periodised.png"))
    print("periodised captured")

    page.get_by_role("tab", name="Balance Sheet").click()
    page.wait_for_timeout(2500)
    page.screenshot(path=str(OUT / "6_balance_sheet.png"))
    print("balance sheet captured")

    page.get_by_role("tab", name="Close Health Check").click()
    page.wait_for_timeout(3000)
    page.keyboard.press("End")
    page.mouse.wheel(0, 20000)
    page.wait_for_timeout(1500)
    page.screenshot(path=str(OUT / "7_close_health_bottom.png"))
    print("close health bottom captured")

    # Apply a subsidiary filter, check badge + clear button
    page.locator('[data-testid="stSidebar"] [data-baseweb="select"]').first.click()
    page.wait_for_timeout(800)
    page.keyboard.press("Enter")  # select first option
    page.keyboard.press("Escape")
    page.wait_for_timeout(2500)
    page.screenshot(path=str(OUT / "8_filtered_sidebar.png"))
    print("filtered sidebar captured")

    browser.close()

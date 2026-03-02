"""
Standalone test for the Playwright automation (BrowserAutomator) only.
Does not start the Telegram bot or touch the database.

Usage:
    .venv/bin/python test_automation.py                  # headless, defaults below
    .venv/bin/python test_automation.py --show-browser   # opens a visible browser window
"""
import argparse
import asyncio
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# ── Configure test inputs here ─────────────────────────────────────────────────
EMAIL = "arpan.biswas@ushur.com"
DIETARY_PREFERENCE = "Non Veg"   # "Veg" or "Non Veg"
FORM_URL = "https://hr.ushur.me/api/rest/qrTrigger/I2x1bmNoYXR1c2h1cjoxNzc1Mzc1MDI3Nw=="
ACTION_DELAY = 500    # ms between actions
TIMEOUT = 15000       # ms for element waits / navigation
# ──────────────────────────────────────────────────────────────────────────────

# Inject env vars before importing the package so Settings() is satisfied.
# Telegram fields are stubs — BrowserAutomator never uses them.
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "stub")
os.environ.setdefault("TELEGRAM_CHAT_ID", "stub")
os.environ.setdefault("FORM_URL", FORM_URL)
os.environ.setdefault("ACTION_DELAY", str(ACTION_DELAY))
os.environ.setdefault("TIMEOUT", str(TIMEOUT))

from lunchbuddy.models import DietaryPreference
from lunchbuddy.processor import BrowserAutomator
from lunchbuddy.config import settings


async def run(headless: bool):
    preference = DietaryPreference(DIETARY_PREFERENCE)

    logging.info("── Test Configuration ───────────────────────────────")
    logging.info(f"  Email:      {EMAIL}")
    logging.info(f"  Preference: {preference.value}")
    logging.info(f"  Form URL:   {settings.form_url}")
    logging.info(f"  Headless:   {headless}")
    logging.info(f"  Timeout:    {settings.timeout} ms")
    logging.info(f"  Delay:      {settings.action_delay} ms")
    logging.info("─────────────────────────────────────────────────────")

    automator = BrowserAutomator()

    if not headless:
        from playwright.async_api import async_playwright

        async def _visible_start():
            automator.playwright = await async_playwright().start()
            automator.browser = await automator.playwright.chromium.launch(
                headless=False,
                slow_mo=settings.action_delay,
            )
            automator.context = await automator.browser.new_context()
            automator.context.set_default_navigation_timeout(settings.timeout)
            automator.context.set_default_timeout(settings.timeout)
            automator.page = await automator.context.new_page()

        automator.start = _visible_start

    success = await automator.fill_form(settings.form_url, EMAIL, preference)

    print()
    if success:
        print("PASS — Lunch registered successfully.")
    else:
        print("FAIL — Registration did not complete. Check logs above.")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test BrowserAutomator in isolation.")
    parser.add_argument(
        "--show-browser",
        action="store_true",
        help="Launch a visible browser window instead of running headless.",
    )
    args = parser.parse_args()
    asyncio.run(run(headless=not args.show_browser))

"""Persistent browser session manager — keeps cookies alive for days/weeks.

Instead of creating throwaway contexts from storage_state.json (which lose session cookies),
this uses launch_persistent_context() with a real Chrome user_data_dir. The browser profile
directory holds all cookies, localStorage, IndexedDB natively — just like a real Chrome install.

After each operation, we save storage_state back as a backup.
"""

import os
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright, BrowserContext


# Persistent profile directory — survives across all launches
PROFILE_DIR = str(Path.home() / ".twitter-mcp" / "chrome-profile")
STORAGE_BACKUP = str(Path.home() / ".twitter-mcp" / "storage_state.json")

# Anti-detection args
BROWSER_ARGS = [
    "--no-sandbox",
    "--disable-blink-features=AutomationControlled",
    "--disable-features=IsolateOrigins,site-per-process",
    "--disable-site-isolation-trials",
    "--disable-web-security",
    "--restore-last-session",  # CRITICAL: prevents Chromium from discarding session cookies on restart
]

IGNORE_ARGS = ["--enable-automation"]

# Twitter blocks headless browsers. Use Xvfb virtual display instead.
# Install: apt-get install -y xvfb
# Start: Xvfb :99 -screen 0 1280x720x24 & export DISPLAY=:99
USE_HEADLESS = False  # Set True only if Xvfb is NOT available


async def get_persistent_context() -> tuple:
    """Launch browser with persistent context.

    Returns (playwright, context) — caller must close both when done.

    The persistent context stores cookies in PROFILE_DIR, which persists
    between launches. This is how real browsers work — cookies survive
    because the profile directory keeps them.
    """
    os.makedirs(PROFILE_DIR, exist_ok=True)

    pw = await async_playwright().start()

    # If we have a storage_state backup but no profile yet, seed the profile
    # by importing cookies on first launch
    storage_path = Path(STORAGE_BACKUP)
    profile_cookies = Path(PROFILE_DIR) / "Default" / "Cookies"

    # Check if Xvfb is running — if so, use non-headless (avoids Twitter bot detection)
    import shutil
    has_display = os.environ.get("DISPLAY") is not None
    headless = USE_HEADLESS if has_display else True  # Fallback to headless if no display

    context = await pw.chromium.launch_persistent_context(
        user_data_dir=PROFILE_DIR,
        headless=headless,
        args=BROWSER_ARGS,
        ignore_default_args=IGNORE_ARGS,
        # Import storage state on first run to seed the profile
        storage_state=str(storage_path) if (storage_path.exists() and not profile_cookies.exists()) else None,
        viewport={"width": 1280, "height": 900},
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    )

    return pw, context


async def save_session(context: BrowserContext):
    """Save current session back to storage_state.json as backup."""
    try:
        os.makedirs(os.path.dirname(STORAGE_BACKUP), exist_ok=True)
        await context.storage_state(path=STORAGE_BACKUP)
    except Exception:
        pass  # Non-critical — profile dir is the primary store


async def close_session(pw, context: BrowserContext):
    """Save session and close browser cleanly."""
    await save_session(context)
    await context.close()
    await pw.stop()


async def import_fresh_cookies(cookies_path: str):
    """Import fresh cookies from a file into the persistent profile.

    Use this when you get new cookies from your real browser.
    It launches the profile, loads the cookies, visits Twitter to
    activate them, then saves.
    """
    pw, context = await get_persistent_context()
    try:
        # Load cookies from the provided file
        import json
        with open(cookies_path) as f:
            state = json.load(f)

        if "cookies" in state:
            await context.add_cookies(state["cookies"])

        # Visit Twitter to activate cookies and let them refresh
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://x.com/home", wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)

        # Save everything
        await save_session(context)
        return "Cookies imported and activated successfully"
    finally:
        await close_session(pw, context)

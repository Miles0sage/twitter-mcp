#!/usr/bin/env python3
"""Twitter session keepalive — pings X.com every 30 min to prevent cookie expiry."""

import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

STORAGE_STATE = Path.home() / ".twitter-mcp" / "storage_state.json"
LOG_DIR = Path(__file__).parent / "data"


async def ping_twitter() -> dict:
    from playwright.async_api import async_playwright

    if not STORAGE_STATE.exists():
        return {"success": False, "error": "storage_state.json not found"}

    pw = await async_playwright().start()
    browser = await pw.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        ignore_default_args=["--enable-automation"],
    )
    context = await browser.new_context(storage_state=str(STORAGE_STATE))

    try:
        page = await context.new_page()
        resp = await page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=20000)
        url = page.url
        status = resp.status if resp else 0

        if "login" in url or "accounts.google" in url:
            await browser.close()
            await pw.stop()
            return {"success": False, "error": "Session expired", "url": url}

        # Save refreshed cookies
        await context.storage_state(path=str(STORAGE_STATE))
        await browser.close()
        await pw.stop()
        return {"success": True, "status": status, "message": "Session alive, cookies refreshed"}

    except Exception as e:
        await browser.close()
        await pw.stop()
        return {"success": False, "error": str(e)}


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    result = asyncio.run(ping_twitter())
    status = "OK" if result["success"] else "FAIL"
    msg = result.get("message", result.get("error", ""))
    print(f"[{ts}] Twitter keepalive: {status} — {msg}")

    log_file = LOG_DIR / "twitter_keepalive.log"
    with open(log_file, "a") as f:
        f.write(json.dumps({"timestamp": ts, **result}) + "\n")

    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())

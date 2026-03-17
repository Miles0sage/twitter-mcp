#!/usr/bin/env python3
"""Twitter session keepalive — pings X.com every 30 min to prevent cookie expiry.

Uses persistent browser profile (same as all tools) so cookies stay alive
in the Chrome profile directory, not just storage_state.json.
"""

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from browser_session import get_persistent_context, close_session

LOG_DIR = Path(__file__).parent / "data"


async def ping_twitter() -> dict:
    try:
        pw, context = await get_persistent_context()
    except Exception as e:
        return {"success": False, "error": f"Browser launch failed: {e}"}

    try:
        page = context.pages[0] if context.pages else await context.new_page()
        resp = await page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=20000)
        url = page.url
        status = resp.status if resp else 0

        if "login" in url or "accounts.google" in url:
            await close_session(pw, context)
            return {"success": False, "error": "Session expired", "url": url}

        # Scroll a bit to look human
        await page.evaluate("window.scrollTo(0, 300)")
        await page.wait_for_timeout(2000)

        await close_session(pw, context)
        return {"success": True, "status": status, "message": "Session alive, cookies refreshed"}

    except Exception as e:
        try:
            await close_session(pw, context)
        except Exception:
            pass
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

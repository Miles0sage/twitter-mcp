"""Interactive login helper for the persistent Chrome profile.

Run this once, log in to X manually in the browser window that opens,
then press Enter in the terminal. Cookies persist for all future MCP calls.
"""

import asyncio
import sys
from browser_session import get_persistent_context, save_session, get_fresh_page, close_stale_pages


async def interactive_login():
    pw, context = await get_persistent_context(headless=False)

    page = await get_fresh_page(context)
    await close_stale_pages(context, keep=page)
    await page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded")

    print("\n" + "=" * 60)
    print("  Browser opened. Log in to X with your burner account.")
    print("  When you see the home timeline, return here and press Enter.")
    print("=" * 60 + "\n")

    try:
        input("Press Enter after you have finished logging in... ")
    except (EOFError, KeyboardInterrupt):
        print("\nAborted, closing without saving.")
        await context.close()
        await pw.stop()
        return 1

    cookies = await context.cookies("https://x.com")
    cookie_names = {c["name"] for c in cookies}

    if "auth_token" not in cookie_names:
        print("\nWARNING: 'auth_token' cookie not found — login may have failed.")
        print(f"Cookies present: {sorted(cookie_names)}")
        print("Closing without overwriting backup.")
        await context.close()
        await pw.stop()
        return 2

    await save_session(context)
    await context.close()
    await pw.stop()

    print("\nLogin saved. auth_token + ct0 captured.")
    print("Profile: ~/.twitter-mcp/chrome-profile/")
    print("Backup:  ~/.twitter-mcp/storage_state.json")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(interactive_login()))

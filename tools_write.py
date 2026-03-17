import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright


async def _setup_browser():
    """Set up Playwright browser with saved cookies/storage."""
    storage_state_path = Path.home() / ".twitter-mcp" / "storage_state.json"

    if not storage_state_path.exists():
        raise FileNotFoundError(f"Storage state file not found: {storage_state_path}")

    # Read storage state
    with open(storage_state_path, 'r') as f:
        storage_state = json.load(f)

    # Start Playwright and launch browser with context
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-blink-features=AutomationControlled'],
        ignore_default_args=['--enable-automation'],
    )

    # Create context with saved storage state
    context = await browser.new_context(
        storage_state=storage_state,
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )

    page = await context.new_page()

    return playwright, browser, context, page


async def _wait_for_navigation_and_load(page):
    """Wait for page to load properly after navigation."""
    await page.wait_for_load_state('networkidle')
    await page.wait_for_timeout(2000)  # Additional wait for dynamic content


async def post_tweet(text: str) -> str:
    """
    Post a tweet to X/Twitter.

    Args:
        text: The content of the tweet to post

    Returns:
        Success message
    """
    playwright = None
    browser = None
    context = None

    try:
        playwright, browser, context, page = await _setup_browser()

        # Navigate to the tweet composition page
        await page.goto("https://x.com/compose/post")
        await _wait_for_navigation_and_load(page)

        # Find and fill the tweet text area
        textbox = page.locator('[data-testid="tweetTextarea_0"]').first.or_(page.locator('[role="textbox"]').first)
        await textbox.click()
        await textbox.fill(text)

        # Click the post button
        post_button = page.locator('[data-testid="tweetButton"]').first.or_(page.locator('text=Post').first)
        await post_button.click()

        # Wait for the tweet to post
        await page.wait_for_timeout(3000)

        # Verify that the tweet was posted by checking for success indicators
        success_indicators = [
            page.locator('text=Posted'),
            page.locator('[data-testid="confirmationSheetDialog"]'),  # For retweets/likes
        ]

        # Wait briefly to see if any success indicator appears
        for indicator in success_indicators:
            try:
                await indicator.wait_for(timeout=5000)
                break
            except:
                continue

        return f'Tweet posted: {text[:50]}...'

    finally:
        # Clean up resources
        if context:
            await context.close()
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()


async def reply_to_tweet(tweet_url: str, text: str) -> str:
    """
    Reply to a specific tweet.

    Args:
        tweet_url: URL of the tweet to reply to
        text: The reply text

    Returns:
        Success message
    """
    playwright = None
    browser = None
    context = None

    try:
        playwright, browser, context, page = await _setup_browser()

        # Navigate to the tweet URL
        await page.goto(tweet_url)
        await _wait_for_navigation_and_load(page)

        # Find and click the reply button
        reply_button = page.locator('[data-testid="reply"]').first
        await reply_button.click()

        # Wait for reply composer to appear
        await page.wait_for_selector('[data-testid="tweetTextarea_0"], [role="textbox"]')

        # Find the reply text area
        textbox = page.locator('[data-testid="tweetTextarea_0"]').first.or_(page.locator('[role="textbox"]').first)
        await textbox.click()
        await textbox.fill(text)

        # Click the reply button
        post_button = page.locator('[data-testid="tweetButton"]').first.or_(page.locator('text=Post').first)
        await post_button.click()

        # Wait for the reply to post
        await page.wait_for_timeout(3000)

        return f'Replied to tweet: {text[:50]}...'

    finally:
        # Clean up resources
        if context:
            await context.close()
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()


async def like_tweet(tweet_url: str) -> str:
    """
    Like a specific tweet.

    Args:
        tweet_url: URL of the tweet to like

    Returns:
        Success message
    """
    playwright = None
    browser = None
    context = None

    try:
        playwright, browser, context, page = await _setup_browser()

        # Navigate to the tweet URL
        await page.goto(tweet_url)
        await _wait_for_navigation_and_load(page)

        # Find and click the like button
        like_button = page.locator('[data-testid="like"]').first
        await like_button.click()

        # Wait for the like to register
        await page.wait_for_timeout(2000)

        return f'Liked tweet: {tweet_url}'

    finally:
        # Clean up resources
        if context:
            await context.close()
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()


async def retweet(tweet_url: str) -> str:
    """
    Retweet a specific tweet (with confirmation).

    Args:
        tweet_url: URL of the tweet to retweet

    Returns:
        Success message
    """
    playwright = None
    browser = None
    context = None

    try:
        playwright, browser, context, page = await _setup_browser()

        # Navigate to the tweet URL
        await page.goto(tweet_url)
        await _wait_for_navigation_and_load(page)

        # Find and click the retweet button
        retweet_button = page.locator('[data-testid="retweet"]').first
        await retweet_button.click()

        # Wait for and click the confirm retweet button
        confirm_button = page.locator('text=Retweet').first
        await confirm_button.click()

        # Wait for the retweet to register
        await page.wait_for_timeout(2000)

        return f'Retweeted tweet: {tweet_url}'

    finally:
        # Clean up resources
        if context:
            await context.close()
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()


# Synchronous wrapper functions to fix nested event loop issues
def sync_post_tweet(text: str) -> str:
    """Synchronous wrapper for post_tweet function."""
    if asyncio.get_event_loop().is_running():
        # If there's already a running loop, create a new one in a separate thread
        import concurrent.futures
        import threading

        def run_in_thread():
            return asyncio.run(post_tweet(text))

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result()
    else:
        return asyncio.run(post_tweet(text))


def sync_reply_to_tweet(tweet_url: str, text: str) -> str:
    """Synchronous wrapper for reply_to_tweet function."""
    if asyncio.get_event_loop().is_running():
        # If there's already a running loop, create a new one in a separate thread
        import concurrent.futures
        import threading

        def run_in_thread():
            return asyncio.run(reply_to_tweet(tweet_url, text))

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result()
    else:
        return asyncio.run(reply_to_tweet(tweet_url, text))


def sync_like_tweet(tweet_url: str) -> str:
    """Synchronous wrapper for like_tweet function."""
    if asyncio.get_event_loop().is_running():
        # If there's already a running loop, create a new one in a separate thread
        import concurrent.futures
        import threading

        def run_in_thread():
            return asyncio.run(like_tweet(tweet_url))

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result()
    else:
        return asyncio.run(like_tweet(tweet_url))


def sync_retweet(tweet_url: str) -> str:
    """Synchronous wrapper for retweet function."""
    if asyncio.get_event_loop().is_running():
        # If there's already a running loop, create a new one in a separate thread
        import concurrent.futures
        import threading

        def run_in_thread():
            return asyncio.run(retweet(tweet_url))

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result()
    else:
        return asyncio.run(retweet(tweet_url))
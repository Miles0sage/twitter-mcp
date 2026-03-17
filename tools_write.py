import asyncio
import json
import concurrent.futures
from browser_session import get_persistent_context, close_session


async def _wait_for_load(page):
    """Wait for page to load properly."""
    await page.wait_for_load_state('networkidle')
    await page.wait_for_timeout(2000)


async def post_tweet(text: str) -> str:
    """Post a tweet to X/Twitter."""
    pw, context = await get_persistent_context()

    try:
        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto("https://x.com/compose/post")
        await _wait_for_load(page)

        textbox = page.locator('[data-testid="tweetTextarea_0"]').first.or_(page.locator('[role="textbox"]').first)
        await textbox.click()
        await textbox.fill(text)

        post_button = page.locator('[data-testid="tweetButton"]').first.or_(page.locator('text=Post').first)
        await post_button.click()
        await page.wait_for_timeout(3000)

        return f'Tweet posted: {text[:50]}...'

    finally:
        await close_session(pw, context)


async def reply_to_tweet(tweet_url: str, text: str) -> str:
    """Reply to a specific tweet."""
    pw, context = await get_persistent_context()

    try:
        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto(tweet_url)
        await _wait_for_load(page)

        reply_button = page.locator('[data-testid="reply"]').first
        await reply_button.click()

        await page.wait_for_selector('[data-testid="tweetTextarea_0"], [role="textbox"]')

        textbox = page.locator('[data-testid="tweetTextarea_0"]').first.or_(page.locator('[role="textbox"]').first)
        await textbox.click()
        await textbox.fill(text)

        post_button = page.locator('[data-testid="tweetButton"]').first.or_(page.locator('text=Post').first)
        await post_button.click()
        await page.wait_for_timeout(3000)

        return f'Replied to tweet: {text[:50]}...'

    finally:
        await close_session(pw, context)


async def like_tweet(tweet_url: str) -> str:
    """Like a specific tweet."""
    pw, context = await get_persistent_context()

    try:
        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto(tweet_url)
        await _wait_for_load(page)

        like_button = page.locator('[data-testid="like"]').first
        await like_button.click()
        await page.wait_for_timeout(2000)

        return f'Liked tweet: {tweet_url}'

    finally:
        await close_session(pw, context)


async def retweet(tweet_url: str) -> str:
    """Retweet a specific tweet."""
    pw, context = await get_persistent_context()

    try:
        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto(tweet_url)
        await _wait_for_load(page)

        retweet_button = page.locator('[data-testid="retweet"]').first
        await retweet_button.click()

        confirm_button = page.locator('text=Retweet').first
        await confirm_button.click()
        await page.wait_for_timeout(2000)

        return f'Retweeted tweet: {tweet_url}'

    finally:
        await close_session(pw, context)


# Synchronous wrappers
def sync_post_tweet(text: str) -> str:
    try:
        asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return executor.submit(asyncio.run, post_tweet(text)).result()
    except RuntimeError:
        return asyncio.run(post_tweet(text))


def sync_reply_to_tweet(tweet_url: str, text: str) -> str:
    try:
        asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return executor.submit(asyncio.run, reply_to_tweet(tweet_url, text)).result()
    except RuntimeError:
        return asyncio.run(reply_to_tweet(tweet_url, text))


def sync_like_tweet(tweet_url: str) -> str:
    try:
        asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return executor.submit(asyncio.run, like_tweet(tweet_url)).result()
    except RuntimeError:
        return asyncio.run(like_tweet(tweet_url))


def sync_retweet(tweet_url: str) -> str:
    try:
        asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return executor.submit(asyncio.run, retweet(tweet_url)).result()
    except RuntimeError:
        return asyncio.run(retweet(tweet_url))

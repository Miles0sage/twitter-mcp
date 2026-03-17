import asyncio
import json
from playwright.async_api import async_playwright
from pathlib import Path


async def read_feed(max_results: int = 20) -> str:
    """
    Read tweets from the Twitter home feed.

    Args:
        max_results: Maximum number of tweets to return (default: 20)

    Returns:
        JSON string containing tweet data (text, author, timestamp)
    """
    storage_state_path = Path.home() / ".twitter-mcp" / "storage_state.json"

    if not storage_state_path.exists():
        return json.dumps({"error": f"Storage state not found at {storage_state_path}"})

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-blink-features=AutomationControlled'],
            ignore_default_args=['--enable-automation'],
        )
        context = await browser.new_context(storage_state=str(storage_state_path))
        page = await context.new_page()

        try:
            # Navigate to Twitter home
            await page.goto("https://x.com/home", wait_until="networkidle")

            # Wait for tweets to load
            await page.wait_for_selector('[data-testid="tweet"]', timeout=10000)

            tweets = []
            scroll_attempts = 0
            max_scroll_attempts = 10  # Prevent infinite scrolling

            while len(tweets) < max_results and scroll_attempts < max_scroll_attempts:
                # Get all tweet elements
                tweet_elements = await page.query_selector_all('[data-testid="tweet"]')

                for tweet_element in tweet_elements:
                    if len(tweets) >= max_results:
                        break

                    try:
                        # Extract tweet text
                        tweet_text_element = await tweet_element.query_selector('div[data-testid="tweetText"]')
                        tweet_text = ""
                        if tweet_text_element:
                            tweet_text = await tweet_text_element.inner_text()

                        # Extract author
                        author_element = await tweet_element.query_selector('div[data-testid="User-Name"] div span')
                        author = ""
                        if author_element:
                            author = await author_element.inner_text()

                        # Extract timestamp
                        time_element = await tweet_element.query_selector('time')
                        timestamp = ""
                        if time_element:
                            timestamp = await time_element.get_attribute('datetime')

                        tweet_data = {
                            "author": author,
                            "text": tweet_text,
                            "timestamp": timestamp
                        }

                        # Avoid adding duplicate tweets
                        if tweet_data not in tweets:
                            tweets.append(tweet_data)

                    except Exception:
                        continue  # Skip problematic tweets

                if len(tweets) < max_results:
                    # Scroll to load more tweets
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(2)  # Wait for new tweets to load
                    scroll_attempts += 1

            return json.dumps(tweets, ensure_ascii=False)

        except Exception as e:
            return json.dumps({"error": f"Failed to read feed: {str(e)}"})

        finally:
            await browser.close()


async def read_notifications() -> str:
    """
    Read notifications from Twitter.

    Returns:
        JSON string containing notification data
    """
    storage_state_path = Path.home() / ".twitter-mcp" / "storage_state.json"

    if not storage_state_path.exists():
        return json.dumps({"error": f"Storage state not found at {storage_state_path}"})

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-blink-features=AutomationControlled'],
            ignore_default_args=['--enable-automation'],
        )
        context = await browser.new_context(storage_state=str(storage_state_path))
        page = await context.new_page()

        try:
            # Navigate to Twitter notifications
            await page.goto("https://x.com/notifications", wait_until="networkidle")

            # Wait for notifications to load
            await page.wait_for_selector('[data-testid="notification"]', timeout=10000)

            notifications = []
            # Get all notification elements
            notification_elements = await page.query_selector_all('[data-testid="notification"]')

            for notification_element in notification_elements:
                try:
                    full_text = await notification_element.inner_text()
                    lines = [l.strip() for l in full_text.split('\n') if l.strip()]
                    text = ' '.join(lines[:5]) if lines else ""

                    time_element = await notification_element.query_selector('time')
                    timestamp = ""
                    if time_element:
                        timestamp = await time_element.get_attribute('datetime')

                    notifications.append({
                        "text": text[:300],
                        "timestamp": timestamp
                    })

                except Exception:
                    continue  # Skip problematic notifications

            return json.dumps(notifications, ensure_ascii=False)

        except Exception as e:
            return json.dumps({"error": f"Failed to read notifications: {str(e)}"})

        finally:
            await browser.close()


def sync_read_feed(max_results: int = 20) -> str:
    """Synchronous wrapper for read_feed"""
    return asyncio.run(read_feed(max_results))


def sync_read_notifications() -> str:
    """Synchronous wrapper for read_notifications"""
    return asyncio.run(read_notifications())
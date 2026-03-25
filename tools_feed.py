import asyncio
import json
import concurrent.futures
from browser_session import get_persistent_context, close_session


async def read_feed(max_results: int = 20) -> str:
    """Read tweets from the Twitter home feed."""
    pw, context = await get_persistent_context()

    try:
        page = context.pages[0] if context.pages else await context.new_page()

        # Use domcontentloaded instead of networkidle (Twitter never stops loading)
        await page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=20000)

        # Wait for tweets to load
        await page.wait_for_selector('[data-testid="tweet"]', timeout=15000)

        tweets = []
        scroll_attempts = 0
        max_scroll_attempts = 10

        while len(tweets) < max_results and scroll_attempts < max_scroll_attempts:
            tweet_elements = await page.query_selector_all('[data-testid="tweet"]')

            for tweet_element in tweet_elements:
                if len(tweets) >= max_results:
                    break

                try:
                    tweet_text_element = await tweet_element.query_selector('div[data-testid="tweetText"]')
                    tweet_text = await tweet_text_element.inner_text() if tweet_text_element else ""

                    author_element = await tweet_element.query_selector('div[data-testid="User-Name"] div span')
                    author = await author_element.inner_text() if author_element else ""

                    time_element = await tweet_element.query_selector('time')
                    timestamp = await time_element.get_attribute('datetime') if time_element else ""

                    tweet_data = {"author": author, "text": tweet_text, "timestamp": timestamp}

                    if tweet_data not in tweets:
                        tweets.append(tweet_data)

                except Exception:
                    continue

            if len(tweets) < max_results:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)
                scroll_attempts += 1

        return json.dumps(tweets, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": f"Failed to read feed: {str(e)}"})

    finally:
        await close_session(pw, context)


async def read_notifications() -> str:
    """Read notifications from Twitter."""
    pw, context = await get_persistent_context()

    try:
        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto("https://x.com/notifications", wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_selector('[data-testid="cellInnerDiv"]', timeout=15000)

        notifications = []
        notification_elements = await page.query_selector_all('[data-testid="cellInnerDiv"]')

        for notification_element in notification_elements[:20]:
            try:
                full_text = await notification_element.inner_text()
                lines = [l.strip() for l in full_text.split('\n') if l.strip()]
                text = ' '.join(lines[:5]) if lines else ""
                if not text or len(text) < 5:
                    continue

                time_element = await notification_element.query_selector('time')
                timestamp = await time_element.get_attribute('datetime') if time_element else ""

                notifications.append({"text": text[:300], "timestamp": timestamp})

            except Exception:
                continue

        return json.dumps(notifications, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": f"Failed to read notifications: {str(e)}"})

    finally:
        await close_session(pw, context)


def sync_read_feed(max_results: int = 20) -> str:
    """Synchronous wrapper for read_feed"""
    def _run():
        return asyncio.run(read_feed(max_results))
    try:
        asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return executor.submit(_run).result(timeout=60)
    except RuntimeError:
        return asyncio.run(read_feed(max_results))


async def read_bookmarks(max_results: int = 20) -> str:
    """Read bookmarked tweets from Twitter."""
    pw, context = await get_persistent_context()

    try:
        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto("https://x.com/i/bookmarks", wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_selector('[data-testid="tweet"]', timeout=15000)

        tweets = []
        scroll_attempts = 0
        max_scroll_attempts = 10

        while len(tweets) < max_results and scroll_attempts < max_scroll_attempts:
            tweet_elements = await page.query_selector_all('[data-testid="tweet"]')

            for tweet_element in tweet_elements:
                if len(tweets) >= max_results:
                    break

                try:
                    tweet_text_element = await tweet_element.query_selector('div[data-testid="tweetText"]')
                    tweet_text = await tweet_text_element.inner_text() if tweet_text_element else ""

                    author_element = await tweet_element.query_selector('div[data-testid="User-Name"] div span')
                    author = await author_element.inner_text() if author_element else ""

                    time_element = await tweet_element.query_selector('time')
                    timestamp = await time_element.get_attribute('datetime') if time_element else ""

                    # Try to get link
                    link_elements = await tweet_element.query_selector_all('a[href*="/status/"]')
                    link = ""
                    for le in link_elements:
                        href = await le.get_attribute('href')
                        if href and '/status/' in href:
                            link = f"https://x.com{href}" if href.startswith('/') else href
                            break

                    tweet_data = {"author": author, "text": tweet_text, "timestamp": timestamp, "link": link}

                    if tweet_data not in tweets:
                        tweets.append(tweet_data)

                except Exception:
                    continue

            if len(tweets) < max_results:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)
                scroll_attempts += 1

        return json.dumps(tweets, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": f"Failed to read bookmarks: {str(e)}"})

    finally:
        await close_session(pw, context)


def sync_read_bookmarks(max_results: int = 20) -> str:
    """Synchronous wrapper for read_bookmarks"""
    def _run():
        return asyncio.run(read_bookmarks(max_results))
    try:
        asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return executor.submit(_run).result(timeout=90)
    except RuntimeError:
        return asyncio.run(read_bookmarks(max_results))


def sync_read_notifications() -> str:
    """Synchronous wrapper for read_notifications"""
    def _run():
        return asyncio.run(read_notifications())
    try:
        asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return executor.submit(_run).result(timeout=60)
    except RuntimeError:
        return asyncio.run(read_notifications())

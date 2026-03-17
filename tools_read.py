import asyncio
import urllib.parse
from playwright.async_api import async_playwright
import concurrent.futures
from typing import Optional
from browser_session import get_persistent_context, close_session


async def _search_tweets_async(query: str, max_results: int = 10) -> str:
    """Navigate to Twitter search and extract tweets."""
    pw, context = await get_persistent_context()

    try:
        page = context.pages[0] if context.pages else await context.new_page()

        # Navigate to search results
        encoded_query = urllib.parse.quote(query)
        url = f"https://x.com/search?q={encoded_query}&f=live"
        await page.goto(url)

        # Wait for tweets to load
        await page.wait_for_selector('[data-testid="tweet"]', timeout=10000)

        # Extract tweets
        tweet_elements = await page.query_selector_all('[data-testid="tweet"]')

        results = []
        for i, tweet_element in enumerate(tweet_elements[:max_results]):
            try:
                # Extract author name
                author_name_el = await tweet_element.query_selector('[data-testid="User-Name"] span')
                author_name = await author_name_el.inner_text() if author_name_el else "Unknown"

                # Extract handle
                handle_el = await tweet_element.query_selector('a[href*="/"] span')
                handle = await handle_el.inner_text() if handle_el else "Unknown"

                # Extract tweet text
                tweet_text_el = await tweet_element.query_selector('div[data-testid="tweetText"]')
                tweet_text = await tweet_text_el.inner_text() if tweet_text_el else ""

                # Extract timestamp
                time_el = await tweet_element.query_selector('time')
                timestamp = await time_el.get_attribute('datetime') if time_el else "Unknown"

                # Extract engagement counts
                # Looking for likes, retweets, replies by finding elements with aria-labels or specific selectors
                reply_el = await tweet_element.query_selector('button[aria-label*="Reply" i]')
                reply_count = await reply_el.inner_text() if reply_el else "0"

                retweet_el = await tweet_element.query_selector('button[aria-label*="Retweet" i]')
                retweet_count = await retweet_el.inner_text() if retweet_el else "0"

                like_el = await tweet_element.query_selector('button[aria-label*="Like" i]')
                like_count = await like_el.inner_text() if like_el else "0"

                tweet_info = f"{i+1}. Author: {author_name}\n   Handle: {handle}\n   Text: {tweet_text}\n   Timestamp: {timestamp}\n   Replies: {reply_count}, Retweets: {retweet_count}, Likes: {like_count}\n"
                results.append(tweet_info)

            except Exception as e:
                continue  # Skip problematic tweets

        if not results:
            return f"No tweets found for query: {query}"

        return "\n".join(results)

    finally:
        await close_session(pw, context)


def search_tweets(query: str, max_results: int = 10) -> str:
    """Synchronous wrapper for search_tweets."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running event loop, safe to call asyncio.run()
        return asyncio.run(_search_tweets_async(query, max_results))

    # There is a running event loop, use ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(asyncio.run, _search_tweets_async(query, max_results))
        return future.result()


async def _get_user_profile_async(username: str) -> str:
    """Get user profile information from Twitter."""
    pw, context = await get_persistent_context()

    try:
        page = context.pages[0] if context.pages else await context.new_page()

        # Navigate to user profile
        url = f"https://x.com/{username}"
        await page.goto(url)

        # Wait for page to load
        await page.wait_for_timeout(3000)

        # Extract bio
        bio_el = await page.query_selector('[data-testid="UserDescription"]')
        bio = await bio_el.inner_text() if bio_el else "No bio"

        # Extract follower/following from links
        follower_el = await page.query_selector('a[href$="/verified_followers"] span span, a[href$="/followers"] span span')
        followers = await follower_el.inner_text() if follower_el else "?"

        following_el = await page.query_selector('a[href$="/following"] span span')
        following = await following_el.inner_text() if following_el else "?"

        # Get display name from page
        name_el = await page.query_selector('[data-testid="UserName"] span')
        name = await name_el.inner_text() if name_el else username

        return f"Name: {name}\nUsername: @{username}\nBio: {bio}\nFollowers: {followers}\nFollowing: {following}"

    finally:
        await close_session(pw, context)


def get_user_profile(username: str) -> str:
    """Synchronous wrapper for get_user_profile."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running event loop, safe to call asyncio.run()
        return asyncio.run(_get_user_profile_async(username))

    # There is a running event loop, use ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(asyncio.run, _get_user_profile_async(username))
        return future.result()


async def _get_user_tweets_async(username: str, max_results: int = 10) -> str:
    """Get tweets from a user's profile."""
    pw, context = await get_persistent_context()

    try:
        page = context.pages[0] if context.pages else await context.new_page()

        # Navigate to user profile
        url = f"https://x.com/{username}"
        await page.goto(url)

        # Wait for tweets to load
        await page.wait_for_selector('[data-testid="cellInnerDiv"]', timeout=10000)

        # Scroll to load more tweets
        tweets = []
        scroll_attempts = 0
        max_scroll_attempts = 5

        while len(tweets) < max_results and scroll_attempts < max_scroll_attempts:
            # Find tweet elements
            tweet_elements = await page.query_selector_all('[data-testid="cellInnerDiv"] [data-testid="tweet"]')

            for tweet_element in tweet_elements[len(tweets):max_results]:
                if len(tweets) >= max_results:
                    break

                try:
                    # Extract author name
                    author_name_el = await tweet_element.query_selector('[data-testid="User-Name"] span')
                    author_name = await author_name_el.inner_text() if author_name_el else "Unknown"

                    # Extract tweet text
                    tweet_text_el = await tweet_element.query_selector('div[data-testid="tweetText"]')
                    tweet_text = await tweet_text_el.inner_text() if tweet_text_el else ""

                    # Extract timestamp
                    time_el = await tweet_element.query_selector('time')
                    timestamp = await time_el.get_attribute('datetime') if time_el else "Unknown"

                    # Extract engagement counts
                    reply_el = await tweet_element.query_selector('button[aria-label*="Reply" i]')
                    reply_count = await reply_el.inner_text() if reply_el else "0"

                    retweet_el = await tweet_element.query_selector('button[aria-label*="Retweet" i]')
                    retweet_count = await retweet_el.inner_text() if retweet_el else "0"

                    like_el = await tweet_element.query_selector('button[aria-label*="Like" i]')
                    like_count = await like_el.inner_text() if like_el else "0"

                    tweet_info = f"Author: {author_name}\n   Text: {tweet_text}\n   Timestamp: {timestamp}\n   Replies: {reply_count}, Retweets: {retweet_count}, Likes: {like_count}\n"
                    tweets.append(tweet_info)

                except Exception:
                    continue

            if len(tweets) < max_results:
                # Scroll down to load more tweets
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)  # Wait for new tweets to load
                scroll_attempts += 1

        if not tweets:
            return f"No tweets found for user: {username}"

        result = f"Tweets from {username}:\n"
        for i, tweet in enumerate(tweets[:max_results], 1):
            result += f"\n{i}. {tweet}"

        return result

    finally:
        await close_session(pw, context)


def get_user_tweets(username: str, max_results: int = 10) -> str:
    """Synchronous wrapper for get_user_tweets."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running event loop, safe to call asyncio.run()
        return asyncio.run(_get_user_tweets_async(username, max_results))

    # There is a running event loop, use ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(asyncio.run, _get_user_tweets_async(username, max_results))
        return future.result()


async def _get_trending_async() -> str:
    """Get trending topics from Twitter."""
    pw, context = await get_persistent_context()

    try:
        page = context.pages[0] if context.pages else await context.new_page()

        # Navigate to home page — trending sidebar loads here
        await page.goto("https://x.com/home", wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # Get trends from sidebar "What's happening" section
        trend_elements = await page.query_selector_all('[data-testid="trend"]')

        trends = []
        for el in trend_elements[:15]:
            try:
                full_text = await el.inner_text()
                lines = [l.strip() for l in full_text.split('\n') if l.strip() and l.strip() != '·']
                lines = [l for l in lines if len(l) > 1 and l not in ('Trending', 'Show more')]
                if lines:
                    entry = f"{len(trends)+1}. {lines[0]}"
                    if len(lines) > 1 and any(w in lines[1].lower() for w in ['post', 'k ', 'trending']):
                        entry += f" ({lines[1]})"
                    trends.append(entry)
                    if len(trends) >= 10:
                        break
            except Exception:
                continue

        if not trends:
            return "Trending unavailable on headless VPS. Use twitter_search to find popular topics."

        return "Trending Topics:\n" + "\n".join(trends)

    finally:
        await close_session(pw, context)


def get_trending() -> str:
    """Synchronous wrapper for get_trending."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running event loop, safe to call asyncio.run()
        return asyncio.run(_get_trending_async())

    # There is a running event loop, use ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(asyncio.run, _get_trending_async())
        return future.result()


# Example usage:
if __name__ == "__main__":
    # Example of how to use the functions
    print("Searching for tweets...")
    results = search_tweets("python programming", 5)
    print(results)

    print("\nGetting user profile...")
    profile = get_user_profile("elonmusk")
    print(profile)

    print("\nGetting user tweets...")
    user_tweets = get_user_tweets("elonmusk", 3)
    print(user_tweets)

    print("\nGetting trending topics...")
    trending = get_trending()
    print(trending)
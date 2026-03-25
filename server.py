"""Twitter/X MCP Server — 10 tools for reading and posting on Twitter/X, no API key needed."""

from mcp.server.fastmcp import FastMCP


def create_server():
    mcp = FastMCP("twitter-mcp")

    @mcp.tool()
    def twitter_search(query: str, max_results: int = 10) -> str:
        """Search Twitter/X for tweets by keyword.
        Args:
            query: Search query
            max_results: Max tweets to return (default 10)
        """
        try:
            from tools_read import search_tweets
            return search_tweets(query, max_results)
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def twitter_user(username: str) -> str:
        """Get a Twitter/X user's profile (bio, followers, following).
        Args:
            username: Twitter username (without @)
        """
        try:
            from tools_read import get_user_profile
            return get_user_profile(username)
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def twitter_user_tweets(username: str, max_results: int = 10) -> str:
        """Get recent tweets from a Twitter/X user.
        Args:
            username: Twitter username (without @)
            max_results: Max tweets (default 10)
        """
        try:
            from tools_read import get_user_tweets
            return get_user_tweets(username, max_results)
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def twitter_trending() -> str:
        """Get trending topics on Twitter/X."""
        try:
            from tools_read import get_trending
            return get_trending()
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def twitter_post(text: str) -> str:
        """Post a tweet. Requires auth cookies (~/.twitter-mcp/storage_state.json).
        Args:
            text: Tweet text (max 280 chars)
        """
        try:
            from tools_write import sync_post_tweet
            return sync_post_tweet(text)
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def twitter_reply(tweet_url: str, text: str) -> str:
        """Reply to a tweet. Requires auth cookies.
        Args:
            tweet_url: URL of the tweet to reply to
            text: Reply text
        """
        try:
            from tools_write import sync_reply_to_tweet
            return sync_reply_to_tweet(tweet_url, text)
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def twitter_like(tweet_url: str) -> str:
        """Like a tweet. Requires auth cookies.
        Args:
            tweet_url: URL of the tweet to like
        """
        try:
            from tools_write import sync_like_tweet
            return sync_like_tweet(tweet_url)
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def twitter_retweet(tweet_url: str) -> str:
        """Retweet a tweet. Requires auth cookies.
        Args:
            tweet_url: URL of the tweet to retweet
        """
        try:
            from tools_write import sync_retweet
            return sync_retweet(tweet_url)
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def twitter_feed(max_results: int = 20) -> str:
        """Read your Twitter/X home feed. Requires auth cookies.
        Args:
            max_results: Max tweets to return (default 20)
        """
        try:
            from tools_feed import sync_read_feed
            return sync_read_feed(max_results)
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def twitter_notifications() -> str:
        """Read your Twitter/X notifications and mentions. Requires auth cookies."""
        try:
            from tools_feed import sync_read_notifications
            return sync_read_notifications()
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def twitter_bookmarks(max_results: int = 20) -> str:
        """Read your saved/bookmarked tweets on Twitter/X. Requires auth cookies.
        Args:
            max_results: Max bookmarks to return (default 20)
        """
        try:
            from tools_feed import sync_read_bookmarks
            return sync_read_bookmarks(max_results)
        except Exception as e:
            return f"Error: {e}"

    return mcp


if __name__ == "__main__":
    mcp = create_server()
    mcp.run()

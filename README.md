# 🐦 Twitter/X MCP Server

Free Twitter/X integration for AI agents — no API key needed. Read tweets, post, search, trending — all via Playwright browser automation.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/) [![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE) [![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-brightgreen.svg)](https://github.com/modelcontextprotocol) [![Tools](https://img.shields.io/badge/Tools-12-orange.svg)](#)

## What

Twitter/X MCP Server provides a complete integration layer between AI agents and Twitter/X using Playwright browser automation. Unlike traditional Twitter API approaches that require API keys and face rate limits, this server leverages browser automation to access Twitter functionality without API restrictions. It offers tools for reading tweets, posting content, searching, trending topics, and more — all accessible through the Model Context Protocol (MCP).

## Tools

| Tool Name | Description | Authentication Required |
|----------|-------------|------------------------|
| twitter_search | Search for tweets by keyword or hashtag | No |
| twitter_post | Post a new tweet | Yes |
| twitter_read_feed | Read the user's feed | Yes |
| twitter_read_profile | Read a user's profile information | No |
| twitter_read_tweet | Read a specific tweet | No |
| twitter_like_tweet | Like a specific tweet | Yes |
| twitter_retweet | Retweet a specific tweet | Yes |
| twitter_follow_user | Follow a user | Yes |
| twitter_unfollow_user | Unfollow a user | Yes |
| twitter_get_trending | Get trending topics | No |
| twitter_get_user_tweets | Get tweets from a specific user | No |
| twitter_reply_to_tweet | Reply to a specific tweet | Yes |

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/twitter-mcp.git
cd twitter-mcp
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Add to your `~/.mcp.json`:
```json
{
  "servers": [
    {
      "name": "twitter-mcp",
      "cmd": ["python", "/path/to/your/twitter-mcp/server.py"],
      "env": {}
    }
  ]
}
```

## Auth Setup

For write operations (posting, liking, following, etc.), you need to authenticate with Twitter/X using Playwright:

1. Run the login command:
```bash
playwright open https://twitter.com
```

2. Login with your Twitter/X credentials in the opened browser
3. The authentication cookies will be saved for use by the tools

## Examples

### Search for tweets:
```python
# Search for tweets containing a keyword
tweets = twitter_search(keyword="AI", max_results=10)
```

### Post a tweet:
```python
# Post a new tweet (requires authentication)
result = twitter_post(content="Just tried the new Twitter/X MCP server! Amazing!")
```

### Read your feed:
```python
# Read the authenticated user's feed (requires authentication)
feed_tweets = twitter_read_feed(max_results=20)
```
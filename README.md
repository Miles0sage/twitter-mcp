# Twitter/X MCP Server

**Read, search, and post on Twitter/X from any AI agent.** No API key needed -- uses persistent browser sessions.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![MCP Compatible](https://img.shields.io/badge/MCP-compatible-brightgreen?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCI+PC9zdmc+)](https://modelcontextprotocol.io)
[![Tools: 11](https://img.shields.io/badge/tools-11-orange.svg)](#tools)
[![GitHub stars](https://img.shields.io/github/stars/Miles0sage/twitter-mcp?style=social)](https://github.com/Miles0sage/twitter-mcp)

---

## Why This Exists

Twitter's API costs $100+/month and rate-limits everything. This MCP server uses **Playwright browser automation** with a persistent Chrome profile instead -- zero API fees, no rate limit headaches. Your AI agent gets full Twitter access through the Model Context Protocol.

Works with Claude Code, Cursor, Windsurf, or any MCP-compatible client.

---

## Tools

| Category | Tool | Description | Auth Required |
|----------|------|-------------|:---:|
| **Read** | `twitter_search` | Search tweets by keyword or hashtag | No |
| | `twitter_feed` | Read your home timeline | Yes |
| | `twitter_bookmarks` | Read your saved bookmarks | Yes |
| | `twitter_user` | Get a user's profile info | No |
| | `twitter_user_tweets` | Get tweets from a specific user | No |
| | `twitter_trending` | Get trending topics | No |
| | `twitter_notifications` | Read your notifications | Yes |
| **Write** | `twitter_post` | Post a new tweet | Yes |
| | `twitter_reply` | Reply to a tweet | Yes |
| | `twitter_like` | Like a tweet | Yes |
| | `twitter_retweet` | Retweet a tweet | Yes |

> **No API key needed.** Read-only tools work without authentication. Write tools require a one-time browser login (cookies persist automatically).

---

## Quick Start

```bash
git clone https://github.com/Miles0sage/twitter-mcp.git
cd twitter-mcp
pip install -r requirements.txt
playwright install chromium
```

Add to your MCP config (`~/.mcp.json` or client settings):

```json
{
  "mcpServers": {
    "twitter": {
      "command": "python3",
      "args": ["server.py"],
      "cwd": "/path/to/twitter-mcp"
    }
  }
}
```

---

## Authentication

This server uses a **persistent Chrome profile** stored at `~/.twitter-mcp/chrome-profile/`. Log in once and your session persists across restarts.

### First-time setup

```bash
# Opens a real browser -- log in to Twitter/X manually
python3 -c "from browser_session import login; login()"
```

Once logged in, cookies are saved to the Chrome profile. All future MCP calls reuse the session automatically.

### Headless vs non-headless

Twitter blocks headless browsers. The server runs Chromium with `DISPLAY=:99` (Xvfb) by default for server environments. On desktop, it uses your normal display.

```bash
# Server/VPS setup
export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 &
```

### Keepalive

A keepalive script prevents session expiry by loading Twitter periodically:

```bash
# Add to crontab (every 30 min)
*/30 * * * * DISPLAY=:99 python3 /path/to/twitter-mcp/twitter_keepalive.py
```

---

## Usage Examples

```
"Search Twitter for AI agent news"
  -> Latest tweets matching query, with engagement stats

"Read my feed"
  -> Your home timeline, newest first

"Show my bookmarks"
  -> Your saved/bookmarked tweets

"Post: Just shipped a new MCP server!"
  -> Tweet posted, returns URL

"What's trending?"
  -> Top trending topics with tweet counts

"Get @elonmusk's recent tweets"
  -> Latest tweets from the user
```

---

## Architecture

```
LLM / MCP Client
       |
  MCP Protocol (stdio)
       |
  server.py ── registers 11 tools
       |
  +----+----+--------+
  |         |        |
tools_   tools_   tools_
read.py  feed.py  write.py
  |         |        |
  +----+----+--------+
       |
  browser_session.py
  (persistent Chromium via Playwright)
       |
  ~/.twitter-mcp/chrome-profile/
  (cookies + session state)
```

---

## Project Structure

```
server.py               # MCP server, tool registration
tools_read.py           # Search, user profile, user tweets, trending
tools_feed.py           # Feed, bookmarks, notifications
tools_write.py          # Post, reply, like, retweet
browser_session.py      # Playwright session management, persistent Chrome profile
twitter_keepalive.py    # Session keepalive cron script
api_server.py           # Optional REST API wrapper
```

---

## Comparison

| Feature | Twitter MCP | Twitter API (Basic) | Twitter API (Pro) | Apify Scrapers |
|---------|:-:|:-:|:-:|:-:|
| Cost | **Free** | $100/mo | $5,000/mo | Per-run fees |
| Auth | Browser login | OAuth + API key | OAuth + API key | API key |
| Post tweets | Yes | Yes | Yes | No |
| Read feed | Yes | Limited | Yes | Yes |
| Bookmarks | Yes | No | Yes | No |
| Search | Yes | Limited | Yes | Yes |
| Rate limits | Browser-level | Strict | Strict | Per-plan |
| MCP native | Yes | No | No | No |
| Setup time | 2 min | 30+ min | Application | 10 min |

---

## License

MIT

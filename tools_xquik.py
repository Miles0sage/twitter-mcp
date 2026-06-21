import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


API_KEY_ENV = "XQUIK_API_KEY"
BASE_URL_ENV = "XQUIK_BASE_URL"
DEFAULT_BASE_URL = "https://xquik.com"
REQUEST_TIMEOUT_SECONDS = 20


class XquikError(RuntimeError):
    """Raised when the optional Xquik backend returns an error."""


def should_use_xquik() -> bool:
    """Return true when read tools should use Xquik instead of browser scraping."""
    return bool(os.environ.get(API_KEY_ENV))


def xquik_search_tweets(query: str, max_results: int = 10) -> str:
    data = _request_json(
        "/x/tweets/search",
        {"q": query, "limit": max_results, "queryType": "Latest"},
    )
    tweets = _tweet_list(data)[:max_results]
    if not tweets:
        return f"No tweets found for query: {query}"
    return _format_tweets(tweets)


def xquik_user_profile(username: str) -> str:
    profile = _request_json(f"/x/users/{_quote_path(_clean_username(username))}", {})
    return _format_profile(profile, username)


def xquik_user_tweets(username: str, max_results: int = 10) -> str:
    clean_username = _clean_username(username)
    profile = _request_json(f"/x/users/{_quote_path(clean_username)}", {})
    user_id = str(_field(profile, "id", default=clean_username))
    data = _request_json(f"/x/users/{_quote_path(user_id)}/tweets", {})
    tweets = _tweet_list(data)[:max_results]
    if not tweets:
        return f"No tweets found for user: {clean_username}"
    return f"Tweets from {clean_username}:\n\n{_format_tweets(tweets)}"


def xquik_trending() -> str:
    data = _request_json("/x/trends", {"count": 10})
    trends = data.get("trends", [])
    if not isinstance(trends, list) or not trends:
        return "Trending unavailable from Xquik."

    lines: list[str] = []
    for index, trend in enumerate(trends[:10], 1):
        if not isinstance(trend, dict):
            continue
        name = _field(trend, "name", default="")
        detail = _field(trend, "description", "query", default="")
        if not name:
            continue
        suffix = f" ({detail})" if detail else ""
        lines.append(f"{index}. {name}{suffix}")

    if not lines:
        return "Trending unavailable from Xquik."
    return "Trending Topics:\n" + "\n".join(lines)


def _request_json(path: str, params: dict[str, object]) -> dict[str, Any]:
    api_key = os.environ.get(API_KEY_ENV)
    if not api_key:
        raise XquikError(f"Set {API_KEY_ENV} to use the Xquik backend.")

    query = urllib.parse.urlencode(
        {key: value for key, value in params.items() if value not in (None, "")},
    )
    base_url = os.environ.get(BASE_URL_ENV, DEFAULT_BASE_URL).rstrip("/")
    url = f"{base_url}/api/v1{path}"
    if query:
        url = f"{url}?{query}"

    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "x-api-key": api_key,
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=REQUEST_TIMEOUT_SECONDS,
        ) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        payload = error.read().decode("utf-8", errors="replace")
        message = _error_message(payload) or error.reason or "request failed"
        raise XquikError(f"Xquik request failed ({error.code}): {message}") from error
    except urllib.error.URLError as error:
        raise XquikError(f"Xquik request failed: {error.reason}") from error

    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as error:
        raise XquikError("Xquik returned invalid JSON.") from error

    if not isinstance(parsed, dict):
        raise XquikError("Xquik returned an unexpected response.")
    return parsed


def _error_message(payload: str) -> str:
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        return payload.strip()
    if not isinstance(parsed, dict):
        return payload.strip()
    message = parsed.get("message") or parsed.get("error")
    return str(message) if message else payload.strip()


def _tweet_list(data: dict[str, Any]) -> list[dict[str, Any]]:
    tweets = data.get("tweets", [])
    if not isinstance(tweets, list):
        return []
    return [tweet for tweet in tweets if isinstance(tweet, dict)]


def _format_tweets(tweets: list[dict[str, Any]]) -> str:
    rows: list[str] = []
    for index, tweet in enumerate(tweets, 1):
        author = tweet.get("author")
        author_data = author if isinstance(author, dict) else {}
        author_name = _field(author_data, "name", default="Unknown")
        username = _field(author_data, "username", "screenName", default="")
        handle = f"@{username}" if username else "Unknown"
        text = _field(tweet, "text", "fullText", default="")
        timestamp = _field(tweet, "createdAt", "created_at", default="Unknown")
        replies = _field(tweet, "replyCount", "reply_count", default=0)
        retweets = _field(tweet, "retweetCount", "retweet_count", default=0)
        likes = _field(tweet, "likeCount", "like_count", default=0)
        rows.append(
            f"{index}. Author: {author_name}\n"
            f"   Handle: {handle}\n"
            f"   Text: {text}\n"
            f"   Timestamp: {timestamp}\n"
            f"   Replies: {replies}, Retweets: {retweets}, Likes: {likes}\n",
        )
    return "\n".join(rows)


def _format_profile(profile: dict[str, Any], fallback_username: str) -> str:
    username = _field(profile, "username", default=_clean_username(fallback_username))
    name = _field(profile, "name", default=username)
    bio = _field(profile, "description", "bio", default="No bio")
    followers = _field(profile, "followers", "followersCount", default="?")
    following = _field(profile, "following", "followingCount", default="?")
    return (
        f"Name: {name}\n"
        f"Username: @{username}\n"
        f"Bio: {bio}\n"
        f"Followers: {followers}\n"
        f"Following: {following}"
    )


def _field(data: dict[str, Any], *names: str, default: object) -> object:
    for name in names:
        value = data.get(name)
        if value not in (None, ""):
            return value
    return default


def _clean_username(username: str) -> str:
    return username.strip().lstrip("@")


def _quote_path(value: str) -> str:
    return urllib.parse.quote(value, safe="")

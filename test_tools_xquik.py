import os
import unittest
from unittest.mock import patch

import tools_xquik


class XquikToolsTest(unittest.TestCase):
    def test_search_formats_tweets(self):
        with patch.dict(os.environ, {"XQUIK_API_KEY": "test"}, clear=True):
            with patch.object(
                tools_xquik,
                "_request_json",
                return_value={
                    "tweets": [
                        {
                            "text": "hello",
                            "createdAt": "2026-01-01T00:00:00Z",
                            "replyCount": 1,
                            "retweetCount": 2,
                            "likeCount": 3,
                            "author": {"name": "Ada", "username": "ada"},
                        },
                    ],
                },
            ):
                result = tools_xquik.xquik_search_tweets("hello", 1)

        self.assertIn("Author: Ada", result)
        self.assertIn("Handle: @ada", result)
        self.assertIn("Replies: 1, Retweets: 2, Likes: 3", result)

    def test_user_tweets_resolves_username_before_timeline(self):
        calls = []

        def fake_request(path, params):
            calls.append((path, params))
            if path == "/x/users/ada":
                return {"id": "123", "username": "ada"}
            return {
                "tweets": [
                    {
                        "text": "post",
                        "author": {"name": "Ada", "username": "ada"},
                    },
                ],
            }

        with patch.dict(os.environ, {"XQUIK_API_KEY": "test"}, clear=True):
            with patch.object(tools_xquik, "_request_json", side_effect=fake_request):
                result = tools_xquik.xquik_user_tweets("@ada", 1)

        self.assertEqual(calls[0], ("/x/users/ada", {}))
        self.assertEqual(calls[1], ("/x/users/123/tweets", {}))
        self.assertIn("Tweets from ada:", result)


if __name__ == "__main__":
    unittest.main()

# INF601 - Advanced Programming in Python
# Hosia Stokes Jr
# Mini Project 7

"""Offline tests for server.py.

These tests replace httpx.request with a fake Practice Hub, so they never
contact the real API and never need a real token. Run them with:

    python -m unittest -v
"""

import asyncio
import os
import unittest
from unittest import mock

import httpx

# Fake settings must exist before server.py is imported.
os.environ["PRACTICE_API_URL"] = "https://practice.example/"
os.environ["PRACTICE_API_TOKEN"] = "fake-test-token"

import server  # noqa: E402
from mcp.server.fastmcp.exceptions import ToolError  # noqa: E402

POST = {"id": 7, "title": "Hello", "body": "Hi", "tags": ["python"],
        "author_id": 14, "author_name": "Test User",
        "created_at": "2026-11-14T00:00:00Z", "updated_at": "2026-11-14T00:00:00Z",
        "attachments": []}


class FakeAPI:
    """Stands in for httpx.request and remembers every call made to it."""

    def __init__(self, status=200, json=None, text=None, error=None):
        self.status, self.json, self.text, self.error = status, json, text, error
        self.calls = []

    def __call__(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        if self.error:
            raise self.error
        request = httpx.Request(method, url)
        if self.json is not None:
            return httpx.Response(self.status, json=self.json, request=request)
        return httpx.Response(self.status, text=self.text or "", request=request)


class ServerTests(unittest.TestCase):

    def use(self, **kwargs):
        """Install a FakeAPI for the rest of this test and return it."""
        fake = FakeAPI(**kwargs)
        patcher = mock.patch.object(server.httpx, "request", fake)
        patcher.start()
        self.addCleanup(patcher.stop)
        return fake

    # --- settings and registration -------------------------------------

    def test_trailing_slash_removed_from_base_url(self):
        self.assertEqual(server.BASE, "https://practice.example")

    def test_all_five_tools_registered(self):
        names = {t.name for t in asyncio.run(server.mcp.list_tools())}
        self.assertEqual(names, {"list_posts", "get_post", "create_post",
                                 "update_post", "delete_post"})

    # --- happy paths ----------------------------------------------------

    def test_list_posts_sends_token_and_mine_flag(self):
        fake = self.use(json=[POST])
        self.assertEqual(server.list_posts(mine=True), [POST])
        method, url, kw = fake.calls[0]
        self.assertEqual((method, url), ("GET", "https://practice.example/api/v1/posts"))
        self.assertEqual(kw["params"], {"mine": True})
        self.assertEqual(kw["headers"], {"Authorization": "Bearer fake-test-token"})

    def test_list_posts_defaults_to_all_posts(self):
        fake = self.use(json=[])
        server.list_posts()
        self.assertEqual(fake.calls[0][2]["params"], {"mine": False})

    def test_get_post(self):
        fake = self.use(json=POST)
        self.assertEqual(server.get_post(7), POST)
        self.assertEqual(fake.calls[0][:2], ("GET", "https://practice.example/api/v1/posts/7"))

    def test_create_post_with_tags(self):
        fake = self.use(status=201, json=POST)
        self.assertEqual(server.create_post("Hello", "Hi", ["python"]), POST)
        method, url, kw = fake.calls[0]
        self.assertEqual((method, url), ("POST", "https://practice.example/api/v1/posts"))
        self.assertEqual(kw["json"], {"title": "Hello", "body": "Hi", "tags": ["python"]})

    def test_create_post_without_tags_omits_them(self):
        fake = self.use(status=201, json=POST)
        server.create_post("Hello")
        self.assertEqual(fake.calls[0][2]["json"], {"title": "Hello", "body": ""})

    def test_update_post_sends_only_changed_fields_with_patch(self):
        fake = self.use(json={**POST, "title": "New"})
        self.assertEqual(server.update_post(7, title="New")["title"], "New")
        method, url, kw = fake.calls[0]
        self.assertEqual((method, url), ("PATCH", "https://practice.example/api/v1/posts/7"))
        self.assertEqual(kw["json"], {"title": "New"})

    def test_delete_post_handles_204_no_content(self):
        fake = self.use(status=204)
        self.assertEqual(server.delete_post(7), "Post 7 was deleted.")
        self.assertEqual(fake.calls[0][:2], ("DELETE", "https://practice.example/api/v1/posts/7"))

    # --- input checks (no API call made) --------------------------------

    def test_create_post_rejects_empty_title(self):
        fake = self.use(json=POST)
        with self.assertRaisesRegex(ToolError, "title"):
            server.create_post("   ")
        self.assertEqual(fake.calls, [])

    def test_update_post_with_nothing_to_change(self):
        fake = self.use(json=POST)
        with self.assertRaisesRegex(ToolError, "Nothing to update"):
            server.update_post(7)
        self.assertEqual(fake.calls, [])

    # --- API errors become clear messages --------------------------------

    def assert_tool_error(self, call, pattern):
        with self.assertRaisesRegex(ToolError, pattern) as ctx:
            call()
        self.assertNotIn("fake-test-token", str(ctx.exception))

    def test_401_authentication_error(self):
        self.use(status=401, json={"detail": "Invalid token"})
        self.assert_tool_error(server.list_posts, r"Authentication failed \(401\)")

    def test_403_not_your_post(self):
        self.use(status=403, json={"detail": "Forbidden"})
        self.assert_tool_error(lambda: server.delete_post(3), r"\(403\): post 3 belongs to another user")

    def test_404_missing_post(self):
        self.use(status=404, json={"detail": "Not found"})
        self.assert_tool_error(lambda: server.get_post(999), r"\(404\): post 999 does not exist")

    def test_422_shows_api_validation_message(self):
        self.use(status=422, json={"detail": [{"loc": ["body", "title"],
                                               "msg": "Field required"}]})
        self.assert_tool_error(lambda: server.create_post("x"), r"\(422\): Field required")

    def test_other_http_error(self):
        self.use(status=500, text="Internal Server Error")
        self.assert_tool_error(lambda: server.get_post(1), r"API error 500: Internal Server Error")

    def test_connection_failure(self):
        self.use(error=httpx.ConnectError("refused"))
        self.assert_tool_error(server.list_posts, r"Could not connect to Practice Hub")

    def test_timeout(self):
        self.use(error=httpx.ReadTimeout("slow"))
        self.assert_tool_error(server.list_posts, r"did not respond within 15 seconds")

    def test_non_json_success_response(self):
        self.use(status=200, text="<html>oops</html>")
        self.assert_tool_error(lambda: server.get_post(1), r"not JSON")


if __name__ == "__main__":
    unittest.main()

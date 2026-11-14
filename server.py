# INF601 - Advanced Programming in Python
# Hosia Stokes Jr
# Mini Project 7

"""FastMCP server that lets Claude Code work with Practice Hub posts.

Settings come from environment variables so the API token never
appears in this file:

    PRACTICE_API_URL    for example https://practice.fhsucyber.com
    PRACTICE_API_TOKEN  your personal Practice Hub API token
"""

import os, httpx
import sys
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

# Read settings once at startup. A missing variable stops the server with
# a clear message instead of a confusing KeyError traceback.
try:
    BASE = os.environ["PRACTICE_API_URL"].strip().rstrip("/")
    TOKEN = os.environ["PRACTICE_API_TOKEN"].strip()
except KeyError as missing:
    sys.exit(f"Missing environment variable {missing}. "
             "Set PRACTICE_API_URL and PRACTICE_API_TOKEN before starting the server.")
if not BASE or not TOKEN:
    sys.exit("PRACTICE_API_URL and PRACTICE_API_TOKEN must not be empty.")

mcp = FastMCP("practice-hub")

TIMEOUT = 15.0  # seconds to wait for Practice Hub before giving up


def _error_detail(r: httpx.Response) -> str:
    """Return the API's own error message from a failed response, if any."""
    try:
        data = r.json()
    except ValueError:
        return r.text.strip()[:200] or r.reason_phrase
    detail = data.get("detail", data) if isinstance(data, dict) else data
    if isinstance(detail, list):  # validation errors often arrive as a list
        return "; ".join(str(item.get("msg", item)) if isinstance(item, dict)
                         else str(item) for item in detail)
    return str(detail)[:200]


def _request(method: str, path: str, what: str, **kwargs) -> httpx.Response:
    """Send one authenticated request and turn failures into clear errors.

    `what` describes the thing being requested (for example "post 12") so
    error messages can say exactly what went wrong. Raising ToolError makes
    FastMCP send Claude a readable error message, and the server keeps
    running for the next tool call. The token is never included in errors.
    """
    try:
        r = httpx.request(method, f"{BASE}{path}",
                          headers={"Authorization": f"Bearer {TOKEN}"},
                          timeout=TIMEOUT, **kwargs)
    except httpx.TimeoutException:
        raise ToolError(f"Practice Hub did not respond within {TIMEOUT:g} seconds. "
                        "Try again in a moment.")
    except httpx.RequestError as e:
        raise ToolError(f"Could not connect to Practice Hub at {BASE} "
                        f"({type(e).__name__}). Check PRACTICE_API_URL and your "
                        "internet connection.")

    if r.status_code == 401:
        raise ToolError("Authentication failed (401): the API token is missing, "
                        "invalid, or expired. Check PRACTICE_API_TOKEN.")
    if r.status_code == 403:
        raise ToolError(f"Permission denied (403): {what} belongs to another user. "
                        "You can only update or delete your own posts.")
    if r.status_code == 404:
        raise ToolError(f"Not found (404): {what} does not exist.")
    if r.status_code == 422:
        raise ToolError(f"Practice Hub rejected the data (422): {_error_detail(r)}")
    if r.is_error:
        raise ToolError(f"Practice Hub API error {r.status_code}: {_error_detail(r)}")
    return r


def _json(r: httpx.Response):
    """Decode a successful response body, with a clear error if it is not JSON."""
    try:
        return r.json()
    except ValueError:
        raise ToolError(f"Practice Hub returned a response that is not JSON "
                        f"(HTTP {r.status_code}).")


@mcp.tool()
def list_posts(mine: bool = False) -> list[dict]:
    """List posts; set mine=True for only your own.

    Returns up to 50 posts, newest first. Each post has id, title, body,
    tags, author_id, author_name, created_at, updated_at, and attachments.
    """
    r = _request("GET", "/api/v1/posts", "the post list", params={"mine": mine})
    return _json(r)


@mcp.tool()
def get_post(post_id: int) -> dict:
    """Get one post by its ID.

    Returns the post's id, title, body, tags, author_id, author_name,
    created_at, updated_at, and attachments.
    """
    r = _request("GET", f"/api/v1/posts/{post_id}", f"post {post_id}")
    return _json(r)


@mcp.tool()
def create_post(title: str, body: str = "", tags: list[str] | None = None) -> dict:
    """Create a new post owned by you.

    title is required. body is optional text (Markdown is fine). tags is
    an optional list of strings, for example ["python", "api"].
    Returns the new post, including its id.
    """
    if not title.strip():
        raise ToolError("A post needs a title; title cannot be empty.")
    payload = {"title": title, "body": body}
    if tags is not None:
        payload["tags"] = tags
    r = _request("POST", "/api/v1/posts", "the new post", json=payload)
    return _json(r)


@mcp.tool()
def update_post(post_id: int, title: str | None = None, body: str | None = None,
                tags: list[str] | None = None) -> dict:
    """Update one of your own posts.

    Only the fields you pass are changed (title, body, and/or tags); the
    rest stay as they are. Returns the updated post. You cannot update
    posts that belong to other users.
    """
    changes = {}
    if title is not None:
        if not title.strip():
            raise ToolError("title cannot be empty; leave it out to keep the current title.")
        changes["title"] = title
    if body is not None:
        changes["body"] = body
    if tags is not None:
        changes["tags"] = tags
    if not changes:
        raise ToolError("Nothing to update: pass at least one of title, body, or tags.")
    r = _request("PATCH", f"/api/v1/posts/{post_id}", f"post {post_id}", json=changes)
    return _json(r)


@mcp.tool()
def delete_post(post_id: int) -> str:
    """Permanently delete one of your own posts by its ID.

    This cannot be undone. You cannot delete posts that belong to other users.
    """
    _request("DELETE", f"/api/v1/posts/{post_id}", f"post {post_id}")
    return f"Post {post_id} was deleted."


if __name__ == "__main__":
    # stdio transport: Claude Code starts this script and talks to it
    # over standard input/output.
    mcp.run(transport="stdio")

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

# ...add get_post, create_post, update_post, delete_post

if __name__ == "__main__":
    mcp.run()

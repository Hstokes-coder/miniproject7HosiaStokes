# INF601 - Advanced Programming in Python
# Hosia Stokes Jr
# Mini Project 7

import os, httpx
from mcp.server.fastmcp import FastMCP

BASE = os.environ["PRACTICE_API_URL"]
TOKEN = os.environ["PRACTICE_API_TOKEN"]
mcp = FastMCP("practice-hub")

@mcp.tool()
def list_posts(mine: bool = False) -> list[dict]:
    """List posts; set mine=True for only your own."""
    r = httpx.get(f"{BASE}/api/v1/posts", params={"mine": mine},
                  headers={"Authorization": f"Bearer {TOKEN}"})
    r.raise_for_status()
    return r.json()

# ...add get_post, create_post, update_post, delete_post

if __name__ == "__main__":
    mcp.run()

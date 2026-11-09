import json
from typing import Any

import httpx2
from mcp.server import MCPServer

# Initialize MCPServer
mcp = MCPServer("music-dl")

API_BASE = "http://127.0.0.1:8000"
USER_AGENT = "weather-app/1.0"

async def search_videos(title: str, max_num: int) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    url = f"{API_BASE}/search/videos"
    request_body = {
        "page_size": max_num,
        "page_number": 0,
        "name": title
    }
    async with httpx2.AsyncClient() as client:
        try:

            response = await client.post(url,json=request_body, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()

        except Exception as e:
          return {"error": f"{type(e).__name__}: {e}"}


@mcp.tool()
async def claude_get_videos(title: str, max_num: int) -> str:
    """List youtube videos.

    Args:
        title: Video title to search for.
        max_num: Than number of videos returned by the search
    """
    data = await search_videos(title,max_num)

    if data is None:
        return "Search failed."
    return json.dumps(data, indent=2)

if __name__ == "__main__":
    mcp.run(transport="stdio")
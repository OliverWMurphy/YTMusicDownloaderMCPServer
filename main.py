import json
import logging
from pathlib import Path
from typing import Any

import httpx2
from mcp.server import MCPServer
from pathvalidate import sanitize_filename

# Initialize MCPServer
mcp = MCPServer("music-dl") 

logger = logging.getLogger(__name__)
API_BASE = "http://127.0.0.1:8000"
USER_AGENT = "music-dl/1.0"
DOWNLOAD_DIR = Path("~/Music/claude")

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
        
async def download_audio(video_id: str) -> dict[str, Any] | None:
    """Download a video to disk and return its location."""
    try:
        async with httpx2.AsyncClient() as client, client.stream("GET", f"{API_BASE}/video/single/{video_id}", timeout=240.0) as r:
            r.raise_for_status()
            ctype = r.headers.get("content-type", "")
            filename = sanitize_filename(r.headers.get("content-disposition", video_id))

            if not ctype.startswith("video/mp4"):
                return f"Unexpected content type: {ctype}"
            
            DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
            dest = DOWNLOAD_DIR / Path(filename)

            logger.info(f"dest: {dest}")

            with dest.open("wb") as f:
                async for chunk in r.aiter_bytes():
                    f.write(chunk)
            return {"success": True}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}

@mcp.tool()
async def claude_download_audio(video_id) -> str:
    """Download the audio of a youtube video.

    Args:
        video_id: The id of a youtube video. This the value of the query param v.
        for example, the id for https://www.youtube.com/watch?v=NAh9oLs67Cw is NAh9oLs67Cw
    """
    data = await download_audio(video_id)

    if data is None:
        return "Download failed."
    return json.dumps(data, indent=1)


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
    return json.dumps(data, indent=1)

if __name__ == "__main__":
    mcp.run(transport="stdio")
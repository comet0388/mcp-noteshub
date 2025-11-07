from fastapi import FastAPI, Query
from utils.rag_helper import get_relevant_chunks
from typing import Dict, Any
import random

# ---------------------------------------------------
# 🚀 FastAPI App Initialization
# ---------------------------------------------------
app = FastAPI(
    title="MCP NotesHub Server",
    description="Backend for contextual note retrieval and quiz generation.",
    version="2.0.0"
)

# ---------------------------------------------------
# 🧠 Global Cache
# ---------------------------------------------------
# Stores active sessions in memory
# Structure:
# {
#   "cache_id": {
#       "file": str or None,
#       "topic": str or None,
#       "chunks": [str],
#       "served": set()
#   }
# }
chunk_cache: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------
# 🔹 1. Get or Create Chunk Session
# ---------------------------------------------------
@app.get("/tools/query")
def get_chunk(
    file: str | None = Query(None, description="Name of the note file (optional)"),
    topic: str | None = Query(None, description="Topic keyword to query (optional)")
):
    """
    Retrieve a random chunk from cache if available.
    Otherwise, build chunks using RAG helper and cache them.
    """
    cache_key = f"{file or 'none'}::{topic or 'none'}"

    # 🧠 Step 1: If cache exists, return a random unused chunk
    if cache_key in chunk_cache:
        session = chunk_cache[cache_key]
        remaining = [c for i, c in enumerate(session["chunks"]) if i not in session["served"]]

        # If no remaining chunks → clear cache
        if not remaining:
            del chunk_cache[cache_key]
            return {"message": "🧹 All chunks served. Cache cleared."}

        # Pick one randomly
        chunk = random.choice(remaining)
        chunk_index = session["chunks"].index(chunk)
        session["served"].add(chunk_index)

        return {
            "mode": session["mode"],
            "file": session["file"],
            "topic": session["topic"],
            "chunk_index": chunk_index + 1,
            "chunk": chunk,
            "remaining": len(remaining) - 1,
            "message": "✅ Served from cache."
        }

    # 🧠 Step 2: If cache doesn’t exist, build it using rag_helper
    try:
        result = get_relevant_chunks(file_name=file, topic=topic)
        chunks = result.get("context_chunks", [])
        if not chunks:
            return {"message": "⚠️ No relevant chunks found.", "mode": result.get("mode")}

        chunk_cache[cache_key] = {
            "file": file,
            "topic": topic,
            "chunks": chunks,
            "served": set(),
            "mode": result.get("mode")
        }

        # Immediately serve the first random chunk
        first_chunk = random.choice(chunks)
        chunk_cache[cache_key]["served"].add(chunks.index(first_chunk))

        return {
            "mode": result.get("mode"),
            "file": file,
            "topic": topic,
            "chunk": first_chunk,
            "remaining": len(chunks) - 1,
            "message": "🆕 Cache created and first chunk served."
        }

    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------
# 🔹 2. Manually Clear Cache
# ---------------------------------------------------
@app.get("/tools/clear")
def clear_cache(
    file: str | None = Query(None, description="Name of the note file (optional)"),
    topic: str | None = Query(None, description="Topic name (optional)")
):
    """
    Clear the cache manually for a given file/topic combination.
    """
    cache_key = f"{file or 'none'}::{topic or 'none'}"
    if cache_key in chunk_cache:
        del chunk_cache[cache_key]
        return {"message": f"🧹 Cache cleared for query ({file or '*'}, {topic or '*'})"}
    return {"message": "No cache found to clear."}


# ---------------------------------------------------
# 🔹 3. Stop Session (for quiz termination)
# ---------------------------------------------------
@app.get("/tools/stop")
def stop_session(
    file: str | None = Query(None),
    topic: str | None = Query(None)
):
    """
    Stop the current quiz session and clear its cache.
    """
    cache_key = f"{file or 'none'}::{topic or 'none'}"
    if cache_key in chunk_cache:
        del chunk_cache[cache_key]
        return {"message": "🛑 Session stopped and cache cleared."}
    return {"message": "No active session to stop."}


# ---------------------------------------------------
# 🔹 4. Debug Cache State
# ---------------------------------------------------
@app.get("/tools/status")
def cache_status():
    """
    Show current cache contents for debugging.
    """
    if not chunk_cache:
        return {"cache": "empty"}
    return {
        "active_caches": {
            key: {
                "mode": data["mode"],
                "file": data["file"],
                "topic": data["topic"],
                "total_chunks": len(data["chunks"]),
                "served": len(data["served"]),
                "remaining": len(data["chunks"]) - len(data["served"])
            }
            for key, data in chunk_cache.items()
        }
    }


# ---------------------------------------------------
# 🔹 5. Root Endpoint
# ---------------------------------------------------
@app.get("/")
def root():
    return {
        "message": "🚀 MCP NotesHub server is running!",
        "available_endpoints": [
            "/tools/query?file=&topic=",
            "/tools/clear",
            "/tools/stop",
            "/tools/status"
        ]
    }

from fastapi.responses import FileResponse
import os

@app.get("/mcp-manifest.json", include_in_schema=False)
def manifest():
    """
    Serve the MCP manifest file for ChatGPT plugin registration.
    """
    manifest_path = os.path.join(os.path.dirname(__file__), "mcp-manifest.json")
    if not os.path.exists(manifest_path):
        return {"error": "manifest file not found"}
    return FileResponse(manifest_path, media_type="application/json")


"""
db_handler.py
-------------
ChromaDB operations for the video analysis pipeline.

Metadata stored per frame:
  video_uuid, video_filename, frame_name, frame_id, timestamp, smart_name
"""

import logging
from typing import List

import chromadb


class DBHandler:
    """Handles ChromaDB operations."""

    def __init__(
        self,
        host: str,
        port: int,
        collection_name: str = "Video_Embeddings",
    ) -> None:
        try:
            self.client = chromadb.HttpClient(host=host, port=port)
            # Quick connectivity probe
            self.client.heartbeat()
            logging.info("Connected to ChromaDB at %s:%d", host, port)
        except Exception:
            logging.warning(
                "Could not connect to ChromaDB HTTP server. "
                "Falling back to local PersistentClient."
            )
            self.client = chromadb.PersistentClient(path="./chroma_db")

        self.collection = self.client.get_or_create_collection(name=collection_name)

    # ──────────────────────────────────────────────────────────
    # Write
    # ──────────────────────────────────────────────────────────

    def add_entry(
        self,
        video_uuid: str,
        video_filename: str,
        frame_name: str,
        frame_id: str,
        timestamp: float,
        description: str,
        embedding: List[float],
        position: str = "",
        smart_name: str = "",
    ) -> None:
        """
        Store one frame embedding + full metadata in ChromaDB.

        Metadata fields
        ---------------
        video_uuid, video_filename, frame_name, frame_id,
        timestamp (seconds), position (beginning/middle/end),
        smart_name, filename_plus_uuid
        """
        self.collection.add(
            ids=[f"{video_uuid}_{frame_name}"],
            embeddings=[embedding],
            documents=[description],
            metadatas=[
                {
                    "video_uuid": video_uuid,
                    "video_filename": video_filename,
                    "frame_name": frame_name,
                    "frame_id": frame_id,
                    "timestamp": timestamp,
                    "position": position,
                    "smart_name": smart_name,
                    "filename_plus_uuid": f"{video_filename}_{video_uuid}",
                }
            ],
        )

    # ──────────────────────────────────────────────────────────
    # Read
    # ──────────────────────────────────────────────────────────

    def query(
        self,
        query_embedding: List[float],
        video_uuid: str,
        n_results: int = 10,
    ) -> dict:
        """Return top-n results for the given embedding, filtered by video_uuid."""
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where={"video_uuid": video_uuid},
            include=["documents", "metadatas"],
        )

    # ──────────────────────────────────────────────────────────
    # Delete
    # ──────────────────────────────────────────────────────────

    def delete_video(self, video_uuid: str) -> None:
        """Remove all embeddings associated with a video."""
        self.collection.delete(where={"video_uuid": video_uuid})

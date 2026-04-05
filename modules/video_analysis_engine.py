"""
video_analysis_engine.py
------------------------
Orchestrates the full video analysis pipeline:
  Phase 1 – stream frames → DINO similarity filter → keyframes
  Phase 2 – describe ALL keyframes concurrently via OpenAI (asyncio.gather)
  Phase 3 – build canonical frame-JSON, embed descriptions, store in ChromaDB + SQLite
  Phase 4 – generate smart video title

query_video  – embed query → ChromaDB lookup → pass ALL metadata to LLM → answer
"""

import asyncio
import io
import json
import logging
import os
import sqlite3
import uuid
from typing import Any, Dict, List

from .ai_handler import AIHandler
from .db_handler import DBHandler
from .dino_handler import DINOHandler
from .sqlite_handler import SQLiteHandler
from .video_processor import VideoProcessor


class VideoAnalysisEngine:
    """Orchestrates the video analysis process."""

    def __init__(self) -> None:
        self.video_processor = VideoProcessor()
        self.ai_handler = AIHandler()
        self.db_handler = DBHandler(
            host=os.getenv("CHROMADB_HOST", "localhost"),
            port=int(os.getenv("CHROMADB_PORT", 8000)),
        )
        self.sqlite_handler = SQLiteHandler()
        self.dino_handler = DINOHandler()

    # ──────────────────────────────────────────────────────────────────────────
    # Process  (async)
    # ──────────────────────────────────────────────────────────────────────────

    async def process_video(self, video_path: str) -> Dict[str, Any]:
        """
        End-to-end async video processing pipeline.

        Returns
        -------
        {
            "video_uuid":   str,
            "smart_title":  str,
            "frame_json":   List[dict],   # sorted frame records
        }
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        video_filename = os.path.basename(video_path)
        video_uuid = str(uuid.uuid4())
        logging.info("Processing video: %s (UUID: %s)", video_filename, video_uuid)

        self.sqlite_handler.add_video(video_uuid, video_filename, "Processing…")

        # ── Phase 1: stream frames → DINO filter → keyframes ─────────────────
        logging.info("Streaming and filtering frames (DINO similarity)…")

        DINO_BATCH = 8          # inference batch size
        frame_batch = []
        keyframes: List = []    # list of (PIL.Image, timestamp, frame_name)
        current_base_emb = None

        def _dino_filter_batch(batch):
            nonlocal current_base_emb
            images = [f[0] for f in batch]
            timestamps = [f[1] for f in batch]
            embeddings = self.dino_handler.get_embeddings_batch(images)
            if embeddings is None:
                return
            for i, emb in enumerate(embeddings):
                if current_base_emb is not None:
                    sim = self.dino_handler.compute_similarity(current_base_emb, emb)
                    if sim >= 0.90:
                        continue   # redundant frame – skip
                current_base_emb = emb
                ts = timestamps[i]
                name = f"frame_{ts:.2f}"
                logging.info("Selected keyframe at %.2fs", ts)
                keyframes.append((images[i], ts, name))

        for pil_image, timestamp in self.video_processor.stream_frames(video_path):
            frame_batch.append((pil_image, timestamp))
            if len(frame_batch) >= DINO_BATCH:
                _dino_filter_batch(frame_batch)
                frame_batch = []
        if frame_batch:
            _dino_filter_batch(frame_batch)

        logging.info("Keyframes selected: %d", len(keyframes))

        # ── Phase 2: describe ALL keyframes concurrently ──────────────────────
        logging.info("Describing keyframes via OpenAI (concurrent)…")
        raw_descriptions: List[Dict] = await self.ai_handler.describe_all_images_async(
            keyframes
        )

        # Build the canonical frame-JSON (sorted by frame_name)
        frame_json: List[Dict] = self.ai_handler.build_frame_json(
            keyframes, raw_descriptions, video_filename
        )

        # Also build a simple {frame_name: description} mapping for title gen
        desc_map: Dict[str, str] = {
            rec["frame_name"]: rec["description"] for rec in frame_json
        }

        # ── Phase 3: persist each frame ──────────────────────────────────────
        logging.info("Persisting %d frames to SQLite + ChromaDB…", len(frame_json))

        # Determine total video duration so we can label each frame's position.
        # frame_json is sorted by frame_name, so the last entry has the max timestamp.
        max_ts: float = frame_json[-1]["time_stamp"] if frame_json else 1.0

        def _temporal_label(ts: float, total: float) -> str:
            """Map a timestamp to a human-readable position in the video."""
            if total <= 0:
                return "beginning"
            ratio = ts / total
            if ratio < 0.33:
                return "beginning"
            elif ratio < 0.67:
                return "middle"
            else:
                return "end"

        for record in frame_json:
            frame_name  = record["frame_name"]
            timestamp   = record["time_stamp"]
            description = record["description"]
            position    = _temporal_label(timestamp, max_ts)

            # Find the matching PIL image (needed for SQLite thumbnail)
            matching = [kf for kf in keyframes if kf[2] == frame_name]
            if matching:
                pil_image = matching[0][0]
                img_buf   = io.BytesIO()
                pil_image.save(img_buf, format="JPEG", quality=70)
                img_bytes = img_buf.getvalue()
            else:
                img_bytes = b""

            # SQLite
            frame_id = self.sqlite_handler.add_frame(
                video_uuid, timestamp, description, img_bytes
            )

            # ChromaDB – embed ALL fields including temporal position so queries
            # like "what happened at the beginning / middle / end" resolve correctly.
            enriched_text = (
                f"[File: {video_filename}] "
                f"[Frame: {frame_name}] "
                f"[Time: {timestamp:.2f}s] "
                f"[Position in video: {position}] "
                f"{description}"
            )
            embedding = self.ai_handler.get_embedding(enriched_text)

            self.db_handler.add_entry(
                video_uuid=video_uuid,
                video_filename=video_filename,
                frame_name=frame_name,
                frame_id=str(frame_id),
                timestamp=timestamp,
                position=position,
                description=enriched_text,
                embedding=embedding,
            )

        # ── Phase 4: smart title ─────────────────────────────────────────────
        logging.info("Generating smart title…")
        smart_title = await self.ai_handler.generate_smart_title_async(desc_map)
        logging.info("Smart Title: %s", smart_title)

        # Update title in SQLite
        conn = sqlite3.connect(self.sqlite_handler.db_path)
        conn.execute(
            "UPDATE videos SET smart_title = ? WHERE uuid = ?",
            (smart_title, video_uuid),
        )
        conn.commit()
        conn.close()

        logging.info("Processing complete. UUID=%s  title=%s", video_uuid, smart_title)

        return {
            "video_uuid": video_uuid,
            "smart_title": smart_title,
            "frame_json": frame_json,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Query  (async)
    # ──────────────────────────────────────────────────────────────────────────

    async def query_video(self, video_uuid: str, query_text: str) -> str:
        """
        Embed query → ChromaDB retrieval → format ALL metadata → LLM answer.
        """
        logging.info("Querying video %s: %s", video_uuid, query_text)

        query_embedding = self.ai_handler.get_embedding(query_text)
        results = self.db_handler.query(query_embedding, video_uuid)

        # Build rich context string: include all metadata fields for the LLM
        context_parts: List[str] = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]

        for doc, meta in zip(docs, metas):
            entry_lines = [
                f"• Filename   : {meta.get('video_filename', 'N/A')}",
                f"  Frame      : {meta.get('frame_name', 'N/A')}",
                f"  Timestamp  : {meta.get('timestamp', 'N/A')}s",
                f"  Position   : {meta.get('position', 'N/A')} of video",
                f"  Frame ID   : {meta.get('frame_id', 'N/A')}",
                f"  Description: {doc}",
            ]
            context_parts.append("\n".join(entry_lines))

        context_data = "\n\n".join(context_parts) or "No relevant frames found."

        return await self.ai_handler.answer_query_async(query_text, context_data)

    # ──────────────────────────────────────────────────────────────────────────
    # Helper – run async pipeline from sync callers (e.g. Streamlit)
    # ──────────────────────────────────────────────────────────────────────────

    def process_video_sync(self, video_path: str) -> Dict[str, Any]:
        """Synchronous wrapper for process_video (useful in non-async contexts)."""
        return asyncio.run(self.process_video(video_path))

    def query_video_sync(self, video_uuid: str, query_text: str) -> str:
        """Synchronous wrapper for query_video."""
        return asyncio.run(self.query_video(video_uuid, query_text))

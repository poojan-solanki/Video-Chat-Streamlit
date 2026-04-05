"""
ai_handler.py
-------------
Handles all OpenAI API interactions for the video analysis pipeline.

Public API
----------
  async describe_image_async(image, filename, timestamp) -> str
  async describe_all_images_async(keyframes)             -> List[dict]
        keyframes: list of (PIL.Image, timestamp: float, frame_name: str)
        returns : list of {frame_name, timestamp, description}

  build_frame_json(keyframes, descriptions, video_filename) -> List[dict]
        builds and sorts the canonical per-frame JSON record

  async generate_smart_title_async(descriptions_dict)    -> str
  async answer_query_async(query, context_data)          -> str
  get_embedding(text)                                    -> List[float]  (sync)
"""

import asyncio
import base64
import json
import logging
import os
from io import BytesIO
from typing import Dict, List, Tuple

from openai import AsyncOpenAI
from PIL import Image
from sentence_transformers import SentenceTransformer

from dotenv import load_dotenv

load_dotenv()


class AIHandler:
    """
    Async OpenAI handler using gpt-4.1 for vision + chat tasks,
    and SentenceTransformer for local embeddings.
    """

    MODEL = "gpt-4.1"

    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set in environment / .env file")

        self.client: AsyncOpenAI = AsyncOpenAI(api_key=api_key)

        logging.info("Loading SentenceTransformer embedding model…")
        self.embedding_model = SentenceTransformer("google/embeddinggemma-300m")
        logging.info("AIHandler ready (model=%s)", self.MODEL)

    # ──────────────────────────────────────────────────────────────────────────
    # Vision – single frame
    # ──────────────────────────────────────────────────────────────────────────

    async def describe_image_async(
        self,
        image: Image.Image,
        filename: str,
        timestamp: float,
    ) -> str:
        """
        Describe a single video frame using GPT-4.1 vision (chat.completions).

        Returns a plain-text description string.
        """
        # Encode PNG → JPEG → base64
        buf = BytesIO()
        image.save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        prompt = (
            f"You are analyzing a video frame extracted at timestamp {timestamp:.2f}s "
            f"(frame file: {filename}).\n"
            "Describe what you see in detail, focusing on:\n"
            "• People, objects, and their actions\n"
            "• Location / environment cues\n"
            "• Any unusual, suspicious, or noteworthy activity\n"
            "Be concise but specific."
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{b64}",
                                    "detail": "auto",
                                },
                            },
                        ],
                    }
                ],
                max_tokens=400,
                temperature=0.2,
            )
            description = response.choices[0].message.content or ""
            logging.info("Described frame %s (%.2fs)", filename, timestamp)
            return description.strip()

        except Exception as exc:
            logging.error("Error describing frame %s: %s", filename, exc)
            return "Error generating description."

    # ──────────────────────────────────────────────────────────────────────────
    # Vision – batch (all frames at once via asyncio.gather)
    # ──────────────────────────────────────────────────────────────────────────

    async def describe_all_images_async(
        self,
        keyframes: List[Tuple[Image.Image, float, str]],
    ) -> List[Dict]:
        """
        Fire all frame-description API calls concurrently with asyncio.gather.

        Parameters
        ----------
        keyframes : list of (PIL.Image, timestamp_seconds, frame_name)

        Returns
        -------
        list of dicts:
            {
                "frame_name": str,
                "timestamp":  float,
                "description": str,
            }
        """
        if not keyframes:
            return []

        logging.info(
            "Dispatching %d frame description calls concurrently…", len(keyframes)
        )

        tasks = [
            self.describe_image_async(img, name, ts)
            for img, ts, name in keyframes
        ]

        descriptions: List[str] = await asyncio.gather(*tasks)

        results = [
            {
                "frame_name": keyframes[i][2],
                "timestamp": keyframes[i][1],
                "description": descriptions[i],
            }
            for i in range(len(keyframes))
        ]

        logging.info("All %d frame descriptions received.", len(results))
        return results

    # ──────────────────────────────────────────────────────────────────────────
    # Frame JSON builder
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def build_frame_json(
        keyframes: List[Tuple[Image.Image, float, str]],
        descriptions: List[Dict],
        video_filename: str,
    ) -> List[Dict]:
        """
        Assemble one JSON record per frame and sort by filename (lexicographic).

        Parameters
        ----------
        keyframes    : list of (PIL.Image, timestamp, frame_name)
        descriptions : output of describe_all_images_async  (frame_name → desc)
        video_filename : original video file name (e.g. "drone_footage.mp4")

        Returns
        -------
        Sorted list of dicts:
            {
                "filename":   str,   # source video file name
                "frame_name": str,   # e.g. "frame_12.50"
                "time_stamp": float, # seconds into the video
                "description": str,
            }
        """
        # Build a lookup: frame_name → description dict
        desc_map: Dict[str, Dict] = {d["frame_name"]: d for d in descriptions}

        records = []
        for _img, ts, name in keyframes:
            desc_entry = desc_map.get(name, {})
            records.append(
                {
                    "filename": video_filename,
                    "frame_name": name,
                    "time_stamp": ts,
                    "description": desc_entry.get("description", ""),
                }
            )

        # Sort by frame_name (lexicographic on "frame_<float>" strings)
        records.sort(key=lambda r: r["frame_name"])
        return records

    # ──────────────────────────────────────────────────────────────────────────
    # Smart title
    # ──────────────────────────────────────────────────────────────────────────

    async def generate_smart_title_async(
        self, descriptions: Dict[str, str]
    ) -> str:
        """
        Generate a concise, action-oriented video title from frame descriptions.

        Parameters
        ----------
        descriptions : dict mapping frame_name → description string

        Returns
        -------
        A title string (max 8 words).
        """
        all_descs = list(descriptions.values())
        # Sample every 5th if more than 20 frames
        sample = all_descs[::5] if len(all_descs) > 20 else all_descs
        combined = "\n".join(sample)[:5000]

        try:
            response = await self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a video analyst. Create compelling, specific titles "
                            "for video footage that capture the key activity. "
                            "Titles must be concise (max 8 words) and immediately informative."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Based on the following video frame descriptions, generate a precise "
                            "and action-oriented title.\n\n"
                            "Requirements:\n"
                            "- Maximum 8 words\n"
                            "- Lead with the PRIMARY INCIDENT/ACTIVITY\n"
                            "- Include LOCATION/CONTEXT if relevant\n"
                            "- Use specific verbs (Confrontation, Trespassing, Suspicious Activity…)\n"
                            "- Never use filler phrases like 'Video of' or 'Footage of'\n\n"
                            "Examples:\n"
                            "- Trespassing Detected at Warehouse Perimeter\n"
                            "- Unauthorized Vehicle Access During Night Hours\n"
                            "- Physical Confrontation in Parking Lot Zone B\n\n"
                            f"Frame Descriptions:\n{combined}\n\n"
                            'Respond with ONLY valid JSON in this exact format: {"title": "<your title>"}'
                        ),
                    },
                ],
                response_format={"type": "json_object"},
                max_tokens=60,
                temperature=0.4,
            )
            raw = response.choices[0].message.content or "{}"
            data = json.loads(raw)
            return data.get("title", "Untitled Video")

        except Exception as exc:
            logging.error("Error generating smart title: %s", exc)
            return "Untitled Video"

    # ──────────────────────────────────────────────────────────────────────────
    # Query answering
    # ──────────────────────────────────────────────────────────────────────────

    async def answer_query_async(self, query: str, context_data: str) -> str:
        """
        Answer a user question using all metadata retrieved from ChromaDB as context.

        Parameters
        ----------
        query        : the user's natural language question
        context_data : full metadata + descriptions from ChromaDB results,
                       formatted as a string (filename, frame_name, timestamp, description)

        Returns
        -------
        A plain-text answer string.
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a security video analysis assistant. "
                            "Answer questions based ONLY on the provided frame data. "
                            "Each frame entry includes its source file name, frame identifier, "
                            "timestamp (seconds into the video), and a visual description. "
                            "Cite specific timestamps and frame names when relevant."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Retrieved Frame Data:\n"
                            "────────────────────\n"
                            f"{context_data[:6000]}\n"
                            "────────────────────\n\n"
                            f"Question: {query}"
                        ),
                    },
                ],
                max_tokens=400,
                temperature=0.3,
            )
            return (response.choices[0].message.content or "").strip()

        except Exception as exc:
            logging.error("Error answering query: %s", exc)
            return f"Error processing your query: {exc}"

    # ──────────────────────────────────────────────────────────────────────────
    # Embeddings  (sync – SentenceTransformer is not async)
    # ──────────────────────────────────────────────────────────────────────────

    def get_embedding(self, text: str) -> List[float]:
        """Generate a vector embedding for the given text (runs synchronously)."""
        return self.embedding_model.encode(text).tolist()

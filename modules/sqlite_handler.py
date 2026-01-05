import sqlite3
import logging
import io
from typing import List, Dict, Any, Optional
from datetime import datetime

class SQLiteHandler:
    """Handles SQLite operations for video metadata and frame storage."""
    
    def __init__(self, db_path: str = "videos.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Videos table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                uuid TEXT PRIMARY KEY,
                filename TEXT,
                smart_title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Frames table (stores image data as BLOB)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS frames (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_uuid TEXT,
                timestamp REAL,
                description TEXT,
                image_data BLOB,
                FOREIGN KEY (video_uuid) REFERENCES videos (uuid) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()

    def add_video(self, uuid: str, filename: str, smart_title: str):
        """Adds a new video entry."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO videos (uuid, filename, smart_title) VALUES (?, ?, ?)",
            (uuid, filename, smart_title)
        )
        conn.commit()
        conn.close()

    def add_frame(self, video_uuid: str, timestamp: float, description: str, image_data: bytes) -> int:
        """Adds a frame and returns its ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO frames (video_uuid, timestamp, description, image_data) VALUES (?, ?, ?, ?)",
            (video_uuid, timestamp, description, image_data)
        )
        frame_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return frame_id

    def get_videos(self) -> List[Dict[str, Any]]:
        """Retrieves all videos."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM videos ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_frame_image(self, frame_id: int) -> Optional[bytes]:
        """Retrieves the binary image data for a specific frame."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT image_data FROM frames WHERE id = ?", (frame_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def delete_video(self, video_uuid: str):
        """Deletes a video and all its frames."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM videos WHERE uuid = ?", (video_uuid,))
        cursor.execute("DELETE FROM frames WHERE video_uuid = ?", (video_uuid,))
        conn.commit()
        conn.close()

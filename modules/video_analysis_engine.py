import os
import uuid
import logging
import io
import json
from typing import Dict, Any

from .video_processor import VideoProcessor
from .ai_handler import AIHandler
from .db_handler import DBHandler
from .sqlite_handler import SQLiteHandler
from .alert_engine import AlertEngine
from .dino_handler import DINOHandler

class VideoAnalysisEngine:
    """Orchestrates the video analysis process."""
    
    def __init__(self):
        self.video_processor = VideoProcessor()
        self.ai_handler = AIHandler()
        self.db_handler = DBHandler(
            host=os.getenv("CHROMADB_HOST", "localhost"),
            port=int(os.getenv("CHROMADB_PORT", 8000))
        )
        self.sqlite_handler = SQLiteHandler()
        self.alert_engine = AlertEngine()
        self.dino_handler = DINOHandler()

    def process_video(self, video_path: str):
        if not os.path.exists(video_path):
            logging.error(f"Video file not found: {video_path}")
            return

        video_filename = os.path.basename(video_path)
        video_uuid = str(uuid.uuid4())
        logging.info(f"Processing video: {video_filename} (UUID: {video_uuid})")

        # 1. Create Video Entry in SQLite (Title will be updated later)
        self.sqlite_handler.add_video(video_uuid, video_filename, "Processing...")

        # 2. Stream and Filter Frames (Batch Processing)
        logging.info("Streaming and filtering frames with batch processing...")
        
        current_base_emb = None
        current_base_time = 0.0
        
        descriptions = {}
        alerts_generated = []
        frame_count = 0
        
        batch_size = 8
        frame_batch = []
        
        # Helper to process a batch
        def process_batch(batch):
            nonlocal current_base_emb, current_base_time, frame_count
            
            images = [f[0] for f in batch]
            timestamps = [f[1] for f in batch]
            
            # Batch DINO Embeddings
            embeddings = self.dino_handler.get_embeddings_batch(images)
            if embeddings is None:
                return

            for i, emb in enumerate(embeddings):
                timestamp = timestamps[i]
                pil_image = images[i]
                
                # Similarity Check (Sequential logic preserved)
                if current_base_emb is not None:
                    similarity = self.dino_handler.compute_similarity(current_base_emb, emb)
                    if similarity >= 0.90:
                        frame_count += 1
                        continue # Skip redundant frame

                # New Keyframe Selected
                logging.info(f"Selected keyframe at {timestamp:.2f}s")
                current_base_emb = emb
                current_base_time = timestamp
                frame_name = f"frame_{timestamp:.2f}"
                
                # AI Analysis
                desc = self.ai_handler.generate_image_description(pil_image, frame_name)
                descriptions[frame_name] = desc
                
                # Alert Check
                alert = self.alert_engine.check_rules(desc, frame_name)
                if alert:
                    alerts_generated.append(alert)
                
                # Save Frame to SQLite (BLOB)
                img_byte_arr = io.BytesIO()
                pil_image.save(img_byte_arr, format='JPEG')
                img_bytes = img_byte_arr.getvalue()
                
                frame_id = self.sqlite_handler.add_frame(video_uuid, timestamp, desc, img_bytes)
                
                # Store in ChromaDB
                enriched_desc = f"[{timestamp:.1f}s]: {desc}"
                embedding = self.ai_handler.get_embedding(enriched_desc)
                
                self.db_handler.add_entry(
                    video_uuid=video_uuid,
                    video_filename=video_filename,
                    frame_name=str(frame_id),
                    smart_name="Processing...", 
                    description=enriched_desc,
                    embedding=embedding,
                    file_path=""
                )
                
                frame_count += 1

        # Main Loop
        for pil_image, timestamp in self.video_processor.stream_frames(video_path):
            frame_batch.append((pil_image, timestamp))
            
            if len(frame_batch) >= batch_size:
                process_batch(frame_batch)
                frame_batch = []
        
        # Process remaining frames
        if frame_batch:
            process_batch(frame_batch)

        # 3. Generate Smart Title
        logging.info("Generating smart title...")
        smart_title = self.ai_handler.generate_smart_title(descriptions)
        logging.info(f"Smart Title: {smart_title}")
        
        # Update Title in SQLite
        # We need a method to update, for now re-insert or just rely on the fact we can't easily update with current handler
        # Let's add an update method to SQLiteHandler or just overwrite the entry if possible.
        # For simplicity, I will add an update method to SQLiteHandler in next step or just leave it as "Processing..." 
        # Actually, I should update it. I'll add a quick update query here using raw sqlite for now or update the handler.
        # Let's update the handler in the next step properly. For now, I will re-implement add_video to be an upsert or update.
        
        # Quick fix: Update title directly
        import sqlite3
        conn = sqlite3.connect(self.sqlite_handler.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE videos SET smart_title = ? WHERE uuid = ?", (smart_title, video_uuid))
        conn.commit()
        conn.close()
        
        logging.info(f"Processing complete. {len(alerts_generated)} alerts generated.")
        return {
            "video_uuid": video_uuid, 
            "smart_title": smart_title, 
            "alerts": alerts_generated
        }

    def query_video(self, video_uuid: str, query_text: str):
        logging.info(f"Querying video {video_uuid} with: {query_text}")
        query_embedding = self.ai_handler.get_embedding(query_text)
        results = self.db_handler.query(query_embedding, video_uuid)
        
        # Format context for AI answer
        context = ""
        if results['documents']:
            for doc in results['documents'][0]:
                context += doc + "\n"
        
        answer = self.ai_handler.answer_query(query_text, context)
        return answer

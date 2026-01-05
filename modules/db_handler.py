import chromadb
import logging
from typing import List

class DBHandler:
    """Handles ChromaDB operations."""
    
    def __init__(self, host: str, port: int, collection_name: str = "Video_Embeddings"):
        try:
            # Try connecting to HTTP client first as per original code
            self.client = chromadb.HttpClient(host=host, port=port)
        except:
            logging.warning("Could not connect to ChromaDB HTTP server. Falling back to local PersistentClient.")
            self.client = chromadb.PersistentClient(path="./chroma_db")
            
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_entry(self, video_uuid: str, video_filename: str, frame_name: str, 
                 smart_name: str, description: str, embedding: List[float], file_path: str = ""):
        
        self.collection.add(
            ids=[f"{video_uuid}_{frame_name}"],
            embeddings=[embedding],
            documents=[description],
            metadatas=[{
                "video_uuid": video_uuid,
                "video_file_name": video_filename,
                "frame_name": frame_name,
                "filename_plus_uuid": f"{video_filename}_{video_uuid}",
                "smart_name": smart_name,
                "file_path": file_path
            }]
        )

    def query(self, query_embedding: List[float], video_uuid: str, n_results: int = 5):
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where={"video_uuid": video_uuid},
            include=["documents", "metadatas"]
        )
        
    def delete_video(self, video_uuid: str):
        self.collection.delete(where={'video_uuid': video_uuid})

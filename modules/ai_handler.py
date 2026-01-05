import os
import logging
import base64
import time
from io import BytesIO
from PIL import Image
from groq import Groq
from sentence_transformers import SentenceTransformer
from typing import List, Dict
from dotenv import load_dotenv
load_dotenv()

class AIHandler:
    """Handles interactions with Groq API for LLM and SentenceTransformers for embeddings."""
    
    def __init__(self):
        # Initialize Groq client
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set. Please set it in your .env file or environment.")
        
        self.client = Groq(api_key=api_key)
        self.model = "meta-llama/llama-4-scout-17b-16e-instruct"
        # vision call uses the same model unless an override is provided
        self.vision_model = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
        
        # Rate limiting: 30 RPM = 2 seconds per request minimum
        self.min_request_interval = 2.1  # Slightly over 2 seconds to be safe
        self.last_request_time = 0
        
        # Load SentenceTransformer for embeddings (still using local model for speed)
        logging.info("Loading SentenceTransformer for embeddings...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logging.info("AI handler initialized with Groq API.")
        
    def generate_image_description(self, image: Image.Image, filename: str) -> str:
        """Generates a description for a single image using Groq Vision API."""
        # Rate limiting: ensure we don't exceed 30 RPM
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            logging.info(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        try:
            # Convert PIL Image to base64
            buffered = BytesIO()
            image.save(buffered, format="JPEG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            # Create chat completion with vision
            response = self.client.chat.completions.create(
                model=self.vision_model,  # configurable in case of deprecation
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_base64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": (
                                    "Analyze this image and provide a structured report. "
                                    "1. Count people. "
                                    "2. Identify activities (e.g., criminal, working, idle). "
                                    "3. Describe poses and interactions. "
                                    "4. Describe the environment. "
                                    "5. Highlight suspicious behavior. "
                                    f"Frame name: {filename}"
                                )
                            }
                        ]
                    }
                ],
                max_tokens=128,
                temperature=0.7
            )
            
            self.last_request_time = time.time()  # Update last request time
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.last_request_time = time.time()  # Update even on error
            logging.error(f"Error describing image {filename}: {e}")
            return "Error generating description."

    def generate_smart_title(self, video_info: Dict[str, str]) -> str:
        """Generates a smart title based on video descriptions."""
        # Rate limiting before title generation
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            logging.info(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        # Aggregate descriptions (limit length to avoid context overflow)
        combined_text = ""
        # Take a sample of frames (e.g., every 5th frame) to get a better overview if there are many
        descriptions = list(video_info.values())
        sample_descriptions = descriptions[::5] if len(descriptions) > 20 else descriptions
        
        for desc in sample_descriptions:
            combined_text += desc + "\n"
        
        try:
            # Use Groq LLM to generate a title
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a security video analyst. Create compelling, specific titles for drone security footage that capture the key incident or activity. Titles should be actionable and immediately convey what's happening."
                    },
                    {
                        "role": "user",
                        "content": (
                            "Based on the following video frame descriptions from drone security footage, generate a precise and action-oriented title for the video.\n\n"
                            "Requirements:\n"
                            "- Maximum 8 words (must be concise)\n"
                            "- Lead with the PRIMARY INCIDENT/ACTIVITY (not generic descriptions)\n"
                            "- Include LOCATION or CONTEXT if relevant\n"
                            "- Use specific verbs (e.g., 'Confrontation', 'Trespassing', 'Suspicious Activity')\n"
                            "- Never use filler phrases like 'Video of', 'Scene of', or 'Footage of'\n"
                            "- Make it immediately informative for security personnel\n\n"
                            "Example good titles:\n"
                            "- 'Trespassing Detected at Warehouse Perimeter'\n"
                            "- 'Unauthorized Vehicle Access During Night Hours'\n"
                            "- 'Physical Confrontation in Parking Lot Zone B'\n"
                            "- 'Suspicious Package Abandoned at Loading Dock'\n\n"
                            f"Video Frame Descriptions:\n{combined_text[:3000]}\n\n"
                            "Generate ONLY the title, nothing else:"
                        )
                    }
                ],
                max_tokens=30,
                temperature=0.7
            )
            
            self.last_request_time = time.time()
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.last_request_time = time.time()
            logging.error(f"Error generating title: {e}")
            return "Untitled Video"

    def answer_query(self, query: str, context_data: str) -> str:
        """Answers a user query based on the provided context using Groq."""
        # Rate limiting before query
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            logging.info(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful video analysis assistant. Answer questions based on the provided video data."
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Data: {context_data[:3000]}\n\n"
                            f"Query: {query}"
                        )
                    }
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            self.last_request_time = time.time()
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.last_request_time = time.time()
            logging.error(f"Error answering query: {e}")
            return f"Error processing your query: {str(e)}"

    def get_embedding(self, text: str) -> List[float]:
        """Generates a vector embedding for the given text."""
        return self.embedding_model.encode(text).tolist()

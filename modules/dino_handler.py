import torch
import logging
from PIL import Image
from transformers import AutoProcessor, AutoModel
from typing import Optional, List

class DINOHandler:
    """Handles DINO model for image embeddings and similarity checks."""
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.processor = None

    def load_model(self):
        """Lazily loads the DINO model."""
        if self.model is not None:
            return

        logging.info(f"Loading DINOv2 model on {self.device}...")
        try:
            # Using DINOv2 small model
            model_id = "facebook/dinov2-small"
            self.processor = AutoProcessor.from_pretrained(model_id, use_fast=True)
            from transformers import AutoModel
            self.model = AutoModel.from_pretrained(model_id).to(self.device)
        except Exception as e:
            logging.error(f"Error loading DINO model: {e}")
            self.model = None

    def get_embedding(self, image: Image.Image) -> Optional[torch.Tensor]:
        self.load_model()
        if not self.model: return None
        try:
            inputs = self.processor(images=image, return_tensors="pt").to(self.device)
            with torch.no_grad():
                outputs = self.model(**inputs)
            # Use the [CLS] token embedding (first token)
            return outputs.last_hidden_state[:, 0, :]
        except Exception as e:
            logging.error(f"Error computing DINO embedding: {e}")
            return None

    def get_embeddings_batch(self, images: List[Image.Image]) -> Optional[torch.Tensor]:
        """Computes embeddings for a batch of images."""
        self.load_model()
        if not self.model: return None
        try:
            # Processor handles resizing, padding arg might be unused/warning
            inputs = self.processor(images=images, return_tensors="pt").to(self.device)
            with torch.no_grad():
                outputs = self.model(**inputs)
            # Use the [CLS] token embedding (first token)
            return outputs.last_hidden_state[:, 0, :]
        except Exception as e:
            logging.error(f"Error computing DINO embeddings batch: {e}")
            return None

    def compute_similarity(self, emb1: torch.Tensor, emb2: torch.Tensor) -> float:
        if emb1 is None or emb2 is None: return 0.0
        
        # Ensure inputs are 2D (1, D) for CosineSimilarity(dim=1)
        if emb1.dim() == 1:
            emb1 = emb1.unsqueeze(0)
        if emb2.dim() == 1:
            emb2 = emb2.unsqueeze(0)
            
        cos = torch.nn.CosineSimilarity(dim=1, eps=1e-6)
        return cos(emb1, emb2).item()

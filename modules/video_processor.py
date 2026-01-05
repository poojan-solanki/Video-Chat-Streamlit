import cv2
import logging
from typing import Generator, Tuple
from PIL import Image

class VideoProcessor:
    """Handles video file operations and frame extraction."""
    
    def __init__(self):
        pass

    def get_dynamic_frame_interval(self, video_path: str, min_fps: float = 1.0, max_fps: float = 10.0) -> float:
        """Calculates frame interval based on video duration."""
        video = cv2.VideoCapture(video_path)
        if not video.isOpened():
            logging.error(f"Could not open video: {video_path}")
            return 1.0

        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = video.get(cv2.CAP_PROP_FPS)
        video.release()

        duration_seconds = total_frames / fps if fps > 0 else 0
        if duration_seconds == 0:
            return 1.0

        # Fixed interval for DINO processing (2 FPS)
        frame_interval = 0.5

        return max(1.0 / max_fps, min(1.0 / min_fps, frame_interval))

    def stream_frames(self, video_path: str) -> Generator[Tuple[Image.Image, float], None, None]:
        """
        Yields frames from the video as PIL Images.
        Returns: Generator yielding (PIL_Image, timestamp_in_seconds)
        """
        frame_interval_seconds = self.get_dynamic_frame_interval(video_path)
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")

        frame_rate = cap.get(cv2.CAP_PROP_FPS)
        interval_frames = max(1, int(frame_rate * frame_interval_seconds))
        
        frame_count = 0
        
        logging.info(f"Starting frame streaming for {video_path} at {frame_interval_seconds}s interval")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % interval_frames == 0:
                elapsed_time = frame_count / frame_rate
                
                # Convert BGR (OpenCV) to RGB (PIL)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(rgb_frame)
                
                yield pil_image, elapsed_time
            
            frame_count += 1

        cap.release()

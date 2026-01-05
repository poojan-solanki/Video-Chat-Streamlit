### Installation

### 1. Clone the repository

```bash
git clone https://github.com/poojan-solanki/Flytbase-Project.git
cd Flytbase-Project
```

### 2. Use uv sync to install dependencies

```bash
uv sync
source venv/bin/activate  # On Windows: venv\Scripts\activate
```


### Launch Streamlit App

```bash
streamlit run streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

## App Features

### Upload Video
- Upload videos (MP4, AVI, MOV, MKV, FLV, WMV)
- Real-time processing progress
- Automatic frame extraction and analysis
- Smart title generation using AI

### Dashboard
- View all uploaded videos
- Statistics overview (total videos, frames, storage usage)
- Search and filter videos
- View detailed information for each video
- Delete videos with proper cleanup

### Search & Query
- Select any processed video
- Ask natural language questions about the video
- Receive AI-powered answers based on video content
- View source frames used to generate the answers

### Additional Notes
- A **live video feed implementation** can be easily supported using the same architecture.  
- Due to **resource limitations**, the system was tested and demonstrated using uploaded video files instead of live streams.


## 📊 Architecture

```
┌─────────────────────┐
│   Streamlit UI      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  DatabaseManager    │ ← SQLite
│  - Videos           │
│  - Frames           │
│  - Metadata         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  VideoProcessor     │
│  - FrameExtractor   │
│  - ModelManager     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Groq API + ChromaDB │
│  - Analysis         │
│  - Embeddings       │
└─────────────────────┘
```

## Design Decisions and Architectural Choices

The overall architecture was intentionally kept **minimal and modular**, focusing on reliability, speed, and clarity rather than over-engineering.

### Exclusion of LangChain

LangChain was deliberately not used in this project. Based on prior experience and the scope of the requirements, LangChain would not have provided significant benefits for this use case. Instead, it would have introduced **additional abstraction layers and noticeable latency**.
Since the workflow did not require complex agent orchestration, tool chaining, or memory management, a direct integration approach resulted in a **simpler, faster, and more controllable system**.

### Model Experimentation (BLIP & CLIP)

I explored both **BLIP** and **CLIP** models during experimentation:

* **BLIP**: Due to limited development time, I was unable to achieve meaningful results suitable for the task. While BLIP is powerful for image captioning and vision-language understanding, its integration required more tuning and experimentation than the timeline allowed.
* **CLIP**: CLIP was tested but ultimately found to be **less effective for the specific requirements** of this project. Its strengths did not align closely with the task objectives.

Given the constraints, these models were not included in the final architecture.

---

## AI Tools and Models Used

### Large Language Model

* **Model:** `meta-llama/llama-4-scout-17b-16e-instruct`
* **Provider:** Groq Inference

This model was chosen for its **strong instruction-following capabilities** and **low-latency inference** when served via Groq. It significantly improved response time and overall system performance, making it well-suited for real-time or near-real-time applications.

### Image Similarity Model

* **Model:** **DINOv2**

DINOv2 was integrated for **image similarity and visual feature extraction**. It provided robust semantic image embeddings without requiring labeled data, making it an excellent choice for similarity comparison tasks. Its inclusion reduced the number of frames passed to the LLaMA model by skipping visually similar video frames and processing only distinct ones, resulting in faster inference and more efficient overall processing while keeping the architecture lightweight.

---

## Impact on Workflow

* Reduced latency by avoiding unnecessary framework overhead
* Faster inference using Groq-hosted LLaMA models
* Improved processing speed with DINOv2
* Maintained a clean and maintainable codebase suitable for iteration and scaling

---

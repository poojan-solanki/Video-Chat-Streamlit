# Drone Security Agent - Technical Documentation

> **Version:** 1.0  
> **Last Updated:** January 6, 2026  
> **Project:** Video Analysis Engine for Drone Security

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Module Documentation](#module-documentation)
5. [Data Flow](#data-flow)
6. [API Reference](#api-reference)
7. [Database Schema](#database-schema)
8. [Installation & Deployment](#installation--deployment)
9. [Usage Guide](#usage-guide)
10. [Configuration](#configuration)
11. [Performance Optimizations](#performance-optimizations)
12. [Design Decisions](#design-decisions)
13. [Future Enhancements](#future-enhancements)

---

## Executive Summary

The **Drone Security Agent** is an AI-powered video analysis application designed to process drone security footage and provide intelligent insights through natural language queries. The system uses state-of-the-art vision models and large language models to analyze video content, detect security threats, and enable conversational interaction with video data.

### Key Features

- **Intelligent Video Processing**: Automated frame extraction with similarity-based deduplication using DINOv2
- **AI-Powered Analysis**: Vision-language understanding using Groq's LLaMA models
- **Smart Title Generation**: Automatic generation of descriptive video titles based on content
- **Natural Language Queries**: Ask questions about video content and receive contextual answers
- **Alert System**: Rule-based security alert detection for critical events
- **Dual Database Architecture**: SQLite for structured data, ChromaDB for vector embeddings
- **Modern Web Interface**: Built with Streamlit for intuitive user experience

### System Capabilities

- Processes multiple video formats (MP4, MOV, AVI, MKV, WebM)
- Batch processing for efficient frame analysis
- Real-time progress tracking during video processing
- Semantic search across video content
- Frame-level metadata storage and retrieval

---

## System Architecture

The application follows a modular architecture with clear separation of concerns:

![System Architecture](architecture-1.png)

### Architecture Layers

#### 1. **Presentation Layer**
- **Component**: `streamlit_app.py`
- **Responsibility**: User interface, file uploads, video library, chat interface
- **Technologies**: Streamlit, Custom CSS

#### 2. **Orchestration Layer**
- **Component**: `VideoAnalysisEngine`
- **Responsibility**: Coordinates all processing components, manages workflow
- **Technologies**: Python, Threading

#### 3. **Processing Layer**
- **Components**: 
  - `VideoProcessor`: Frame extraction and streaming
  - `AIHandler`: LLM and embedding generation
  - `DINOHandler`: Image similarity computation
  - `AlertEngine`: Security rule evaluation

#### 4. **Data Layer**
- **Components**:
  - `SQLiteHandler`: Structured data storage
  - `DBHandler`: Vector database operations
- **Technologies**: SQLite, ChromaDB

---

## Technology Stack

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Runtime** | Python | 3.9+ | Application runtime |
| **Web Framework** | Streamlit | Latest | User interface |
| **Video Processing** | OpenCV | Latest | Frame extraction |
| **Computer Vision** | PIL (Pillow) | Latest | Image manipulation |
| **LLM Provider** | Groq API | - | Fast LLM inference |
| **LLM Model** | LLaMA-4-Scout-17B | - | Vision-language tasks |
| **Embeddings** | SentenceTransformers | Latest | Text embeddings |
| **Vision Model** | DINOv2-Small | Facebook | Image similarity |
| **Vector DB** | ChromaDB | Latest | Embedding storage |
| **Relational DB** | SQLite | 3.x | Metadata storage |
| **ML Framework** | PyTorch | Latest | Model inference |

### Dependencies

```
opencv-python      # Video frame extraction
chromadb          # Vector database
python-dotenv     # Environment configuration
groq              # Groq API client
pillow            # Image processing
sentence-transformers  # Text embeddings
streamlit         # Web interface
transformers      # HuggingFace models
torch             # PyTorch framework
```

---

## Module Documentation

### 1. Video Analysis Engine

**File**: [`video_analysis_engine.py`](modules/video_analysis_engine.py)

#### Class: `VideoAnalysisEngine`

**Purpose**: Central orchestrator for the entire video analysis pipeline.

**Responsibilities**:
- Coordinate all processing modules
- Manage video processing workflow
- Handle batch processing of frames
- Generate smart titles
- Process user queries

**Key Methods**:

##### `__init__(self)`

Initializes all component handlers:
- `VideoProcessor`: Frame extraction
- `AIHandler`: LLM and embeddings
- `DBHandler`: ChromaDB operations
- `SQLiteHandler`: SQLite operations
- `AlertEngine`: Security alerts
- `DINOHandler`: Image similarity

##### `process_video(self, video_path: str) -> Dict`

**Purpose**: Main video processing pipeline.

**Workflow**:
1. **Video Entry Creation**: Creates initial database entry
2. **Frame Streaming**: Extracts frames at 2 FPS
3. **Batch Processing**: Processes frames in batches of 8
4. **Similarity Filtering**: Uses DINO embeddings to skip similar frames (>90% similarity)
5. **AI Analysis**: Generates descriptions for unique frames
6. **Alert Detection**: Checks for security violations
7. **Data Storage**: Saves to both SQLite and ChromaDB
8. **Title Generation**: Creates smart title from frame descriptions

**Parameters**:
- `video_path` (str): Absolute path to video file

**Returns**:
```python
{
    "video_uuid": str,      # Unique identifier
    "smart_title": str,     # AI-generated title
    "alerts": List[Dict]    # Security alerts
}
```

**Processing Flow**:

![Processing Flow](processing-flow-1.png)

##### `query_video(self, video_uuid: str, query_text: str) -> str`

**Purpose**: Answer natural language queries about video content.

**Workflow**:
1. Generate embedding for query
2. Search ChromaDB for relevant frames
3. Build context from matching descriptions
4. Use LLM to generate answer

**Parameters**:
- `video_uuid` (str): Video identifier
- `query_text` (str): User's question

**Returns**: Natural language answer (str)

---

### 2. AI Handler

**File**: [`ai_handler.py`](/modules/ai_handler.py)

#### Class: `AIHandler`

**Purpose**: Manages all AI/ML operations including vision analysis and text generation.

**Responsibilities**:
- Image description generation
- Smart title creation
- Query answering
- Text embedding generation

**Configuration**:
```python
LLM_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # SentenceTransformer
```

**Key Methods**:

##### `generate_image_description(self, image: Image.Image, filename: str) -> str`

**Purpose**: Generate detailed description of image using vision-language model.

**Implementation Details**:
- Converts image to base64 JPEG
- Uses Groq Vision API
- Temperature: 0.3 (balanced creativity/accuracy)
- Max tokens: 150

**Prompt Template**:
```
Describe this surveillance footage frame in detail. Focus on:
- Objects and people present
- Actions and activities
- Environmental context
- Any security-relevant observations
```

**Returns**: Detailed frame description

##### `generate_smart_title(self, video_info: Dict[str, str]) -> str`

**Purpose**: Create concise, descriptive title from video content.

**Process**:
1. Samples frame descriptions (max 10)
2. Concatenates descriptions with timestamps
3. Prompts LLM to generate 3-5 word title
4. Returns professional, descriptive title

**Example Output**: "Construction Site Worker Activity"

##### `answer_query(self, query: str, context_data: str) -> str`

**Purpose**: Answer user questions using retrieved context.

**Implementation**:
- Uses RAG (Retrieval Augmented Generation) pattern
- Combines retrieved frame descriptions with query
- Generates contextual answer
- Max tokens: 300

##### `get_embedding(self, text: str) -> List[float]`

**Purpose**: Generate 384-dimensional vector embedding.

**Model**: SentenceTransformers `all-MiniLM-L6-v2`
**Dimensions**: 384
**Use Cases**: Semantic search, similarity matching

---

### 3. DINO Handler

**File**: [`dino_handler.py`](/modules/dino_handler.py)

#### Class: `DINOHandler`

**Purpose**: Handle image similarity detection using DINOv2 model.

**Model**: `facebook/dinov2-small`
**Device**: CUDA if available, else CPU

**Key Methods**:

##### `load_model(self)`

**Lazy Loading**: Model loaded on first use to reduce startup time.

**Components**:
- `AutoProcessor`: Image preprocessing
- `AutoModel`: DINOv2 vision transformer

##### `get_embedding(self, image: Image.Image) -> torch.Tensor`

**Purpose**: Generate image embedding vector.

**Process**:
1. Preprocess image
2. Forward pass through model
3. Extract [CLS] token embedding
4. Return as tensor

**Embedding Dimension**: 384 (for small variant)

##### `get_embeddings_batch(self, images: List[Image.Image]) -> torch.Tensor`

**Purpose**: Efficient batch processing of multiple images.

**Optimization**: ~8x faster than sequential processing

**Returns**: Batch of embeddings [batch_size, 384]

##### `compute_similarity(self, emb1: torch.Tensor, emb2: torch.Tensor) -> float`

**Purpose**: Calculate cosine similarity between embeddings.

**Formula**: 
```
similarity = (emb1 · emb2) / (||emb1|| * ||emb2||)
```

**Returns**: Similarity score [0.0, 1.0]
- 0.0: Completely different
- 1.0: Identical
- **Threshold**: 0.90 (frames above this are considered duplicates)

---

### 4. Video Processor

**File**: [`video_processor.py`](/modules/video_processor.py)

#### Class: `VideoProcessor`

**Purpose**: Handle video file operations and frame extraction.

**Key Methods**:

##### `get_dynamic_frame_interval(self, video_path: str) -> float`

**Purpose**: Calculate optimal frame extraction rate.

**Current Implementation**: Fixed at 2 FPS (0.5 second intervals)

**Parameters**:
- `min_fps`: Minimum frames per second (default: 1.0)
- `max_fps`: Maximum frames per second (default: 10.0)

**Returns**: Frame interval in seconds

##### `stream_frames(self, video_path: str) -> Generator[Tuple[Image.Image, float], None, None]`

**Purpose**: Memory-efficient frame streaming.

**Advantages**:
- Low memory footprint (only one frame in memory)
- Immediate processing start
- No temporary file storage

**Yields**:
```python
(pil_image, timestamp)  # Tuple[Image.Image, float]
```

**Process**:
1. Open video with OpenCV
2. Calculate frame skip interval
3. Yield frame every N frames
4. Convert BGR to RGB
5. Convert to PIL Image

---

### 5. SQLite Handler

**File**: [`sqlite_handler.py`](/modules/sqlite_handler.py)

#### Class: `SQLiteHandler`

**Purpose**: Manage structured data storage in SQLite.

**Database**: `videos.db`

**Key Methods**:

##### `_init_db(self)`

**Purpose**: Initialize database schema.

**Tables**:

**videos**:
```sql
CREATE TABLE videos (
    uuid TEXT PRIMARY KEY,
    filename TEXT,
    smart_title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**frames**:
```sql
CREATE TABLE frames (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_uuid TEXT,
    timestamp REAL,
    description TEXT,
    image_data BLOB,
    FOREIGN KEY (video_uuid) REFERENCES videos(uuid) ON DELETE CASCADE
)
```

##### `add_video(self, uuid: str, filename: str, smart_title: str)`

**Purpose**: Create new video entry.

**Usage**: Called at start of video processing.

##### `add_frame(self, video_uuid: str, timestamp: float, description: str, image_data: bytes) -> int`

**Purpose**: Store frame metadata and image data.

**Returns**: Auto-incremented frame ID

**Image Storage**: JPEG format as BLOB

##### `get_videos(self) -> List[Dict[str, Any]]`

**Purpose**: Retrieve all videos.

**Returns**:
```python
[
    {
        "uuid": "abc-123",
        "filename": "drone_footage.mp4",
        "smart_title": "Construction Site Monitoring",
        "created_at": "2026-01-06 11:30:00"
    }
]
```

**Order**: Newest first (DESC by created_at)

##### `get_frame_image(self, frame_id: int) -> Optional[bytes]`

**Purpose**: Retrieve frame image data.

**Returns**: JPEG bytes or None

##### `delete_video(self, video_uuid: str)`

**Purpose**: Delete video and all associated frames.

**Cascading**: Automatically removes all frames due to FOREIGN KEY constraint.

---

### 6. ChromaDB Handler

**File**: [`db_handler.py`](/modules/db_handler.py)

#### Class: `DBHandler`

**Purpose**: Manage vector embeddings for semantic search.

**Collection**: `Video_Embeddings`

**Connection Strategy**:
1. Attempt HTTP client connection (for production)
2. Fallback to PersistentClient (for local development)

**Key Methods**:

##### `add_entry(self, video_uuid: str, video_filename: str, frame_name: str, smart_name: str, description: str, embedding: List[float], file_path: str = "")`

**Purpose**: Store frame embedding with metadata.

**Document ID Format**: `{video_uuid}_{frame_name}`

**Metadata**:
```python
{
    "video_uuid": str,
    "video_file_name": str,
    "frame_name": str,
    "filename_plus_uuid": str,
    "smart_name": str,
    "file_path": str
}
```

##### `query(self, query_embedding: List[float], video_uuid: str, n_results: int = 5)`

**Purpose**: Semantic search for relevant frames.

**Filter**: Results limited to specified video

**Returns**:
```python
{
    "documents": [[str, ...]],  # Frame descriptions
    "metadatas": [[dict, ...]]  # Frame metadata
}
```

##### `delete_video(self, video_uuid: str)`

**Purpose**: Remove all embeddings for a video.

---

### 7. Alert Engine

**File**: [`alert_engine.py`](/modules/alert_engine.py)

#### Class: `AlertEngine`

**Purpose**: Evaluate security rules and generate alerts.

**Rule Types**:

1. **Security Breach** (HIGH)
   - Trigger: "person" + "restricted"
   - Message: "Person detected in restricted area"

2. **Suspicious Activity** (MEDIUM)
   - Trigger: "suspicious" or "suspicious behavior"
   - Message: "Suspicious activity detected"

3. **Weapon Detection** (CRITICAL)
   - Trigger: "weapon" or "gun" or "armed"
   - Message: "Potential weapon detected"

4. **Unauthorized Access** (HIGH)
   - Trigger: "trespassing" or "unauthorized" or "intrusion"
   - Message: "Unauthorized access detected"

**Alert Format**:
```python
{
    "severity": "HIGH",  # CRITICAL, HIGH, MEDIUM
    "type": "Security Breach",
    "message": "Person detected in restricted area",
    "frame": "frame_12.5"
}
```

---

### 8. Streamlit Application

**File**: [`streamlit_app.py`](streamlit_app.py)

#### Application Structure

**Page Configuration**:
```python
st.set_page_config(
    page_title="Drone Security Agent - Powered by Groq",
    layout="wide",
    page_icon="🚁",
    initial_sidebar_state="expanded"
)
```

**Key Features**:

##### Video Upload & Processing
- Supported formats: MP4, MOV, AVI, MKV, WebM
- Real-time progress tracking
- File size display
- Automatic cleaning of temporary files

##### Video Library
- Grid/list view of all videos
- Search functionality
- Metadata display
- Delete functionality
- Thumbnail preview

##### Chat Interface
- Video selection dropdown
- Natural language query input
- AI-powered responses
- Context-aware answers
- Chat history

**Session State**:
```python
{
    'messages': List[Dict],          # Chat history
    'selected_video': str,           # Current video UUID
    'selected_video_name': str,      # Display name
    'engine': VideoAnalysisEngine    # Lazy-loaded engine
}
```

**Lazy Loading Strategy**:
```python
@st.cache_resource
def get_engine():
    return VideoAnalysisEngine()
```

**Benefit**: Reduces initial page load time by deferring heavy model loading.

---

## Data Flow

### Video Processing Flow

![Video Processing Flow](video-processing-flow-1.png)

### Query Processing Flow

![Query Processing Flow](query-processing-flow-1.png)

### Data Storage Strategy

**SQLite** (Structured Data):
- Video metadata
- Frame metadata
- Frame images (BLOB)
- Relational integrity

**ChromaDB** (Vector Data):
- Frame embeddings
- Text descriptions
- Semantic search
- Similarity matching

**Rationale**: Hybrid approach optimizes for both structured queries and semantic search.

---

## API Reference

### Environment Variables

**Required**:
```bash
GROQ_API_KEY="your-groq-api-key"  # Groq API authentication
```

**Optional**:
```bash
CHROMADB_HOST="localhost"         # ChromaDB server host
CHROMADB_PORT="8000"              # ChromaDB server port
```

### Groq API Usage

**Endpoint**: Vision Chat Completions

**Request Format**:
```python
response = client.chat.completions.create(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Describe this image..."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
        }
    ],
    temperature=0.3,
    max_tokens=150
)
```

**Rate Limits**: Managed by exponential backoff retry mechanism

---

## Database Schema

### SQLite Schema

#### Videos Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| uuid | TEXT | PRIMARY KEY | Unique identifier (UUID4) |
| filename | TEXT | NOT NULL | Original filename |
| smart_title | TEXT | NOT NULL | AI-generated title |
| created_at | TIMESTAMP | DEFAULT NOW | Upload timestamp |

**Indexes**: Primary key on `uuid`

#### Frames Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Frame identifier |
| video_uuid | TEXT | FOREIGN KEY → videos(uuid) | Parent video |
| timestamp | REAL | NOT NULL | Time in video (seconds) |
| description | TEXT | NOT NULL | AI-generated description |
| image_data | BLOB | NOT NULL | JPEG image bytes |

**Indexes**: 
- Primary key on `id`
- Foreign key on `video_uuid` (CASCADE DELETE)

**Storage Estimate**: ~100KB per frame (JPEG compressed)

### ChromaDB Schema

**Collection**: `Video_Embeddings`

**Document Structure**:
```json
{
    "id": "video-uuid_frame-name",
    "embedding": [0.123, -0.456, ...],  // 384 dimensions
    "document": "[12.5s]: Person walking with hard hat...",
    "metadata": {
        "video_uuid": "abc-123",
        "video_file_name": "drone_footage.mp4",
        "frame_name": "frame_12.5",
        "filename_plus_uuid": "drone_footage.mp4_abc-123",
        "smart_name": "Construction Monitoring",
        "file_path": ""
    }
}
```

**Index**: HNSW (Hierarchical Navigable Small World) for fast similarity search

---

## Installation & Deployment

### Prerequisites

- Python 3.9 or higher
- pip or uv package manager
- GROQ API key

### Installation Steps

#### 1. Clone Repository
```bash
git clone https://github.com/poojan-solanki/Video-Chat-Streamlit.git
cd Video-Chat-Streamlit
```

#### 2. Install Dependencies

**Using uv** (recommended):
```bash
uv sync
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

**Using pip**:
```bash
pip install -r requirements.txt
```

#### 3. Configure Environment
```bash
# Create .env file
echo "GROQ_API_KEY=your-api-key-here" > .env
```

#### 4. Launch Application
```bash
streamlit run streamlit_app.py
```

**Access**: http://localhost:8501

### Production Deployment

**Recommended Stack**:
- **Hosting**: AWS EC2 / Google Cloud Compute
- **Web Server**: Nginx reverse proxy
- **Process Manager**: systemd or supervisor
- **Database**: Persistent volume for SQLite and ChromaDB

**Docker Deployment** (Optional):
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501"]
```

---

## Usage Guide

### 1. Uploading Videos

1. Click **"📤 Upload Video"** in sidebar
2. Select video file (MP4, MOV, AVI, MKV, WebM)
3. Click **"🚀 Process Video"**
4. Monitor progress bar

**Processing Time**: ~30 seconds per minute of video (depends on GPU availability)

### 2. Viewing Video Library

- **Search**: Use search box to filter by title
- **View Details**: Click on video card
- **Delete**: Use delete button (requires confirmation)

### 3. Querying Videos

1. Select video from dropdown
2. Type natural language question
3. Press Enter or click Send
4. View AI-generated answer

**Example Queries**:
- "What activities are visible in the video?"
- "Are there any people in the footage?"
- "Describe the environment shown"
- "What time of day was this recorded?"

### 4. Viewing Alerts

Alerts are automatically generated during processing and displayed with video metadata:
- **CRITICAL**: Red badge
- **HIGH**: Orange badge
- **MEDIUM**: Yellow badge

---

## Configuration

### Model Configuration

**LLM Model**:
```python
# In ai_handler.py
LLM_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
```

**Embedding Model**:
```python
# In ai_handler.py
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
```

**Vision Model**:
```python
# In dino_handler.py
VISION_MODEL = "facebook/dinov2-small"
```

### Processing Configuration

**Frame Extraction Rate**:
```python
# In video_processor.py
FRAME_INTERVAL = 0.5  # 2 FPS
```

**Batch Size**:
```python
# In video_analysis_engine.py
BATCH_SIZE = 8  # Frames per batch
```

**Similarity Threshold**:
```python
# In video_analysis_engine.py
SIMILARITY_THRESHOLD = 0.90  # 90% similarity
```

### UI Configuration

**Page Layout**:
```python
# In streamlit_app.py
st.set_page_config(
    page_title="Drone Security Agent",
    layout="wide",  # or "centered"
    page_icon="🚁"
)
```

---

## Performance Optimizations

### 1. Lazy Loading

**Heavy Models**: Loaded only when needed
```python
@st.cache_resource
def get_engine():
    return VideoAnalysisEngine()
```

**Benefit**: Reduces initial page load from ~30s to ~2s

### 2. Batch Processing

**Frame Analysis**: Process 8 frames simultaneously
```python
batch_size = 8
embeddings = dino_handler.get_embeddings_batch(images)
```

**Improvement**: 8x faster than sequential processing

### 3. Frame Deduplication

**DINO Similarity**: Skip similar frames (>90%)
```python
if similarity >= 0.90:
    continue  # Skip frame
```

**Impact**: Reduces processed frames by ~70%

### 4. Database Indexing

**SQLite**: Primary keys and foreign keys
**ChromaDB**: HNSW index for fast vector search

**Query Performance**: <100ms for semantic search

### 5. Memory Management

**Frame Streaming**: Only one frame in memory at a time
```python
for frame, timestamp in stream_frames(video_path):
    process(frame)  # Frame is garbage collected after processing
```

**Benefit**: Handles large videos without memory issues

---

## Design Decisions

### 1. Why Not LangChain?

**Decision**: Direct API integration instead of LangChain

**Rationale**:
- Reduced latency (no abstraction overhead)
- Simpler debugging
- More control over prompts
- Lighter dependencies

**Trade-off**: Less framework automation, but better performance

### 2. Dual Database Strategy

**SQLite** for:
- Structured metadata
- BLOB storage (images)
- ACID transactions
- Simple queries

**ChromaDB** for:
- Vector embeddings
- Semantic search
- Similarity matching

**Rationale**: Right tool for the right job

### 3. DINOv2 for Similarity

**Alternatives Considered**:
- CLIP: Less effective for this use case
- BLIP: Required more tuning time

**Chosen**: DINOv2 Small

**Benefits**:
- No labeled data needed
- Strong semantic understanding
- Fast inference
- Small model size (~90MB)

### 4. Groq for LLM Inference

**Alternatives**: OpenAI, Anthropic, Local models

**Chosen**: Groq with LLaMA-4-Scout

**Benefits**:
- Fastest inference speed (~400 tokens/sec)
- Cost-effective
- Vision capabilities
- Strong instruction following

### 5. Streamlit for UI

**Alternatives**: FastAPI + React, Gradio, Flask

**Chosen**: Streamlit

**Benefits**:
- Rapid development
- Python-native
- Built-in state management
- Beautiful default styling

---

## Future Enhancements

### Planned Features

1. **Live Video Streaming**
   - Real-time RTSP/RTMP support
   - Continuous processing
   - Live alert notifications

2. **Advanced Vision Models**
   - BLIP integration for better captioning
   - SAM3 for object segmentation
   - Spatial tracking across frames

3. **Enhanced Security**
   - Custom rule builder
   - ML-based anomaly detection
   - Multi-camera coordination

4. **Performance Improvements**
   - GPU acceleration for all models
   - Distributed processing
   - Caching strategies

5. **User Experience**
   - Mobile app
   - Custom dashboards
   - Export functionality (PDF reports)

### Technical Debt

- Add comprehensive unit tests
- Implement proper logging framework
- Add API documentation (OpenAPI/Swagger)
- Implement user authentication
- Add video playback controls

---

## Appendix

### File Structure

```
flytbase/
├── .env                          # Environment variables
├── .gitignore                    # Git ignore rules
├── README.md                     # Project overview
├── requirements.txt              # Python dependencies
├── streamlit_app.py              # Main application
├── videos.db                     # SQLite database
├── chroma_db/                    # ChromaDB storage
├── modules/
│   ├── __init__.py
│   ├── video_analysis_engine.py  # Main orchestrator
│   ├── video_processor.py        # Frame extraction
│   ├── ai_handler.py             # LLM operations
│   ├── dino_handler.py           # Image similarity
│   ├── sqlite_handler.py         # SQLite operations
│   ├── db_handler.py             # ChromaDB operations
│   └── alert_engine.py           # Security alerts
└── test-videos/                  # Sample videos
```

### Glossary

**DINO**: Self-DIstillation with NO labels - Vision transformer model
**RAG**: Retrieval Augmented Generation - LLM pattern
**HNSW**: Hierarchical Navigable Small World - Vector index algorithm
**BLOB**: Binary Large OBject - Database storage type
**UUID**: Universally Unique Identifier
**FPS**: Frames Per Second
**Embedding**: Dense vector representation of data
**Cosine Similarity**: Measure of similarity between vectors

---


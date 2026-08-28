# Resume-JD Intelligence Platform MVP

A practical, production-oriented MVP web application that analyzes a candidate's resume against a Job Description using LLMs, embeddings, RAG, vector search, and structured matching. 

It evaluates compliance for individual job description requirements by retrieving relevant evidence from the resume and running deterministic scoring algorithms.

---

## Architecture & RAG Pipeline Workflow

The platform implements a structured **Retrieval-Augmented Generation (RAG)** pipeline to evaluate candidate compatibility:

```
[Resume Upload (PDF/DOCX/TXT)]       [Job Description (Paste/File)]
             │                                     │
             ▼                                     ▼
      [DocumentParser]                      [DocumentParser]
             │                                     │
             ▼                                     ▼
      [ResumeAnalyzer]                       [JDAnalyzer]
   (Extract Structured JSON)              (Extract Requirements)
             │                                     │
             ▼                                     ▼
     [RAG Document Splitter]              [RAG Document Splitter]
   (Context-aware Chunks)                 (Context-aware Chunks)
             │                                     │
             ▼                                     ▼
   [EmbeddingService] (Qwen3-Embedding-0.6B) ──► [Index in Qdrant]
                                                           │
                                                           ▼
                                               [RAG Evidence Retrieval]
                                            (Query: each JD requirement)
                                                           │
                                                           ▼
                                                [LLM Match Evaluation]
                                                (Compare evidence text)
                                                           │
                                                           ▼
                                               [Deterministic Scoring]
                                            (required, preferred, semantic)
                                                           │
                                                           ▼
                                                [SQL Database & UI]
```

1. **Intake & Parsing**: Resume and JD files are decoded to clean plain text.
2. **Entity Extraction**: The Groq LLM parses the resume into a structured Pydantic record (skills, work history items, projects, education) and identifies Job Description requirements (skills, experience years needed).
3. **Structured Chunking**: Documents are chunked dynamically by section (preserving experience, project, and qualification contexts) to prevent dilution.
4. **Vector Indexing**: Chunks are embedded using `Qwen3-Embedding-0.6B` and indexed into the Qdrant vector database.
5. **RAG Evidence Verification**: For each job requirement, the platform query-searches Qdrant for matching resume chunks. The LLM evaluates these chunks to determine if they constitute a `strong_match`, `partial_match`, `weak_match`, or are `missing`.
6. **Deterministic Scoring**: A Python-based matching layer computes an overall score using configured weights, bypassing LLM score hallucination.
7. **Interactive Dialogue**: A RAG chatbot uses the indexed contexts of both documents to answer follow-up queries.

---

## Zero-Configuration Fallbacks

To run offline or without secondary infrastructure containers during local development, the application features built-in fallback layers:
* **PostgreSQL Fallback**: Automatically creates and uses a local SQLite database (`sqlite:///./resume_matcher.db`) if a PostgreSQL server is unreachable.
* **Qdrant Fallback**: Automatically creates and uses a local in-memory Qdrant instance (`location=":memory:"`) if the Qdrant container is unreachable.
* **Mock AI Fallback**: If `MOCK_AI=true` or if `GROQ_API_KEY` is not provided, the backend falls back to high-fidelity simulated parsing and keyword matching, enabling offline testing.

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```env
# Groq api config
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL= choose the model you chhose , i use openai/gpt-oss-120b

# Embedding Model
EMBEDDING_MODEL= i used BAAI/bge-small-en-v1.5, you can choose other models as well

# Databases (Set up automatically if left empty/unreachable)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/resume_matcher
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# Mock AI mode the development, set to TRUE for dev mode and save tokens.
MOCK_AI=false
```

Place your **Groq API Key** in the `GROQ_API_KEY` parameter in this `.env` file at the root.

---

## Installation & Setup

### Prerequisites
* Python 3.10+ (tested on Python 3.14)
* Node.js v18+ and npm
* Docker (Optional, for running external Qdrant & PostgreSQL)

### Step 1: Start Databases (Optional)
If you have Docker running, launch the PostgreSQL and Qdrant containers:
```bash
docker compose up -d
```
*If Docker is not running or not installed, the platform will automatically fall back to **SQLite** and **in-memory Qdrant**.*

### Step 2: Backend Setup
1. Navigate to the project root and install requirements:
   ```bash
   pip install -r backend/requirements.txt
   ```
2. Start the FastAPI development server:
   ```bash
   python -m uvicorn backend.app.main:app --reload --port 8000
   ```
   *The backend will be available at [http://localhost:8000](http://localhost:8000). Swagger docs can be viewed at [http://localhost:8000/docs](http://localhost:8000/docs).*

### Step 3: Frontend Setup
1. Navigate to the `frontend/` directory and install packages:
   ```bash
   cd frontend
   npm install
   ```
2. Start the Vite React development server:
   ```bash
   npm run dev
   ```
   *The React interface will run at [http://localhost:5173](http://localhost:5173).*

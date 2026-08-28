import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.database.connection import engine, Base
from backend.app.api.analyze import router as analyze_router
from backend.app.api.chat import router as chat_router
from backend.app.api.history import router as history_router

# Configure logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("app.main")

# Auto-migrate SQL database tables
try:
    logger.info("Auto-migrating database schemas...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schemas initialized.")
except Exception as e:
    logger.critical(f"Failed to auto-migrate database: {e}", exc_info=True)

# Initialize FastAPI App
app = FastAPI(
    title="Resume-JD Matcher API",
    description="Backend services for parsing resumes, mapping skills, scoring and RAG-based search.",
    version="1.0.0"
)

# Enable CORS for React local dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local MVP development, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routes
app.include_router(analyze_router, prefix="/api", tags=["Analysis"])
app.include_router(chat_router, prefix="/api", tags=["Chat"])
app.include_router(history_router, prefix="/api", tags=["History"])

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Resume-JD Matcher API",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)

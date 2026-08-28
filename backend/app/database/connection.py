import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.config import settings

logger = logging.getLogger("app.database")
Base = declarative_base()
SessionLocal = None

def init_database():
    global SessionLocal
    db_url = settings.DATABASE_URL
    
    # Try connecting to PostgreSQL first
    if db_url.startswith("postgresql"):
        try:
            logger.info(f"Attempting connection to PostgreSQL database at {db_url.split('@')[-1]}...")
            engine = create_engine(db_url, connect_args={"connect_timeout": 3})
            # Test connection
            with engine.connect() as conn:
                logger.info("Successfully connected to PostgreSQL database!")
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            return engine
        except Exception as e:
            logger.warning(f"Failed to connect to PostgreSQL database: {e}. Falling back to SQLite.")
            
    # Fall back to SQLite
    sqlite_url = "sqlite:///./resume_matcher.db"
    logger.info(f"Initializing SQLite database at {sqlite_url}...")
    # SQLite needs check_same_thread=False for multithreading in FastAPI
    engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine

# Initialize the engine
engine = init_database()

def get_db():
    if SessionLocal is None:
        init_database()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

import logging
import random
from typing import List
from backend.app.config import settings

logger = logging.getLogger("app.services.embedding_service")

class EmbeddingService:
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        self.mock_mode = settings.MOCK_AI
        self.model = None
        self.vector_dim = 1024  # Qwen3-Embedding-0.6B standard dimension
        
        if self.mock_mode:
            logger.info("EmbeddingService initialized in MOCK MODE.")
        else:
            logger.info("EmbeddingService initialized. Model will be lazy-loaded on the first analysis run.")

    def _load_model(self):
        if self.model is None and not self.mock_mode:
            logger.info(f"EmbeddingService loading model: {self.model_name}...")
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(self.model_name, trust_remote_code=True)
                self.vector_dim = self.model.get_sentence_embedding_dimension()
                logger.info(f"EmbeddingService successfully loaded embedding model! Vector dimension: {self.vector_dim}")
            except Exception as e:
                logger.error(f"Failed to load local embedding model {self.model_name}: {e}. Falling back to Mock Mode.")
                self.mock_mode = True

    def embed_text(self, text: str) -> List[float]:
        """Generate vector embedding for a single text string."""
        self._load_model()
        if self.mock_mode or not self.model:
            # Generate deterministic-ish random floats for mock mode
            random.seed(hash(text))
            return [random.uniform(-0.1, 0.1) for _ in range(self.vector_dim)]
            
        try:
            embedding = self.model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}. Generating mock vector.")
            random.seed(hash(text))
            return [random.uniform(-0.1, 0.1) for _ in range(self.vector_dim)]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a list of text strings."""
        self._load_model()
        if self.mock_mode or not self.model:
            return [self.embed_text(t) for t in texts]
            
        try:
            embeddings = self.model.encode(texts, normalize_embeddings=True, batch_size=16)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}. Generating mock vectors.")
            return [self.embed_text(t) for t in texts]

# Initialize service instance
embedding_service = EmbeddingService()

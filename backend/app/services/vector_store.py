import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from backend.app.config import settings

logger = logging.getLogger("app.services.vector_store")

class VectorStore:
    def __init__(self):
        self.qdrant_url = settings.QDRANT_URL
        self.qdrant_key = settings.QDRANT_API_KEY
        self.client = None
        
        # Try connecting to Qdrant server
        try:
            logger.info(f"Connecting to Qdrant server at {self.qdrant_url}...")
            # Use a quick test client to verify availability
            test_client = QdrantClient(url=self.qdrant_url, api_key=self.qdrant_key, timeout=3.0)
            test_client.get_collections()
            # If successful, initialize the main client with a healthy timeout of 20 seconds
            self.client = QdrantClient(url=self.qdrant_url, api_key=self.qdrant_key, timeout=20.0)
            logger.info("Successfully connected to external Qdrant server!")
        except Exception as e:
            logger.warning(
                f"Failed to connect to Qdrant server: {e}. "
                "Falling back to local in-memory Qdrant client."
            )
            # Fall back to in-memory instance
            self.client = QdrantClient(":memory:")

    def recreate_collection(self, collection_name: str, vector_size: int):
        """Delete and recreate collection for clean indexing."""
        try:
            if self.client.collection_exists(collection_name):
                self.client.delete_collection(collection_name)
            
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=qmodels.VectorParams(
                    size=vector_size,
                    distance=qmodels.Distance.COSINE
                )
            )
            logger.info(f"Recreated Qdrant collection: '{collection_name}'")
            
            # Create payload indexes required by Qdrant Cloud cluster configuration
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name="document_id",
                field_schema=qmodels.PayloadSchemaType.INTEGER
            )
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name="document_type",
                field_schema=qmodels.PayloadSchemaType.KEYWORD
            )
            logger.info(f"Created payload indexes on 'document_id' and 'document_type'")
        except Exception as e:
            logger.error(f"Error recreating Qdrant collection: {e}")
            raise

    def index_chunks(
        self, 
        collection_name: str, 
        chunks: List[str], 
        metadata_list: List[Dict[str, Any]], 
        embeddings: List[List[float]]
    ):
        """Index text chunks with their metadata and embeddings into Qdrant."""
        if not chunks:
            return
            
        import uuid
        points = []
        for i, (chunk, meta, emb) in enumerate(zip(chunks, metadata_list, embeddings)):
            doc_id = meta.get("document_id", 0)
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{collection_name}_{doc_id}_{i}_{chunk[:30]}"))
            points.append(
                qmodels.PointStruct(
                    id=point_id,
                    vector=emb,
                    payload={
                        "text": chunk,
                        **meta
                    }
                )
            )
            
        try:
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            logger.info(f"Successfully indexed {len(points)} chunks in '{collection_name}' collection.")
        except Exception as e:
            logger.error(f"Failed to index points: {e}")
            raise

    def search_similar_chunks(
        self, 
        collection_name: str, 
        query_vector: List[float], 
        filter_doc_id: int, 
        doc_type: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve most similar chunks filtered by document_id and document_type."""
        try:
            # Query filter to narrow search to current document analysis context
            query_filter = qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="document_id",
                        match=qmodels.MatchValue(value=filter_doc_id)
                    ),
                    qmodels.FieldCondition(
                        key="document_type",
                        match=qmodels.MatchValue(value=doc_type)
                    )
                ]
            )
            
            search_results = self.client.query_points(
                collection_name=collection_name,
                query=query_vector,
                query_filter=query_filter,
                limit=limit
            )
            
            results = []
            for hit in search_results.points:
                results.append({
                    "text": hit.payload.get("text", ""),
                    "score": hit.score,
                    "metadata": {k: v for k, v in hit.payload.items() if k != "text"}
                })
            return results
        except Exception as e:
            logger.error(f"Error during Qdrant vector search: {e}")
            return []

# Initialize service instance
vector_store = VectorStore()

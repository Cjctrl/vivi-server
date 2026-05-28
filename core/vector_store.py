"""
Singleton VectorStore and embedding cache service for Qdrant.
"""

from __future__ import annotations

import hashlib
import os
import threading
import uuid
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import structlog
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, ScoredPoint
from qdrant_client.models import Distance, VectorParams

from config.settings import EMBED_MODEL, MEMORY_DB_PATH, VECTOR_DIMENSION
from core.ollama_client import EmbeddingDimensionError, get_client

logger = structlog.get_logger(__name__).bind(component="core")


class EmbeddingService:
    """Caching embedding service using nomic-embed-text."""

    # Max concurrent embedding requests issued by embed_batch. The Ollama
    # embeddings endpoint takes one input per call, so true batching isn't
    # possible — but the calls are independent network round-trips, so running
    # a bounded number in parallel cuts wall-clock time roughly N-fold.
    _BATCH_WORKERS = 8

    def __init__(self, model: str = EMBED_MODEL, dimension: int = VECTOR_DIMENSION) -> None:
        self.model = model
        self.dimension = dimension
        self._cache: OrderedDict[str, List[float]] = OrderedDict()
        self._max_cache_size = 50_000
        # Guards _cache so embed() is safe to call from embed_batch's worker
        # threads. Only the in-memory dict ops are locked; the network call
        # stays outside the lock so embeds still run in parallel.
        self._cache_lock = threading.Lock()
        self._client = get_client()

    def embed(self, text: str) -> List[float]:
        """Embed a single text string, using an in-memory LRU cache."""
        cache_key = hashlib.sha256(text.encode("utf-8")).hexdigest()
        with self._cache_lock:
            if cache_key in self._cache:
                self._cache.move_to_end(cache_key)
                return self._cache[cache_key]

        vector = self._client.embed(self.model, text)
        if len(vector) != self.dimension:
            raise EmbeddingDimensionError(
                f"Embedding dimension mismatch: expected {self.dimension}, got {len(vector)}"
            )

        with self._cache_lock:
            self._cache[cache_key] = vector
            if len(self._cache) > self._max_cache_size:
                self._cache.popitem(last=False)
        return vector

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts, running the calls in parallel.

        The embedding calls are synchronous network round-trips, so a
        ThreadPoolExecutor is used to overlap them. Results are returned in the
        same order as the input texts.
        """
        if not texts:
            return []
        if len(texts) == 1:
            return [self.embed(texts[0])]

        workers = min(self._BATCH_WORKERS, len(texts))
        logger.debug("Embedding batch of %d texts with %d workers", len(texts), workers)
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="embed") as pool:
            # executor.map preserves input order in its results.
            return list(pool.map(self.embed, texts))


class VectorStore:
    """Singleton wrapper for a local Qdrant client."""

    _instances: Dict[tuple, "VectorStore"] = {}

    def __new__(cls, db_path: Optional[Path] = None) -> "VectorStore":
        key = (cls, db_path)
        if key not in cls._instances:
            instance = super().__new__(cls)
            instance._initialized = False
            cls._instances[key] = instance
        return cls._instances[key]

    def __init__(self, db_path: Optional[Path] = None) -> None:
        if getattr(self, "_initialized", False):
            return
        qdrant_url = os.getenv("QDRANT_URL")
        if qdrant_url:
            # Local Qdrant server — set QDRANT_URL=http://localhost:6333
            # Start with: docker run -p 6333:6333 -v ./memory/qdrant:/qdrant/storage qdrant/qdrant
            self.client = QdrantClient(url=qdrant_url)
            logger.info("VectorStore connected to Qdrant server at %s", qdrant_url)
        else:
            if db_path is None:
                db_path = Path(MEMORY_DB_PATH)
            db_path.mkdir(parents=True, exist_ok=True)
            self.client = QdrantClient(path=str(db_path))
            logger.info("VectorStore initialized at %s", db_path)
        self._initialized = True

    def ensure_collection(self, name: str, vector_size: int = VECTOR_DIMENSION) -> None:
        """Create the collection if it does not already exist."""
        try:
            self.client.get_collection(name)
        except Exception:
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            logger.info("Created Qdrant collection %s", name)

    def upsert_points(self, collection: str, points: List[PointStruct]) -> None:
        """Upsert points into the specified collection."""
        if not points:
            return
        self.client.upsert(collection_name=collection, points=points)

    def search(
        self,
        collection: str,
        query_vector: List[float],
        limit: int,
        score_threshold: float = 0.0,
    ) -> List[ScoredPoint]:
        """Search the vector store and return scored points."""
        try:
            results = self.client.query_points(
                collection_name=collection,
                query_vector=query_vector,
                limit=limit,
                with_payload=True,
                score_threshold=score_threshold,
            )
            return results.points
        except TypeError:
            results = self.client.query_points(
                collection_name=collection,
                query=query_vector,
                limit=limit,
                with_payload=True,
                score_threshold=score_threshold,
            )
            return results.points
        except Exception as exc:
            logger.error("Qdrant search failed for collection %s: %s", collection, exc)
            raise

    def count(self, collection: str) -> int:
        """Return the number of points in the collection."""
        try:
            count_result = self.client.count(collection_name=collection)
            return int(getattr(count_result, "count", 0))
        except Exception:
            return 0

    def collection_exists(self, name: str) -> bool:
        """Return whether the collection exists."""
        try:
            self.client.get_collection(name)
            return True
        except Exception:
            return False

    def get_point(self, collection: str, point_id: str) -> Optional[PointStruct]:
        """Retrieve a single point by ID."""
        try:
            points = self.client.retrieve(collection_name=collection, ids=[point_id])
            return points[0] if points else None
        except Exception:
            return None

    def batch_exists(self, collection: str, point_ids: List[str]) -> Set[str]:
        """Return the set of point IDs that already exist in the collection."""
        if not point_ids:
            return set()
        try:
            points = self.client.retrieve(
                collection_name=collection,
                ids=point_ids,
                with_payload=False,
                with_vectors=False,
            )
            return {str(p.id) for p in points}
        except Exception:
            return set()


_embedding_service_instance: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Return the shared singleton EmbeddingService instance."""
    global _embedding_service_instance
    if _embedding_service_instance is None:
        _embedding_service_instance = EmbeddingService()
    return _embedding_service_instance


def get_vector_store(db_path: Optional[Path] = None) -> VectorStore:
    """Return the singleton Qdrant vector store instance."""
    return VectorStore(db_path)

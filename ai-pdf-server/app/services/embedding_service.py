"""Embedding generation service using OpenAI."""

import asyncio
from typing import List, Optional

import numpy as np
from openai import AsyncOpenAI, OpenAIError

from app.core.config import settings
from app.utils.helpers import get_logger

logger = get_logger(__name__)

# Batch size for embedding requests (OpenAI limit is ~2048 for text-embedding-3)
MAX_BATCH_SIZE = 100
MAX_RETRIES = 3
RETRY_DELAY = 1.0


class EmbeddingService:
    """Service for generating embeddings using OpenAI API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize embedding service.

        Args:
            api_key: OpenAI API key (defaults to settings)
            model: Embedding model name (defaults to settings)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.EMBEDDING_MODEL
        self.dimensions = settings.EMBEDDING_DIMENSIONS

        if not self.api_key:
            logger.warning("OpenAI API key not configured")

        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None

    async def generate_embedding(
        self,
        text: str,
        retry_count: int = 0,
    ) -> np.ndarray:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed
            retry_count: Current retry attempt

        Returns:
            Embedding vector as numpy array
        """
        if not self.client:
            raise ValueError("OpenAI client not initialized. Check API key.")

        if not text.strip():
            raise ValueError("Cannot generate embedding for empty text")

        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
            )

            embedding = response.data[0].embedding
            return np.array(embedding, dtype=np.float32)

        except OpenAIError as e:
            logger.error(
                "OpenAI embedding error",
                error=str(e),
                retry_count=retry_count,
            )

            if retry_count < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY * (retry_count + 1))
                return await self.generate_embedding(text, retry_count + 1)

            raise

    async def generate_embeddings_batch(
        self,
        texts: List[str],
    ) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts efficiently.

        Handles batching and rate limiting automatically.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors as numpy arrays
        """
        if not self.client:
            raise ValueError("OpenAI client not initialized. Check API key.")

        if not texts:
            return []

        # Filter empty texts but track indices
        valid_texts = []
        valid_indices = []
        for i, text in enumerate(texts):
            if text.strip():
                valid_texts.append(text)
                valid_indices.append(i)

        if not valid_texts:
            return [np.zeros(self.dimensions, dtype=np.float32) for _ in texts]

        logger.info(
            "Generating batch embeddings",
            total_texts=len(texts),
            valid_texts=len(valid_texts),
        )

        all_embeddings = []

        # Process in batches
        for batch_start in range(0, len(valid_texts), MAX_BATCH_SIZE):
            batch_end = min(batch_start + MAX_BATCH_SIZE, len(valid_texts))
            batch = valid_texts[batch_start:batch_end]

            batch_embeddings = await self._process_batch(batch)
            all_embeddings.extend(batch_embeddings)

            # Small delay between batches to avoid rate limiting
            if batch_end < len(valid_texts):
                await asyncio.sleep(0.1)

        # Reconstruct full list with zeros for empty texts
        result = [np.zeros(self.dimensions, dtype=np.float32) for _ in texts]
        for i, embedding in zip(valid_indices, all_embeddings):
            result[i] = embedding

        logger.info(
            "Batch embedding complete",
            embeddings_generated=len(all_embeddings),
        )

        return result

    async def _process_batch(
        self,
        texts: List[str],
        retry_count: int = 0,
    ) -> List[np.ndarray]:
        """
        Process a single batch of texts.

        Args:
            texts: Batch of texts to embed
            retry_count: Current retry attempt

        Returns:
            List of embedding vectors
        """
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts,
            )

            # Sort by index to maintain order
            sorted_data = sorted(response.data, key=lambda x: x.index)
            embeddings = [
                np.array(item.embedding, dtype=np.float32) for item in sorted_data
            ]

            return embeddings

        except OpenAIError as e:
            logger.error(
                "OpenAI batch embedding error",
                error=str(e),
                batch_size=len(texts),
                retry_count=retry_count,
            )

            if retry_count < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY * (retry_count + 1))
                return await self._process_batch(texts, retry_count + 1)

            raise

    async def cosine_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray,
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (0-1)
        """
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def normalize_embedding(self, embedding: np.ndarray) -> np.ndarray:
        """
        Normalize embedding vector to unit length.

        Args:
            embedding: Embedding vector

        Returns:
            Normalized embedding
        """
        norm = np.linalg.norm(embedding)
        if norm == 0:
            return embedding
        return embedding / norm

    async def health_check(self) -> bool:
        """
        Check if the embedding service is healthy.

        Returns:
            True if service is operational
        """
        try:
            test_embedding = await self.generate_embedding("test")
            return len(test_embedding) == self.dimensions
        except Exception as e:
            logger.error("Embedding service health check failed", error=str(e))
            return False


# Singleton instance
embedding_service = EmbeddingService()

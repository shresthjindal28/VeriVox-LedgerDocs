"""Vector store service using FAISS."""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import faiss
import numpy as np

from app.core.config import settings
from app.models.schemas import DocumentMetadata, TextChunk
from app.utils.helpers import get_logger, load_json_async, save_json_async

logger = get_logger(__name__)


@dataclass
class SearchResult:
    """Result from vector similarity search."""

    chunk: TextChunk
    score: float
    rank: int


@dataclass
class DocumentIndex:
    """Represents a document's FAISS index and metadata."""

    document_id: str
    index: faiss.Index
    chunks: List[TextChunk]
    metadata: DocumentMetadata


class VectorStore:
    """
    Vector store using FAISS for similarity search.

    Supports document-scoped indices for isolation.
    Designed for future migration to pgvector or Pinecone.
    """

    def __init__(
        self,
        index_dir: Optional[Path] = None,
        metadata_dir: Optional[Path] = None,
        dimensions: int = None,
    ):
        """
        Initialize vector store.

        Args:
            index_dir: Directory for FAISS indices
            metadata_dir: Directory for metadata storage
            dimensions: Embedding dimensions
        """
        self.index_dir = index_dir or settings.INDEX_DIR
        self.metadata_dir = metadata_dir or settings.METADATA_DIR
        self.dimensions = dimensions or settings.EMBEDDING_DIMENSIONS

        # In-memory cache of loaded indices
        self._indices: Dict[str, DocumentIndex] = {}

        # Ensure directories exist
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def _create_index(self) -> faiss.Index:
        """
        Create a new FAISS index.

        Uses IndexFlatIP (Inner Product) for cosine similarity with normalized vectors.

        Returns:
            New FAISS index
        """
        # Using L2 distance for simplicity; can switch to IP with normalized vectors
        index = faiss.IndexFlatL2(self.dimensions)
        return index

    async def add_document(
        self,
        document_id: str,
        chunks: List[TextChunk],
        embeddings: List[np.ndarray],
        metadata: DocumentMetadata,
    ) -> bool:
        """
        Add a document with its chunks and embeddings to the store.

        Args:
            document_id: Unique document identifier
            chunks: List of text chunks
            embeddings: Corresponding embedding vectors
            metadata: Document metadata

        Returns:
            True if successful
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings must have same length")

        if not chunks:
            raise ValueError("Cannot add document with no chunks")

        logger.info(
            "Adding document to vector store",
            document_id=document_id,
            chunk_count=len(chunks),
        )

        # Create new index
        index = self._create_index()

        # Stack embeddings into matrix
        embedding_matrix = np.vstack(embeddings).astype(np.float32)

        # Add to index
        index.add(embedding_matrix)

        # Create document index object
        doc_index = DocumentIndex(
            document_id=document_id,
            index=index,
            chunks=chunks,
            metadata=metadata,
        )

        # Cache in memory
        self._indices[document_id] = doc_index

        # Persist to disk
        await self._save_index(document_id)
        await self._save_metadata(document_id, metadata, chunks)

        logger.info(
            "Document added to vector store",
            document_id=document_id,
            vectors_added=index.ntotal,
        )

        return True

    async def search(
        self,
        document_id: str,
        query_embedding: np.ndarray,
        top_k: int = None,
    ) -> List[SearchResult]:
        """
        Search for similar chunks in a document.

        Args:
            document_id: Document to search in
            query_embedding: Query embedding vector
            top_k: Number of results to return

        Returns:
            List of SearchResult objects sorted by relevance
        """
        top_k = top_k or settings.TOP_K_RESULTS

        # Load index if not cached
        if document_id not in self._indices:
            loaded = await self._load_index(document_id)
            if not loaded:
                raise ValueError(f"Document not found: {document_id}")

        doc_index = self._indices[document_id]

        # Ensure query is correct shape
        query = query_embedding.reshape(1, -1).astype(np.float32)

        # Limit top_k to available vectors
        k = min(top_k, doc_index.index.ntotal)

        # Search
        distances, indices = doc_index.index.search(query, k)

        # Convert to SearchResult objects
        results = []
        for rank, (idx, distance) in enumerate(zip(indices[0], distances[0])):
            if idx < 0:  # FAISS returns -1 for invalid indices
                continue

            # Convert L2 distance to similarity score (0-1)
            # Lower distance = higher similarity
            max_distance = 4.0  # Approximate max L2 distance for normalized embeddings
            score = max(0.0, 1.0 - (distance / max_distance))

            results.append(
                SearchResult(
                    chunk=doc_index.chunks[idx],
                    score=float(score),
                    rank=rank + 1,
                )
            )

        logger.debug(
            "Vector search complete",
            document_id=document_id,
            results=len(results),
        )

        return results

    async def get_document_metadata(
        self,
        document_id: str,
    ) -> Optional[DocumentMetadata]:
        """
        Get metadata for a document.

        Args:
            document_id: Document ID

        Returns:
            DocumentMetadata or None if not found
        """
        if document_id in self._indices:
            return self._indices[document_id].metadata

        # Try to load from disk
        metadata_path = self.metadata_dir / f"{document_id}_metadata.json"
        data = await load_json_async(metadata_path)

        if data and "metadata" in data:
            return DocumentMetadata(**data["metadata"])

        return None

    async def document_exists(self, document_id: str) -> bool:
        """
        Check if a document exists in the store.

        Args:
            document_id: Document ID

        Returns:
            True if document exists
        """
        if document_id in self._indices:
            return True

        # Check disk
        index_path = self.index_dir / f"{document_id}.index"
        return index_path.exists()

    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the store.

        Args:
            document_id: Document ID

        Returns:
            True if deleted, False if not found
        """
        # Remove from cache
        if document_id in self._indices:
            del self._indices[document_id]

        # Remove from disk
        from app.utils.helpers import delete_file_async

        index_path = self.index_dir / f"{document_id}.index"
        metadata_path = self.metadata_dir / f"{document_id}_metadata.json"

        index_deleted = await delete_file_async(index_path)
        metadata_deleted = await delete_file_async(metadata_path)

        if index_deleted or metadata_deleted:
            logger.info("Document deleted from vector store", document_id=document_id)
            return True

        logger.warning("Document not found for deletion", document_id=document_id)
        return False

    async def list_documents(self) -> List[DocumentMetadata]:
        """
        List all documents in the store.

        Returns:
            List of DocumentMetadata objects
        """
        documents = []

        # Scan metadata directory
        for metadata_file in self.metadata_dir.glob("*_metadata.json"):
            data = await load_json_async(metadata_file)
            if data and "metadata" in data:
                documents.append(DocumentMetadata(**data["metadata"]))

        return documents

    async def get_all_chunks(
        self,
        document_id: str,
        max_chunks: int = 200,
    ) -> List[TextChunk]:
        """
        Get all chunks for a document (for exhaustive extraction).
        
        Args:
            document_id: Document ID
            max_chunks: Maximum number of chunks to return
            
        Returns:
            List of all TextChunk objects for the document
        """
        # Load index if not cached
        if document_id not in self._indices:
            loaded = await self._load_index(document_id)
            if not loaded:
                logger.warning(f"Document not found for get_all_chunks: {document_id}")
                return []
        
        doc_index = self._indices.get(document_id)
        if not doc_index:
            return []
        
        chunks = doc_index.chunks[:max_chunks]
        logger.debug(
            "Retrieved all chunks",
            document_id=document_id,
            chunk_count=len(chunks),
        )
        return chunks

    async def get_chunks_by_page(
        self,
        document_id: str,
        page_number: int,
    ) -> List[TextChunk]:
        """
        Get all chunks for a specific page.
        
        Args:
            document_id: Document ID
            page_number: Page number (1-indexed)
            
        Returns:
            List of chunks on that page
        """
        all_chunks = await self.get_all_chunks(document_id)
        return [c for c in all_chunks if c.page_number == page_number]

    async def _save_index(self, document_id: str) -> None:
        """Save FAISS index to disk."""
        if document_id not in self._indices:
            return

        index_path = self.index_dir / f"{document_id}.index"
        faiss.write_index(self._indices[document_id].index, str(index_path))

        logger.debug("FAISS index saved", document_id=document_id)

    async def _save_metadata(
        self,
        document_id: str,
        metadata: DocumentMetadata,
        chunks: List[TextChunk],
    ) -> None:
        """Save document metadata and chunks to disk."""
        metadata_path = self.metadata_dir / f"{document_id}_metadata.json"

        data = {
            "metadata": metadata.model_dump(),
            "chunks": [chunk.model_dump() for chunk in chunks],
        }

        await save_json_async(metadata_path, data)
        logger.debug("Metadata saved", document_id=document_id)

    async def _load_index(self, document_id: str) -> bool:
        """
        Load a document index from disk.

        Args:
            document_id: Document ID to load

        Returns:
            True if loaded successfully
        """
        index_path = self.index_dir / f"{document_id}.index"
        metadata_path = self.metadata_dir / f"{document_id}_metadata.json"

        if not index_path.exists() or not metadata_path.exists():
            return False

        try:
            # Load FAISS index
            index = faiss.read_index(str(index_path))

            # Load metadata and chunks
            data = await load_json_async(metadata_path)
            if not data:
                return False

            metadata = DocumentMetadata(**data["metadata"])
            chunks = [TextChunk(**chunk) for chunk in data["chunks"]]

            # Cache in memory
            self._indices[document_id] = DocumentIndex(
                document_id=document_id,
                index=index,
                chunks=chunks,
                metadata=metadata,
            )

            logger.debug("Index loaded from disk", document_id=document_id)
            return True

        except Exception as e:
            logger.error(
                "Failed to load index",
                document_id=document_id,
                error=str(e),
            )
            return False

    async def preload_all_indices(self) -> int:
        """
        Preload all indices into memory.

        Returns:
            Number of indices loaded
        """
        count = 0
        for index_file in self.index_dir.glob("*.index"):
            document_id = index_file.stem
            if await self._load_index(document_id):
                count += 1

        logger.info("Preloaded indices", count=count)
        return count

    def get_stats(self) -> Dict:
        """
        Get vector store statistics.

        Returns:
            Dictionary with store statistics
        """
        total_vectors = sum(
            doc.index.ntotal for doc in self._indices.values()
        )
        return {
            "documents_cached": len(self._indices),
            "total_vectors": total_vectors,
            "dimensions": self.dimensions,
        }


# Singleton instance
vector_store = VectorStore()

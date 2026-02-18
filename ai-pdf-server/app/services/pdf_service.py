"""PDF processing service for text extraction and chunking."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import fitz  # PyMuPDF

from app.core.config import settings
from app.models.schemas import TextChunk
from app.utils.helpers import (
    clean_text,
    compute_sha256,
    generate_chunk_id,
    generate_document_id,
    get_logger,
    save_file_async,
)

logger = get_logger(__name__)

# Thread pool for CPU-bound PDF operations
_executor = ThreadPoolExecutor(max_workers=4)


@dataclass
class BoundingBox:
    """Represents a bounding box on a page."""
    x1: float
    y1: float
    x2: float
    y2: float
    
    def to_dict(self) -> dict:
        return {"x1": self.x1, "y1": self.y1, "x2": self.x2, "y2": self.y2}


@dataclass
class TextBlock:
    """Represents a text block with position information."""
    text: str
    page_number: int
    char_start: int  # Character offset within page
    char_end: int
    bounding_box: BoundingBox


@dataclass
class PageText:
    """Represents extracted text from a single page."""

    page_number: int
    text: str
    char_count: int
    text_blocks: List[TextBlock] = None  # Optional positional data


@dataclass
class PDFExtractionResult:
    """Result of PDF text extraction."""

    pages: List[PageText]
    page_count: int
    total_chars: int
    sha256_hash: str
    has_positions: bool = False  # Whether position data is available


class PDFService:
    """Service for PDF processing operations."""

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
    ):
        """
        Initialize PDF service.

        Args:
            chunk_size: Size of text chunks (defaults to settings)
            chunk_overlap: Overlap between chunks (defaults to settings)
        """
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.upload_dir = settings.UPLOAD_DIR

    def _extract_text_sync(
        self, file_bytes: bytes, extract_positions: bool = True
    ) -> PDFExtractionResult:
        """
        Synchronous PDF text extraction (runs in thread pool).

        Args:
            file_bytes: PDF file content as bytes
            extract_positions: Whether to extract text position data

        Returns:
            PDFExtractionResult with extracted text and metadata
        """
        pages: List[PageText] = []
        total_chars = 0

        # Open PDF from bytes
        doc = fitz.open(stream=file_bytes, filetype="pdf")

        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text")
                cleaned = clean_text(text)

                text_blocks = []
                if extract_positions:
                    # Extract text with position information using "dict" mode
                    try:
                        page_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
                        char_offset = 0
                        
                        for block in page_dict.get("blocks", []):
                            if block.get("type") != 0:  # Only text blocks
                                continue
                            
                            for line in block.get("lines", []):
                                for span in line.get("spans", []):
                                    span_text = span.get("text", "")
                                    if not span_text.strip():
                                        continue
                                    
                                    bbox = span.get("bbox", [0, 0, 0, 0])
                                    text_blocks.append(TextBlock(
                                        text=span_text,
                                        page_number=page_num + 1,
                                        char_start=char_offset,
                                        char_end=char_offset + len(span_text),
                                        bounding_box=BoundingBox(
                                            x1=bbox[0],
                                            y1=bbox[1],
                                            x2=bbox[2],
                                            y2=bbox[3],
                                        ),
                                    ))
                                    char_offset += len(span_text)
                    except Exception as e:
                        logger.warning(f"Failed to extract positions for page {page_num + 1}: {e}")

                pages.append(
                    PageText(
                        page_number=page_num + 1,  # 1-indexed
                        text=cleaned,
                        char_count=len(cleaned),
                        text_blocks=text_blocks if text_blocks else None,
                    )
                )
                total_chars += len(cleaned)

            sha256_hash = compute_sha256(file_bytes)

            return PDFExtractionResult(
                pages=pages,
                page_count=len(doc),
                total_chars=total_chars,
                sha256_hash=sha256_hash,
                has_positions=extract_positions,
            )

        finally:
            doc.close()

    async def extract_text_with_pages(
        self, file_bytes: bytes
    ) -> PDFExtractionResult:
        """
        Extract text from PDF with page information.

        Args:
            file_bytes: PDF file content as bytes

        Returns:
            PDFExtractionResult with all extracted text and metadata
        """
        logger.info("Starting PDF text extraction")

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            _executor, self._extract_text_sync, file_bytes
        )

        logger.info(
            "PDF extraction complete",
            page_count=result.page_count,
            total_chars=result.total_chars,
        )

        return result

    def chunk_text(
        self,
        pages: List[PageText],
        document_id: str,
    ) -> List[TextChunk]:
        """
        Chunk extracted text into smaller segments.

        Uses configurable chunk size and overlap for better RAG retrieval.

        Args:
            pages: List of PageText objects
            document_id: Document ID for chunk ID generation

        Returns:
            List of TextChunk objects
        """
        chunks: List[TextChunk] = []
        chunk_index = 0

        for page in pages:
            if not page.text.strip():
                continue

            text = page.text
            start = 0

            while start < len(text):
                # Calculate end position
                end = start + self.chunk_size

                # Try to break at sentence boundary
                if end < len(text):
                    # Look for sentence endings
                    for sep in [". ", "! ", "? ", "\n\n", "\n"]:
                        last_sep = text[start:end].rfind(sep)
                        if last_sep > self.chunk_size // 2:
                            end = start + last_sep + len(sep)
                            break

                chunk_text = text[start:end].strip()

                if chunk_text:
                    chunk_id = generate_chunk_id(document_id, page.page_number, chunk_index)

                    chunks.append(
                        TextChunk(
                            chunk_id=chunk_id,
                            page_number=page.page_number,
                            text_content=chunk_text,
                            start_index=start,
                            end_index=end,
                        )
                    )
                    chunk_index += 1

                # Move start position with overlap
                start = end - self.chunk_overlap
                if start <= 0 or start >= end:
                    start = end

        logger.info(
            "Text chunking complete",
            chunk_count=len(chunks),
            chunk_size=self.chunk_size,
            overlap=self.chunk_overlap,
        )

        return chunks

    async def save_pdf(self, file_bytes: bytes, document_id: str) -> Path:
        """
        Save uploaded PDF to storage.

        Args:
            file_bytes: PDF content
            document_id: Document ID for naming

        Returns:
            Path where file was saved
        """
        file_path = self.upload_dir / f"{document_id}.pdf"
        await save_file_async(file_path, file_bytes)

        logger.info("PDF saved", document_id=document_id, path=str(file_path))
        return file_path

    async def process_pdf(
        self,
        file_bytes: bytes,
        filename: str,
    ) -> Tuple[str, PDFExtractionResult, List[TextChunk]]:
        """
        Complete PDF processing pipeline.

        Args:
            file_bytes: PDF file content
            filename: Original filename

        Returns:
            Tuple of (document_id, extraction_result, chunks)
        """
        # Generate document ID
        document_id = generate_document_id()

        logger.info(
            "Processing PDF",
            document_id=document_id,
            filename=filename,
            size_bytes=len(file_bytes),
        )

        # Extract text
        extraction_result = await self.extract_text_with_pages(file_bytes)

        # Create chunks
        chunks = self.chunk_text(extraction_result.pages, document_id)

        # Save PDF
        await self.save_pdf(file_bytes, document_id)

        logger.info(
            "PDF processing complete",
            document_id=document_id,
            pages=extraction_result.page_count,
            chunks=len(chunks),
        )

        return document_id, extraction_result, chunks

    async def get_pdf_path(self, document_id: str) -> Path:
        """
        Get the storage path for a document.

        Args:
            document_id: Document ID

        Returns:
            Path to the PDF file
        """
        return self.upload_dir / f"{document_id}.pdf"

    async def delete_pdf(self, document_id: str) -> bool:
        """
        Delete a stored PDF.

        Args:
            document_id: Document ID

        Returns:
            True if deleted, False if not found
        """
        from app.utils.helpers import delete_file_async

        file_path = await self.get_pdf_path(document_id)
        result = await delete_file_async(file_path)

        if result:
            logger.info("PDF deleted", document_id=document_id)
        else:
            logger.warning("PDF not found for deletion", document_id=document_id)

        return result

    async def find_text_positions(
        self,
        document_id: str,
        search_text: str,
        page_number: Optional[int] = None,
    ) -> List[dict]:
        """
        Find the positions of text in a PDF document.
        
        Args:
            document_id: Document ID
            search_text: Text to search for
            page_number: Optional specific page to search
            
        Returns:
            List of position dictionaries with page, bounding_box
        """
        pdf_path = await self.get_pdf_path(document_id)
        if not pdf_path.exists():
            logger.warning(f"PDF not found: {document_id}")
            return []
        
        positions = []
        
        try:
            loop = asyncio.get_event_loop()
            positions = await loop.run_in_executor(
                _executor,
                self._find_text_positions_sync,
                pdf_path,
                search_text,
                page_number,
            )
        except Exception as e:
            logger.error(f"Error finding text positions: {e}")
        
        return positions
    
    def _find_text_positions_sync(
        self,
        pdf_path: Path,
        search_text: str,
        page_number: Optional[int],
    ) -> List[dict]:
        """Synchronous text position search."""
        positions = []
        doc = fitz.open(str(pdf_path))
        
        try:
            pages_to_search = range(len(doc))
            if page_number is not None:
                pages_to_search = [page_number - 1]  # 0-indexed
            
            for page_idx in pages_to_search:
                if page_idx < 0 or page_idx >= len(doc):
                    continue
                    
                page = doc[page_idx]
                
                # Search for text instances
                text_instances = page.search_for(search_text)
                
                for rect in text_instances:
                    positions.append({
                        "page": page_idx + 1,
                        "bounding_box": {
                            "x1": rect.x0,
                            "y1": rect.y0,
                            "x2": rect.x1,
                            "y2": rect.y1,
                        },
                        "text": search_text,
                        # Normalize to percentage for responsive display
                        "normalized": {
                            "x1": rect.x0 / page.rect.width,
                            "y1": rect.y0 / page.rect.height,
                            "x2": rect.x1 / page.rect.width,
                            "y2": rect.y1 / page.rect.height,
                        }
                    })
        finally:
            doc.close()
        
        return positions

    async def get_page_dimensions(self, document_id: str) -> List[dict]:
        """
        Get dimensions of all pages in a PDF.
        
        Args:
            document_id: Document ID
            
        Returns:
            List of page dimension dictionaries
        """
        pdf_path = await self.get_pdf_path(document_id)
        if not pdf_path.exists():
            return []
        
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                _executor,
                self._get_page_dimensions_sync,
                pdf_path,
            )
        except Exception as e:
            logger.error(f"Error getting page dimensions: {e}")
            return []
    
    def _get_page_dimensions_sync(self, pdf_path: Path) -> List[dict]:
        """Synchronous page dimension extraction."""
        dimensions = []
        doc = fitz.open(str(pdf_path))
        
        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                dimensions.append({
                    "page": page_num + 1,
                    "width": page.rect.width,
                    "height": page.rect.height,
                })
        finally:
            doc.close()
        
        return dimensions


# Singleton instance
pdf_service = PDFService()


# Legacy function for backward compatibility
async def extract_text(file) -> str:
    """
    Legacy function for simple text extraction.

    Args:
        file: UploadFile object

    Returns:
        Extracted text as string
    """
    contents = await file.read()
    result = await pdf_service.extract_text_with_pages(contents)
    return " ".join(page.text for page in result.pages)

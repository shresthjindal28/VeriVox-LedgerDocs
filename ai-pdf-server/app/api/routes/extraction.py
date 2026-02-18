"""API routes for exhaustive extraction and highlighting."""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.rag_service import (
    ExtractionMode,
    ExtractionResult,
    rag_service,
)
from app.services.highlight_service import highlight_service, HighlightSet
from app.utils.helpers import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/extraction", tags=["extraction"])


class ExtractionRequest(BaseModel):
    """Request body for extraction."""
    query: str
    document_id: str
    include_highlights: bool = True


class ExtractionResponse(BaseModel):
    """Response for extraction request."""
    success: bool
    extraction: dict
    highlights: Optional[dict] = None
    answer: str
    message: str = ""


class HighlightRequest(BaseModel):
    """Request body for highlighting."""
    document_id: str
    text: str
    category: Optional[str] = ""


class HighlightResponse(BaseModel):
    """Response for highlight request."""
    success: bool
    highlights: list
    count: int


@router.post("/extract", response_model=ExtractionResponse)
async def extract_from_document(request: ExtractionRequest):
    """
    Perform exhaustive extraction from a document.
    
    This endpoint extracts ALL instances of the requested information
    from the entire document, not just top-K similarity matches.
    """
    try:
        # Perform exhaustive extraction
        extraction_result = await rag_service.extract_all_from_document(
            query=request.query,
            document_id=request.document_id,
        )
        
        # Generate highlights if requested
        highlights = None
        if request.include_highlights and extraction_result.total_count > 0:
            highlight_set = await highlight_service.get_highlights_for_extraction(
                document_id=request.document_id,
                extraction_result=extraction_result,
            )
            highlights = highlight_set.to_dict()
        
        # Format response answer
        answer = rag_service._format_extraction_response(extraction_result)
        
        return ExtractionResponse(
            success=True,
            extraction=extraction_result.to_dict(),
            highlights=highlights,
            answer=answer,
            message=f"Extracted {extraction_result.total_count} items from {extraction_result.pages_scanned} pages",
        )
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/highlight", response_model=HighlightResponse)
async def find_and_highlight(request: HighlightRequest):
    """
    Find text in document and return highlight positions.
    
    This endpoint is useful for ad-hoc highlighting of specific text.
    """
    try:
        highlights = await highlight_service.find_text_and_highlight(
            document_id=request.document_id,
            text=request.text,
            category=request.category or "",
        )
        
        return HighlightResponse(
            success=True,
            highlights=[h.to_dict() for h in highlights],
            count=len(highlights),
        )
        
    except Exception as e:
        logger.error(f"Highlight failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/highlights/{document_id}")
async def get_page_highlights(
    document_id: str,
    page: Optional[int] = None,
):
    """
    Get existing highlights for a document or page.
    """
    from app.services.pdf_service import pdf_service
    
    try:
        dimensions = await pdf_service.get_page_dimensions(document_id)
        
        return {
            "document_id": document_id,
            "pages": dimensions,
            "page_count": len(dimensions),
        }
        
    except Exception as e:
        logger.error(f"Failed to get highlights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

"""Highlight service for PDF text position mapping and synchronization."""

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.services.pdf_service import pdf_service
from app.services.rag_service import ExtractedItem, ExtractionResult
from app.core.config import settings
from app.utils.helpers import get_logger

logger = get_logger(__name__)


@dataclass
class Highlight:
    """Represents a highlight on a PDF page."""
    
    id: str
    text: str
    page: int
    bounding_box: Dict[str, float]  # x1, y1, x2, y2
    normalized_box: Dict[str, float]  # Percentage-based for responsive display
    category: str = ""
    color: str = "#FFFF00"  # Default yellow
    opacity: float = 0.4
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "text": self.text,
            "page": self.page,
            "bounding_box": self.bounding_box,
            "normalized_box": self.normalized_box,
            "category": self.category,
            "color": self.color,
            "opacity": self.opacity,
        }


@dataclass
class HighlightSet:
    """A collection of highlights for a document."""
    
    document_id: str
    highlights: List[Highlight] = field(default_factory=list)
    total_count: int = 0
    pages_covered: List[int] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "document_id": self.document_id,
            "highlights": [h.to_dict() for h in self.highlights],
            "total_count": self.total_count,
            "pages_covered": self.pages_covered,
        }


# Color palette for different categories
CATEGORY_COLORS = {
    "skill": "#FFD700",      # Gold
    "project": "#87CEEB",    # Sky blue
    "certification": "#90EE90",  # Light green
    "experience": "#DDA0DD",  # Plum
    "education": "#F0E68C",   # Khaki
    "contact": "#FFA07A",     # Light salmon
    "default": "#FFFF00",     # Yellow
}


class HighlightService:
    """Service for managing PDF highlights and synchronization."""
    
    def __init__(self):
        """Initialize highlight service."""
        self.merge_threshold = settings.HIGHLIGHT_MERGE_THRESHOLD
    
    async def get_highlights_for_extraction(
        self,
        document_id: str,
        extraction_result: ExtractionResult,
    ) -> HighlightSet:
        """
        Generate highlights for extracted items.
        
        Args:
            document_id: Document ID
            extraction_result: Result from exhaustive extraction
            
        Returns:
            HighlightSet with all highlights
        """
        if not settings.ENABLE_HIGHLIGHT_SYNC:
            logger.warning("Highlight sync disabled")
            return HighlightSet(document_id=document_id)
        
        if not extraction_result.items:
            return HighlightSet(document_id=document_id)
        
        logger.info(
            "Generating highlights",
            document_id=document_id,
            item_count=len(extraction_result.items),
        )
        
        highlights = []
        pages_covered = set()
        
        for item in extraction_result.items:
            # Search for the text in the PDF
            positions = await pdf_service.find_text_positions(
                document_id=document_id,
                search_text=item.text,
                page_number=item.page if item.page > 0 else None,
            )
            
            if not positions:
                # Try with snippet if exact text not found
                if item.snippet and len(item.snippet) > 10:
                    positions = await pdf_service.find_text_positions(
                        document_id=document_id,
                        search_text=item.snippet[:50],  # Use first 50 chars
                        page_number=item.page if item.page > 0 else None,
                    )
            
            for pos in positions:
                highlight_id = self._generate_highlight_id(item, pos)
                color = CATEGORY_COLORS.get(
                    item.category.lower() if item.category else "default",
                    CATEGORY_COLORS["default"]
                )
                
                highlights.append(Highlight(
                    id=highlight_id,
                    text=item.text,
                    page=pos["page"],
                    bounding_box=pos["bounding_box"],
                    normalized_box=pos.get("normalized", pos["bounding_box"]),
                    category=item.category,
                    color=color,
                ))
                pages_covered.add(pos["page"])
        
        # Merge overlapping highlights
        highlights = self._merge_overlapping_highlights(highlights)
        
        result = HighlightSet(
            document_id=document_id,
            highlights=highlights,
            total_count=len(highlights),
            pages_covered=sorted(pages_covered),
        )
        
        logger.info(
            "Highlights generated",
            document_id=document_id,
            highlight_count=len(highlights),
            pages_covered=len(pages_covered),
        )
        
        return result
    
    async def get_highlights_for_answer(
        self,
        document_id: str,
        answer_text: str,
        sources: List[Any],
    ) -> HighlightSet:
        """
        Generate highlights for a conversational answer.
        
        Args:
            document_id: Document ID
            answer_text: The answer text
            sources: Source references from the answer
            
        Returns:
            HighlightSet with source highlights
        """
        highlights = []
        pages_covered = set()
        
        for source in sources:
            # Extract text snippet from source
            snippet = getattr(source, "text", "") or str(source.get("text", ""))
            page = getattr(source, "page", 0) or source.get("page", 0)
            
            if not snippet or len(snippet) < 5:
                continue
            
            # Search for the snippet
            positions = await pdf_service.find_text_positions(
                document_id=document_id,
                search_text=snippet[:100],  # Limit search text length
                page_number=page if page > 0 else None,
            )
            
            for pos in positions:
                highlight_id = hashlib.md5(
                    f"{pos['page']}:{snippet[:20]}".encode()
                ).hexdigest()[:12]
                
                highlights.append(Highlight(
                    id=highlight_id,
                    text=snippet,
                    page=pos["page"],
                    bounding_box=pos["bounding_box"],
                    normalized_box=pos.get("normalized", pos["bounding_box"]),
                    category="source",
                    color="#87CEEB",  # Light blue for sources
                ))
                pages_covered.add(pos["page"])
        
        return HighlightSet(
            document_id=document_id,
            highlights=highlights,
            total_count=len(highlights),
            pages_covered=sorted(pages_covered),
        )
    
    async def find_text_and_highlight(
        self,
        document_id: str,
        text: str,
        category: str = "",
    ) -> List[Highlight]:
        """
        Find text in document and create highlights.
        
        Args:
            document_id: Document ID
            text: Text to find
            category: Optional category for coloring
            
        Returns:
            List of Highlight objects
        """
        positions = await pdf_service.find_text_positions(
            document_id=document_id,
            search_text=text,
        )
        
        highlights = []
        color = CATEGORY_COLORS.get(category.lower(), CATEGORY_COLORS["default"])
        
        for pos in positions:
            highlight_id = hashlib.md5(
                f"{pos['page']}:{text[:20]}".encode()
            ).hexdigest()[:12]
            
            highlights.append(Highlight(
                id=highlight_id,
                text=text,
                page=pos["page"],
                bounding_box=pos["bounding_box"],
                normalized_box=pos.get("normalized", pos["bounding_box"]),
                category=category,
                color=color,
            ))
        
        return highlights
    
    def _generate_highlight_id(self, item: ExtractedItem, position: Dict) -> str:
        """Generate a unique ID for a highlight."""
        content = f"{item.text}:{position['page']}:{position['bounding_box']}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _merge_overlapping_highlights(
        self,
        highlights: List[Highlight],
    ) -> List[Highlight]:
        """
        Merge highlights that overlap significantly.
        
        Args:
            highlights: List of highlights to merge
            
        Returns:
            Merged list of highlights
        """
        if len(highlights) <= 1:
            return highlights
        
        # Group by page
        by_page: Dict[int, List[Highlight]] = {}
        for h in highlights:
            if h.page not in by_page:
                by_page[h.page] = []
            by_page[h.page].append(h)
        
        merged = []
        for page, page_highlights in by_page.items():
            # Sort by y1, then x1
            page_highlights.sort(
                key=lambda h: (h.bounding_box.get("y1", 0), h.bounding_box.get("x1", 0))
            )
            
            current = page_highlights[0]
            for next_h in page_highlights[1:]:
                if self._boxes_overlap(current.bounding_box, next_h.bounding_box):
                    # Merge by expanding current box
                    current = Highlight(
                        id=current.id,
                        text=current.text + " " + next_h.text,
                        page=page,
                        bounding_box=self._merge_boxes(
                            current.bounding_box, next_h.bounding_box
                        ),
                        normalized_box=self._merge_boxes(
                            current.normalized_box, next_h.normalized_box
                        ),
                        category=current.category or next_h.category,
                        color=current.color,
                    )
                else:
                    merged.append(current)
                    current = next_h
            
            merged.append(current)
        
        return merged
    
    def _boxes_overlap(self, box1: Dict, box2: Dict) -> bool:
        """Check if two bounding boxes overlap significantly."""
        # Check vertical overlap
        y_overlap = min(box1.get("y2", 0), box2.get("y2", 0)) - max(box1.get("y1", 0), box2.get("y1", 0))
        if y_overlap <= 0:
            return False
        
        # Check horizontal overlap
        x_overlap = min(box1.get("x2", 0), box2.get("x2", 0)) - max(box1.get("x1", 0), box2.get("x1", 0))
        if x_overlap <= 0:
            return False
        
        # Calculate overlap ratio
        box1_area = (box1.get("x2", 0) - box1.get("x1", 0)) * (box1.get("y2", 0) - box1.get("y1", 0))
        overlap_area = x_overlap * y_overlap
        
        if box1_area <= 0:
            return False
        
        return (overlap_area / box1_area) >= self.merge_threshold
    
    def _merge_boxes(self, box1: Dict, box2: Dict) -> Dict[str, float]:
        """Merge two bounding boxes into one encompassing box."""
        return {
            "x1": min(box1.get("x1", 0), box2.get("x1", 0)),
            "y1": min(box1.get("y1", 0), box2.get("y1", 0)),
            "x2": max(box1.get("x2", 0), box2.get("x2", 0)),
            "y2": max(box1.get("y2", 0), box2.get("y2", 0)),
        }
    
    def get_highlight_hash(self, highlight_set: HighlightSet) -> str:
        """
        Generate a hash of a highlight set for blockchain anchoring.
        
        Args:
            highlight_set: The highlight set
            
        Returns:
            SHA256 hash of the highlights
        """
        content = str(highlight_set.to_dict())
        return hashlib.sha256(content.encode()).hexdigest()


# Singleton instance
highlight_service = HighlightService()

"""
Internal routes for service-to-service communication.

These endpoints are not exposed through the public gateway and are
used for inter-service communication (e.g., PDF service checking
document ownership).
"""

from fastapi import APIRouter, HTTPException, status, Header
from typing import Optional

from app.core.supabase import supabase
from app.utils.helpers import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/internal", tags=["Internal"])


@router.get("/documents/{document_id}/owner")
async def get_document_owner(
    document_id: str,
    x_service_key: Optional[str] = Header(None, alias="X-Service-Key"),
):
    """
    Get the owner of a document.
    
    This is an internal endpoint used by the PDF service to validate
    document ownership for voice calls.
    
    Args:
        document_id: The document UUID
        x_service_key: Optional service authentication key
    
    Returns:
        {"owner_id": "<user_id>"} if found
        404 if document not found
    """
    try:
        # Query the document_ownership table using admin client (bypasses RLS)
        # Exclude soft-deleted documents
        result = supabase.admin_table("document_ownership").select(
            "user_id"
        ).eq("document_id", document_id).eq("is_deleted", False).execute()
        
        # Check if result has data
        if not result.data or len(result.data) == 0:
            # Document not found in ownership table
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found in ownership records"
            )
        
        # Get the first result (should only be one)
        owner_data = result.data[0]
        return {"owner_id": owner_data.get("user_id")}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking document ownership: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check document ownership"
        )


@router.post("/documents/{document_id}/ownership")
async def register_document_ownership(
    document_id: str,
    user_id: str,
    filename: Optional[str] = None,
    x_service_key: Optional[str] = Header(None, alias="X-Service-Key"),
):
    """
    Register document ownership.
    
    Called by the PDF service when a document is uploaded.
    
    Args:
        document_id: The document UUID
        user_id: The user who owns the document (query param)
        filename: Optional original filename (query param)
        x_service_key: Optional service authentication key
    
    Returns:
        {"success": True} if registered
    """
    try:
        # Upsert the ownership record using admin client
        record = {"document_id": document_id, "user_id": user_id, "is_deleted": False}
        if filename:
            record["filename"] = filename
        result = supabase.admin_table("document_ownership").upsert(record).execute()
        
        logger.info(f"Registered ownership: document={document_id}, user={user_id}")
        
        return {"success": True, "document_id": document_id, "user_id": user_id}
        
    except Exception as e:
        logger.error(f"Error registering document ownership: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register document ownership"
        )


@router.delete("/documents/{document_id}/ownership")
async def remove_document_ownership(
    document_id: str,
    x_service_key: Optional[str] = Header(None, alias="X-Service-Key"),
):
    """
    Soft-delete document ownership record.
    
    Sets is_deleted=true so the document is hidden from UI everywhere.
    
    Args:
        document_id: The document UUID
        x_service_key: Optional service authentication key
    
    Returns:
        {"success": True} if updated
    """
    try:
        result = supabase.admin_table("document_ownership").update(
            {"is_deleted": True}
        ).eq("document_id", document_id).execute()
        
        logger.info(f"Soft-deleted ownership record for document: {document_id}")
        
        return {"success": True, "document_id": document_id}
        
    except Exception as e:
        logger.error(f"Error removing document ownership: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove document ownership"
        )


@router.get("/users/{user_id}/documents")
async def get_user_documents(
    user_id: str,
    x_service_key: Optional[str] = Header(None, alias="X-Service-Key"),
):
    """
    Get all documents owned by a user.
    
    Args:
        user_id: The user UUID
        x_service_key: Optional service authentication key
    
    Returns:
        {"documents": [{"document_id": "...", "created_at": "..."}]}
    """
    try:
        result = supabase.admin_table("document_ownership").select(
            "document_id, created_at"
        ).eq("user_id", user_id).eq("is_deleted", False).order("created_at", desc=True).execute()
        
        return {"documents": result.data or []}
        
    except Exception as e:
        logger.error(f"Error fetching user documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user documents"
        )

"""Document upload and management routes."""

from datetime import datetime
from typing import List

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.supabase import supabase
from app.core.security import integrity_service
from app.models.schemas import (
    DeleteResponse,
    DocumentHashResponse,
    DocumentListResponse,
    DocumentMetadata,
    IntegrityVerifyRequest,
    IntegrityVerifyResponse,
    UploadResponse,
)
from app.services.embedding_service import embedding_service
from app.services.pdf_service import pdf_service
from app.services.vector_service import vector_store
from app.services.blockchain_service import blockchain_service
from app.utils.helpers import get_logger, get_utc_timestamp

logger = get_logger(__name__)

router = APIRouter(tags=["Documents"])


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF document",
    description="Upload a PDF file for processing. The document will be extracted, chunked, embedded, and indexed.",
)
async def upload_pdf(request: Request, file: UploadFile = File(...)):
    """
    Upload and process a PDF document.

    - Extracts text with page information
    - Creates text chunks with configurable size and overlap
    - Generates embeddings for semantic search
    - Stores vectors in FAISS index
    - Registers SHA-256 hash for integrity verification

    Returns document ID, chunk count, and SHA-256 hash.
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )

    # Validate content type
    if file.content_type and file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content type: {file.content_type}. Expected application/pdf",
        )

    try:
        # Read file content
        file_bytes = await file.read()

        if len(file_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file uploaded",
            )

        logger.info(
            "Processing upload",
            filename=file.filename,
            size_bytes=len(file_bytes),
        )

        # Process PDF
        document_id, extraction_result, chunks = await pdf_service.process_pdf(
            file_bytes=file_bytes,
            filename=file.filename,
        )

        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract text from PDF. The document may be empty or contain only images.",
            )

        # Generate embeddings
        chunk_texts = [chunk.text_content for chunk in chunks]
        embeddings = await embedding_service.generate_embeddings_batch(chunk_texts)

        # Create document metadata
        metadata = DocumentMetadata(
            document_id=document_id,
            filename=file.filename,
            upload_timestamp=get_utc_timestamp(),
            sha256_hash=extraction_result.sha256_hash,
            page_count=extraction_result.page_count,
            chunk_count=len(chunks),
            file_size_bytes=len(file_bytes),
        )

        # Store in vector database
        await vector_store.add_document(
            document_id=document_id,
            chunks=chunks,
            embeddings=embeddings,
            metadata=metadata,
        )

        # Register hash for integrity verification
        await integrity_service.register_document(
            document_id=document_id,
            sha256_hash=extraction_result.sha256_hash,
            filename=file.filename,
            file_size_bytes=len(file_bytes),
        )

        # Create blockchain integrity proof for this document
        try:
            user_id_for_proof = (
                request.headers.get("x-user-id")
                or request.headers.get("X-User-ID")
                or "anonymous"
            )
            await blockchain_service.store_document_proof(
                document_id=document_id,
                document_bytes=file_bytes,
                user_id=str(user_id_for_proof).strip(),
                filename=file.filename,
            )
            logger.info("Blockchain proof created", document_id=document_id)
        except Exception as e:
            logger.warning("Blockchain proof creation failed (non-fatal)", error=str(e))

        # Register document ownership in Supabase (same DB dashboard reads from)
        user_id = (
            request.headers.get("x-user-id")
            or request.headers.get("X-User-ID")
            or ""
        )
        user_id = str(user_id).strip()
        if not user_id:
            logger.warning(
                "No X-User-ID header on upload - ensure requests go through gateway with auth"
            )
        elif not supabase.is_available():
            logger.warning(
                "Supabase not configured - set SUPABASE_URL and SUPABASE_SERVICE_KEY in ai-pdf-server"
            )
        else:
            try:
                supabase.client.table("document_ownership").upsert(
                    {
                        "document_id": document_id,
                        "user_id": user_id,
                        "filename": file.filename,
                    }
                ).execute()
                logger.info(
                    "Registered document ownership",
                    document_id=document_id,
                    user_id=user_id,
                )
            except Exception as e:
                logger.warning(
                    "Could not register document ownership",
                    document_id=document_id,
                    error=str(e),
                )

        logger.info(
            "Document uploaded successfully",
            document_id=document_id,
            pages=extraction_result.page_count,
            chunks=len(chunks),
        )

        return UploadResponse(
            document_id=document_id,
            filename=file.filename,
            page_count=extraction_result.page_count,
            chunk_count=len(chunks),
            sha256_hash=extraction_result.sha256_hash,
            message="Document uploaded and processed successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Upload failed", error=str(e), filename=file.filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}",
        )


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="List user documents",
    description="Get documents owned by the current user (excludes soft-deleted).",
)
async def list_documents(request: Request):
    """List documents for the authenticated user from document_ownership."""
    try:
        user_id = request.headers.get("x-user-id") or request.headers.get("X-User-ID")
        if not user_id:
            return DocumentListResponse(documents=[], total_count=0)

        if not supabase.is_available():
            documents = await vector_store.list_documents()
            return DocumentListResponse(documents=documents, total_count=len(documents))

        result = supabase.client.table("document_ownership").select(
            "document_id, filename, created_at"
        ).eq("user_id", user_id.strip()).eq("is_deleted", False).order(
            "created_at", desc=True
        ).execute()

        rows = result.data or []
        documents = []
        for row in rows:
            doc_id = row.get("document_id")
            filename = row.get("filename") or "Document"
            created_at = row.get("created_at") or ""
            metadata = None
            try:
                metadata = await vector_store.get_document_metadata(doc_id)
            except Exception:
                pass
            try:
                ts = datetime.fromisoformat(created_at.replace("Z", "+00:00")) if created_at else datetime.utcnow()
            except Exception:
                ts = datetime.utcnow()
            doc = DocumentMetadata(
                document_id=doc_id,
                filename=filename,
                upload_timestamp=ts,
                sha256_hash="",
                page_count=getattr(metadata, "page_count", 0) if metadata else 0,
                chunk_count=getattr(metadata, "chunk_count", 0) if metadata else 0,
                file_size_bytes=getattr(metadata, "file_size_bytes", 0) if metadata else 0,
            )
            documents.append(doc)

        return DocumentListResponse(documents=documents, total_count=len(documents))
    except Exception as e:
        logger.error("Failed to list documents", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}",
        )


@router.get(
    "/documents/{document_id}",
    response_model=DocumentMetadata,
    summary="Get document metadata",
    description="Get metadata for a specific document by ID.",
)
async def get_document(document_id: str):
    """Get document metadata by ID."""
    metadata = await vector_store.get_document_metadata(document_id)

    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )

    return metadata


@router.get(
    "/documents/{document_id}/file",
    summary="Download PDF file",
    description="Download the original PDF file.",
    response_class=FileResponse,
)
async def get_document_file(document_id: str):
    """
    Download the original PDF file.
    
    Returns the PDF file for viewing/download.
    """
    # Get metadata to verify document exists and get filename
    metadata = await vector_store.get_document_metadata(document_id)
    
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )
    
    # Build path to PDF file
    pdf_path = settings.UPLOAD_DIR / f"{document_id}.pdf"
    
    if not pdf_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF file not found for document: {document_id}",
        )
    
    return FileResponse(
        path=str(pdf_path),
        filename=metadata.filename,
        media_type="application/pdf",
    )


@router.get(
    "/documents/{document_id}/hash",
    response_model=DocumentHashResponse,
    summary="Get document hash",
    description="Get the SHA-256 hash of a document for integrity verification.",
)
async def get_document_hash(document_id: str):
    """
    Get document SHA-256 hash.

    This hash can be used for:
    - Integrity verification
    - Blockchain storage (future)
    - Document authenticity proof
    """
    record = await integrity_service.get_hash_record(document_id)

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )

    return DocumentHashResponse(
        document_id=document_id,
        sha256_hash=record.sha256_hash,
        filename=record.filename,
        blockchain_ready=True,
    )


@router.post(
    "/documents/verify",
    response_model=IntegrityVerifyResponse,
    summary="Verify document integrity",
    description="Verify a document's integrity by comparing provided hash with stored hash.",
)
async def verify_document_integrity(request: IntegrityVerifyRequest):
    """
    Verify document integrity.

    Compares the provided SHA-256 hash against the hash
    stored when the document was uploaded.

    This enables:
    - Tamper detection
    - Authenticity verification
    - Blockchain-ready integrity proofs
    """
    is_valid, stored_hash, message = await integrity_service.verify_integrity(
        document_id=request.document_id,
        provided_hash=request.provided_hash,
    )

    if not stored_hash:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {request.document_id}",
        )

    return IntegrityVerifyResponse(
        document_id=request.document_id,
        is_valid=is_valid,
        stored_hash=stored_hash,
        provided_hash=request.provided_hash,
        message=message,
    )


@router.delete(
    "/documents/{document_id}",
    response_model=DeleteResponse,
    summary="Delete a document",
    description="Delete a document and all associated data (vectors, metadata, PDF file).",
)
async def delete_document(document_id: str):
    """
    Delete a document (soft delete in ownership, physical delete of data).

    - Sets is_deleted=true in document_ownership (hides from UI)
    - Removes vector embeddings, PDF file, integrity record
    """
    # Check if document exists
    exists = await vector_store.document_exists(document_id)
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )

    # Soft-delete in User-Service (document_ownership.is_deleted = true)
    try:
        import httpx
        user_svc = settings.USER_SERVICE_URL.rstrip("/")
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{user_svc}/internal/documents/{document_id}/ownership",
                timeout=5.0,
            )
            if resp.status_code not in (200, 404):
                logger.warning(f"User-Service soft-delete returned {resp.status_code}")
    except Exception as e:
        logger.warning(f"Could not soft-delete ownership (non-fatal): {e}")

    # Physical delete from vector store, PDF, integrity
    await vector_store.delete_document(document_id)
    await pdf_service.delete_pdf(document_id)
    await integrity_service.delete_record(document_id)

    logger.info("Document deleted", document_id=document_id)

    return DeleteResponse(
        document_id=document_id,
        message="Document deleted successfully",
    )


@router.get(
    "/blockchain/status",
    summary="Get blockchain status",
    description="Get the status of blockchain integration.",
)
async def get_blockchain_status():
    """
    Get blockchain integration status.

    Returns information about blockchain readiness
    and any active blockchain integrations.
    """
    return integrity_service.get_blockchain_status()

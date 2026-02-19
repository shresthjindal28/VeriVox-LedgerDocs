"""
Dashboard Service for aggregating statistics and data for the dashboard.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from app.core.supabase import supabase
from app.services.vector_service import vector_store
from app.utils.helpers import get_logger

logger = get_logger(__name__)


class DashboardService:
    """Service for dashboard data aggregation."""
    
    async def get_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get aggregated statistics for a user.
        
        Returns: total_documents, active_sessions, total_extractions, total_proofs
        """
        stats = {
            "total_documents": 0,
            "active_sessions": 0,
            "total_extractions": 0,
            "total_proofs": 0,
        }
        
        if not supabase.is_available():
            logger.warning("Supabase not available, returning zero stats")
            return stats
        
        try:
            doc_result = supabase.client.table("document_ownership").select(
                "document_id", count="exact"
            ).eq("user_id", user_id).execute()
            stats["total_documents"] = doc_result.count if hasattr(doc_result, 'count') else len(doc_result.data) if doc_result.data else 0
            
            session_result = supabase.client.table("voice_sessions").select(
                "session_id", count="exact"
            ).eq("user_id", user_id).neq("state", "ended").execute()
            stats["active_sessions"] = session_result.count if hasattr(session_result, 'count') else len(session_result.data) if session_result.data else 0
            
            extraction_result = supabase.client.table("blockchain_proofs").select(
                "proof_id", count="exact"
            ).eq("user_id", user_id).eq("proof_type", "extraction").execute()
            stats["total_extractions"] = extraction_result.count if hasattr(extraction_result, 'count') else len(extraction_result.data) if extraction_result.data else 0
            
            proofs_result = supabase.client.table("blockchain_proofs").select(
                "proof_id", count="exact"
            ).eq("user_id", user_id).execute()
            stats["total_proofs"] = proofs_result.count if hasattr(proofs_result, 'count') else len(proofs_result.data) if proofs_result.data else 0
            
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
        
        return stats
    
    async def get_user_documents(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get paginated documents for a user with blockchain status.
        
        Returns: documents (id, name, upload_date, pages, blockchain_status, blockchain_hash), pagination
        """
        if not supabase.is_available():
            return {"documents": [], "pagination": {"page": page, "limit": limit, "total": 0}}
        
        offset = (page - 1) * limit
        try:
            ownership_result = supabase.client.table("document_ownership").select(
                "document_id", "filename", "created_at"
            ).eq("user_id", user_id).order("created_at", desc=True).range(offset, offset + limit - 1).execute()
            
            rows = ownership_result.data or []
            count_result = supabase.client.table("document_ownership").select(
                "document_id", count="exact"
            ).eq("user_id", user_id).execute()
            total = count_result.count if hasattr(count_result, 'count') else len(count_result.data) if count_result.data else 0
            
            documents = []
            for row in rows:
                doc_id = row.get("document_id")
                filename = row.get("filename") or "Document"
                created_at = row.get("created_at") or ""
                pages = 0
                blockchain_status = "pending"
                blockchain_hash = None
                
                try:
                    meta = await vector_store.get_document_metadata(doc_id)
                    if meta:
                        pages = getattr(meta, "page_count", 0) or 0
                except Exception:
                    pass
                
                try:
                    proof_result = supabase.client.table("blockchain_proofs").select(
                        "hash_value", "verified"
                    ).eq("document_id", doc_id).eq("user_id", user_id).eq("proof_type", "document").limit(1).execute()
                    if proof_result.data and len(proof_result.data) > 0:
                        p = proof_result.data[0]
                        blockchain_hash = p.get("hash_value")
                        blockchain_status = "verified" if p.get("verified") else "failed"
                except Exception:
                    pass
                
                documents.append({
                    "id": doc_id,
                    "name": filename,
                    "upload_date": created_at,
                    "pages": pages,
                    "blockchain_status": blockchain_status,
                    "blockchain_hash": blockchain_hash,
                })
            
            return {
                "documents": documents,
                "pagination": {"page": page, "limit": limit, "total": total},
            }
        except Exception as e:
            logger.error(f"Error getting user documents: {e}")
            return {"documents": [], "pagination": {"page": page, "limit": limit, "total": 0}}
    
    async def get_recent_sessions(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get recent voice sessions for a user with document_name.
        
        Returns: sessions (session_id, document_name, duration_seconds, verification_status, created_at), limit 20 default.
        """
        if not supabase.is_available():
            return {"sessions": [], "total": 0}
        
        try:
            count_result = supabase.client.table("voice_sessions").select(
                "session_id", count="exact"
            ).eq("user_id", user_id).execute()
            total = count_result.count if hasattr(count_result, 'count') else len(count_result.data) if count_result.data else 0
            
            sessions_result = supabase.client.table("voice_sessions").select(
                "*"
            ).eq("user_id", user_id).order(
                "created_at", desc=True
            ).limit(limit).offset(offset).execute()
            
            sessions = sessions_result.data or []
            doc_ids = list({s.get("document_id") for s in sessions if s.get("document_id")})
            name_by_id = {}
            if doc_ids:
                try:
                    for doc_id in doc_ids:
                        r = supabase.client.table("document_ownership").select("filename").eq("document_id", doc_id).eq("user_id", user_id).limit(1).execute()
                        if r.data and len(r.data) > 0:
                            name_by_id[doc_id] = r.data[0].get("filename") or "Document"
                except Exception:
                    pass
            
            formatted_sessions = []
            for session in sessions:
                doc_id = session.get("document_id")
                formatted_sessions.append({
                    "session_id": session.get("session_id"),
                    "document_id": doc_id,
                    "document_name": name_by_id.get(doc_id, "Document"),
                    "state": session.get("state"),
                    "created_at": session.get("created_at"),
                    "ended_at": session.get("ended_at"),
                    "duration_seconds": session.get("duration_seconds", 0),
                    "question_count": session.get("question_count", 0),
                    "transcript_status": session.get("transcript_status", "pending"),
                    "verification_status": session.get("verification_status", "pending"),
                })
            
            return {
                "sessions": formatted_sessions,
                "total": total,
                "limit": limit,
                "offset": offset,
            }
        except Exception as e:
            logger.error(f"Error getting recent sessions: {e}")
            return {"sessions": [], "total": 0}
    
    async def get_blockchain_proofs(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        proof_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get blockchain proofs for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of proofs to return
            offset: Offset for pagination
            proof_type: Optional filter by proof type
            
        Returns:
            Dictionary with:
            - proofs: List of proof data
            - total: Total count
        """
        if not supabase.is_available():
            return {"proofs": [], "total": 0}
        
        try:
            # Build query
            query = supabase.client.table("blockchain_proofs").select(
                "*"
            ).eq("user_id", user_id)
            
            if proof_type:
                query = query.eq("proof_type", proof_type)
            
            # Get total count
            count_query = query.select("proof_id", count="exact")
            count_result = count_query.execute()
            total = count_result.count if hasattr(count_result, 'count') else len(count_result.data) if count_result.data else 0
            
            # Get proofs ordered by timestamp desc
            proofs_result = query.order(
                "timestamp", desc=True
            ).limit(limit).offset(offset).execute()
            
            proofs = proofs_result.data if proofs_result.data else []
            
            # Format proofs for frontend
            formatted_proofs = []
            for proof in proofs:
                formatted_proofs.append({
                    "proof_id": proof.get("proof_id"),
                    "proof_type": proof.get("proof_type"),
                    "hash_value": proof.get("hash_value"),
                    "document_id": proof.get("document_id"),
                    "session_id": proof.get("session_id"),
                    "tx_hash": proof.get("tx_hash"),
                    "block_number": proof.get("block_number"),
                    "verified": proof.get("verified", False),
                    "timestamp": proof.get("timestamp"),
                    "metadata": proof.get("metadata", {}),
                })
            
            return {
                "proofs": formatted_proofs,
                "total": total,
                "limit": limit,
                "offset": offset,
            }
        except Exception as e:
            logger.error(f"Error getting blockchain proofs: {e}")
            return {"proofs": [], "total": 0}


# Singleton instance
dashboard_service = DashboardService()

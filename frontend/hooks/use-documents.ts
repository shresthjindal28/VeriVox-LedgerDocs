'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { documentsApi } from '@/lib/api';
import { useDocumentStore } from '@/stores';
import type { DocumentInfo } from '@/types';

// Query keys
export const documentKeys = {
  all: ['documents'] as const,
  lists: () => [...documentKeys.all, 'list'] as const,
  list: (filters?: Record<string, unknown>) => [...documentKeys.lists(), filters] as const,
  details: () => [...documentKeys.all, 'detail'] as const,
  detail: (id: string) => [...documentKeys.details(), id] as const,
  verification: (id: string) => [...documentKeys.all, 'verification', id] as const,
};

// ============================================================================
// Document Hooks
// ============================================================================

export function useDocuments() {
  const { setDocuments, setLoading, setError } = useDocumentStore();
  
  return useQuery({
    queryKey: documentKeys.lists(),
    queryFn: async () => {
      const data = await documentsApi.listDocuments();
      setDocuments(data);
      return data;
    },
    staleTime: 30 * 1000, // 30 seconds
  });
}

export function useDocument(documentId: string) {
  const { setCurrentDocument } = useDocumentStore();
  
  return useQuery({
    queryKey: documentKeys.detail(documentId),
    queryFn: async () => {
      const data = await documentsApi.getDocument(documentId);
      setCurrentDocument(data);
      return data;
    },
    enabled: !!documentId,
    staleTime: 60 * 1000, // 1 minute
  });
}

export function useDocumentVerification(documentId: string) {
  return useQuery({
    queryKey: documentKeys.verification(documentId),
    queryFn: () => documentsApi.verifyDocument(documentId),
    enabled: !!documentId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();
  const { 
    setUploading, 
    setUploadProgress, 
    setUploadError, 
    addDocument 
  } = useDocumentStore();
  
  return useMutation({
    mutationFn: (file: File) => documentsApi.upload(file),
    onMutate: () => {
      setUploading(true);
      setUploadProgress(0);
    },
    onSuccess: (data) => {
      const newDoc: DocumentInfo = {
        document_id: data.document_id,
        filename: data.filename,
        page_count: data.page_count,
        upload_date: new Date().toISOString(),
        file_size: 0, // Will be updated when list refreshes
      };
      addDocument(newDoc);
      queryClient.invalidateQueries({ queryKey: documentKeys.lists() });
      setUploadProgress(100);
    },
    onError: (error: Error) => {
      setUploadError(error.message);
    },
    onSettled: () => {
      setUploading(false);
    },
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();
  const { removeDocument } = useDocumentStore();
  
  return useMutation({
    mutationFn: (documentId: string) => documentsApi.deleteDocument(documentId),
    onSuccess: (_, documentId) => {
      removeDocument(documentId);
      queryClient.invalidateQueries({ queryKey: documentKeys.lists() });
      queryClient.removeQueries({ queryKey: documentKeys.detail(documentId) });
    },
  });
}

// ============================================================================
// Prefetch helpers
// ============================================================================

export function usePrefetchDocument() {
  const queryClient = useQueryClient();
  
  return (documentId: string) => {
    queryClient.prefetchQuery({
      queryKey: documentKeys.detail(documentId),
      queryFn: () => documentsApi.getDocument(documentId),
      staleTime: 60 * 1000,
    });
  };
}

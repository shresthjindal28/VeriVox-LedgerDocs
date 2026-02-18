import { create } from 'zustand';
import type { DocumentInfo } from '@/types';

interface DocumentState {
  // Documents list
  documents: DocumentInfo[];
  currentDocument: DocumentInfo | null;
  
  // Upload state
  uploadProgress: number;
  isUploading: boolean;
  uploadError: string | null;
  
  // Loading state
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setDocuments: (documents: DocumentInfo[]) => void;
  addDocument: (document: DocumentInfo) => void;
  removeDocument: (documentId: string) => void;
  updateDocument: (documentId: string, updates: Partial<DocumentInfo>) => void;
  setCurrentDocument: (document: DocumentInfo | null) => void;
  setUploadProgress: (progress: number) => void;
  setUploading: (uploading: boolean) => void;
  setUploadError: (error: string | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

const initialState = {
  documents: [],
  currentDocument: null,
  uploadProgress: 0,
  isUploading: false,
  uploadError: null,
  isLoading: false,
  error: null,
};

export const useDocumentStore = create<DocumentState>()((set, get) => ({
  ...initialState,
  
  setDocuments: (documents) => set({ documents }),
  
  addDocument: (document) => set((state) => ({
    documents: [...state.documents, document],
  })),
  
  removeDocument: (documentId) => set((state) => ({
    documents: state.documents.filter((doc) => doc.document_id !== documentId),
    currentDocument: state.currentDocument?.document_id === documentId 
      ? null 
      : state.currentDocument,
  })),
  
  updateDocument: (documentId, updates) => set((state) => ({
    documents: state.documents.map((doc) =>
      doc.document_id === documentId ? { ...doc, ...updates } : doc
    ),
    currentDocument: state.currentDocument?.document_id === documentId
      ? { ...state.currentDocument, ...updates }
      : state.currentDocument,
  })),
  
  setCurrentDocument: (currentDocument) => set({ currentDocument }),
  
  setUploadProgress: (uploadProgress) => set({ uploadProgress }),
  
  setUploading: (isUploading) => set({ 
    isUploading, 
    uploadProgress: isUploading ? 0 : get().uploadProgress,
    uploadError: isUploading ? null : get().uploadError,
  }),
  
  setUploadError: (uploadError) => set({ uploadError, isUploading: false }),
  
  setLoading: (isLoading) => set({ isLoading }),
  
  setError: (error) => set({ error }),
  
  reset: () => set(initialState),
}));

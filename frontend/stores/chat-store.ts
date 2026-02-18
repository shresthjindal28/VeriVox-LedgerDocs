import { create } from 'zustand';
import type { ChatMessage, SourceReference } from '@/types';

interface ChatState {
  // Messages per document
  messagesByDocument: Record<string, ChatMessage[]>;
  
  // Current state
  currentDocumentId: string | null;
  isStreaming: boolean;
  streamingMessage: string;
  pendingQuestion: string | null;
  
  // Sources
  currentSources: SourceReference[];
  
  // WebSocket state
  isConnected: boolean;
  connectionError: string | null;
  
  // Loading state
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setCurrentDocument: (documentId: string | null) => void;
  addMessage: (documentId: string, message: ChatMessage) => void;
  updateLastMessage: (documentId: string, content: string) => void;
  appendToStreamingMessage: (chunk: string) => void;
  finalizeStreamingMessage: (documentId: string, sources?: SourceReference[]) => void;
  setStreaming: (streaming: boolean) => void;
  setPendingQuestion: (question: string | null) => void;
  setSources: (sources: SourceReference[]) => void;
  setConnected: (connected: boolean) => void;
  setConnectionError: (error: string | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearMessages: (documentId: string) => void;
  reset: () => void;
}

const initialState = {
  messagesByDocument: {},
  currentDocumentId: null,
  isStreaming: false,
  streamingMessage: '',
  pendingQuestion: null,
  currentSources: [],
  isConnected: false,
  connectionError: null,
  isLoading: false,
  error: null,
};

export const useChatStore = create<ChatState>()((set, get) => ({
  ...initialState,
  
  setCurrentDocument: (currentDocumentId) => set({ currentDocumentId }),
  
  addMessage: (documentId, message) => set((state) => ({
    messagesByDocument: {
      ...state.messagesByDocument,
      [documentId]: [...(state.messagesByDocument[documentId] || []), message],
    },
  })),
  
  updateLastMessage: (documentId, content) => set((state) => {
    const messages = state.messagesByDocument[documentId] || [];
    if (messages.length === 0) return state;
    
    const updatedMessages = [...messages];
    const lastIndex = updatedMessages.length - 1;
    updatedMessages[lastIndex] = {
      ...updatedMessages[lastIndex],
      content,
    };
    
    return {
      messagesByDocument: {
        ...state.messagesByDocument,
        [documentId]: updatedMessages,
      },
    };
  }),
  
  appendToStreamingMessage: (chunk) => set((state) => ({
    streamingMessage: state.streamingMessage + chunk,
  })),
  
  finalizeStreamingMessage: (documentId, sources) => {
    const { streamingMessage, pendingQuestion } = get();
    
    if (streamingMessage) {
      const assistantMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: streamingMessage,
        timestamp: new Date().toISOString(),
        sources,
      };
      
      set((state) => ({
        messagesByDocument: {
          ...state.messagesByDocument,
          [documentId]: [...(state.messagesByDocument[documentId] || []), assistantMessage],
        },
        streamingMessage: '',
        isStreaming: false,
        pendingQuestion: null,
        currentSources: sources || [],
      }));
    }
  },
  
  setStreaming: (isStreaming) => set({ 
    isStreaming,
    streamingMessage: isStreaming ? '' : get().streamingMessage,
  }),
  
  setPendingQuestion: (pendingQuestion) => set({ pendingQuestion }),
  
  setSources: (currentSources) => set({ currentSources }),
  
  setConnected: (isConnected) => set({ 
    isConnected,
    connectionError: isConnected ? null : get().connectionError,
  }),
  
  setConnectionError: (connectionError) => set({ 
    connectionError,
    isConnected: false,
  }),
  
  setLoading: (isLoading) => set({ isLoading }),
  
  setError: (error) => set({ error }),
  
  clearMessages: (documentId) => set((state) => ({
    messagesByDocument: {
      ...state.messagesByDocument,
      [documentId]: [],
    },
  })),
  
  reset: () => set(initialState),
}));

// Helper to get messages for current document
export const useCurrentMessages = () => {
  const { messagesByDocument, currentDocumentId } = useChatStore();
  return currentDocumentId ? messagesByDocument[currentDocumentId] || [] : [];
};

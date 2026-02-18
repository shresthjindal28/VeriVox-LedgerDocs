'use client';

import { useMutation } from '@tanstack/react-query';
import { chatApi } from '@/lib/api';
import { useChatStore } from '@/stores';
import type { ChatMessage } from '@/types';

// ============================================================================
// Chat Hooks
// ============================================================================

export function useAskQuestion(documentId: string) {
  const { addMessage, setLoading, setError, setSources } = useChatStore();
  
  return useMutation({
    mutationFn: (question: string) => chatApi.askQuestion(documentId, question),
    onMutate: (question) => {
      // Add user message immediately
      const userMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'user',
        content: question,
        timestamp: new Date().toISOString(),
      };
      addMessage(documentId, userMessage);
      setLoading(true);
    },
    onSuccess: (data) => {
      // Add assistant response
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.answer,
        timestamp: new Date().toISOString(),
        sources: data.sources,
      };
      addMessage(documentId, assistantMessage);
      setSources(data.sources || []);
    },
    onError: (error: Error) => {
      setError(error.message);
      // Add error message
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${error.message}`,
        timestamp: new Date().toISOString(),
      };
      addMessage(documentId, errorMessage);
    },
    onSettled: () => {
      setLoading(false);
    },
  });
}

// ============================================================================
// WebSocket Chat Hook
// ============================================================================

export function useChatWebSocket(documentId: string) {
  const {
    setConnected,
    setConnectionError,
    setStreaming,
    appendToStreamingMessage,
    finalizeStreamingMessage,
    addMessage,
    setPendingQuestion,
    setSources,
  } = useChatStore();
  
  let ws: WebSocket | null = null;
  
  const connect = () => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8080';
    ws = new WebSocket(`${wsUrl}/ws/chat/${documentId}`);
    
    ws.onopen = () => {
      setConnected(true);
      setConnectionError(null);
    };
    
    ws.onclose = () => {
      setConnected(false);
    };
    
    ws.onerror = (error) => {
      setConnectionError('WebSocket connection error');
      setConnected(false);
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'token':
            appendToStreamingMessage(data.content);
            break;
            
          case 'complete':
            finalizeStreamingMessage(documentId, data.sources);
            break;
            
          case 'error':
            setStreaming(false);
            setConnectionError(data.message);
            break;
            
          case 'sources':
            setSources(data.sources || []);
            break;
        }
      } catch (e) {
        // Handle non-JSON messages (raw text chunks)
        appendToStreamingMessage(event.data);
      }
    };
    
    return ws;
  };
  
  const sendMessage = (question: string) => {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      setConnectionError('WebSocket not connected');
      return;
    }
    
    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: question,
      timestamp: new Date().toISOString(),
    };
    addMessage(documentId, userMessage);
    
    // Start streaming
    setStreaming(true);
    setPendingQuestion(question);
    
    // Send to server
    ws.send(JSON.stringify({ question }));
  };
  
  const disconnect = () => {
    if (ws) {
      ws.close();
      ws = null;
    }
    setConnected(false);
  };
  
  return {
    connect,
    sendMessage,
    disconnect,
    isConnected: () => ws?.readyState === WebSocket.OPEN,
  };
}

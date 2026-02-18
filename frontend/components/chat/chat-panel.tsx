'use client';

import * as React from 'react';
import { ChatMessage } from './chat-message';
import { ChatInput } from './chat-input';
import { ChatMessageSkeleton } from '@/components/ui/loading';
import { cn } from '@/lib/utils';
import type { ChatMessage as ChatMessageType, SourceReference } from '@/types';
import { useChatStore } from '@/stores';

interface ChatPanelProps {
  documentId: string;
  messages: ChatMessageType[];
  streamingContent?: string;
  onSend: (message: string) => void;
  onVoiceStart?: () => void;
  onVoiceEnd?: () => void;
  onSourceClick?: (source: SourceReference) => void;
  isLoading?: boolean;
  isRecording?: boolean;
  className?: string;
}

export function ChatPanel({
  documentId,
  messages,
  streamingContent,
  onSend,
  onVoiceStart,
  onVoiceEnd,
  onSourceClick,
  isLoading = false,
  isRecording = false,
  className,
}: ChatPanelProps) {
  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const containerRef = React.useRef<HTMLDivElement>(null);
  
  // Auto-scroll to bottom when new messages arrive
  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);
  
  return (
    <div className={cn('flex h-full flex-col', className)}>
      {/* Messages */}
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto"
      >
        {messages.length === 0 && !isLoading && (
          <div className="flex h-full flex-col items-center justify-center p-8 text-center">
            <div className="mb-4 rounded-full bg-muted p-4">
              <svg
                className="h-8 w-8 text-muted-foreground"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                />
              </svg>
            </div>
            <h3 className="mb-2 text-lg font-medium">Start a conversation</h3>
            <p className="text-sm text-muted-foreground">
              Ask questions about the document and get AI-powered answers with source references.
            </p>
          </div>
        )}
        
        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            message={message}
            onSourceClick={onSourceClick}
          />
        ))}
        
        {/* Streaming message */}
        {streamingContent && (
          <ChatMessage
            message={{
              id: 'streaming',
              role: 'assistant',
              content: streamingContent,
              timestamp: new Date().toISOString(),
            }}
            isStreaming
          />
        )}
        
        {/* Loading indicator */}
        {isLoading && !streamingContent && (
          <div className="px-4 py-4">
            <ChatMessageSkeleton />
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input */}
      <ChatInput
        onSend={onSend}
        onVoiceStart={onVoiceStart}
        onVoiceEnd={onVoiceEnd}
        isLoading={isLoading}
        isRecording={isRecording}
        showVoice={!!onVoiceStart}
      />
    </div>
  );
}

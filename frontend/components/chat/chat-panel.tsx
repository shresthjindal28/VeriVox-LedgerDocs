'use client';

import * as React from 'react';
import { ChatMessage } from './chat-message';
import { ChatInput } from './chat-input';
import { ChatMessageSkeleton } from '@/components/ui/loading';
import { cn } from '@/lib/utils';
import type { ChatMessage as ChatMessageType, SourceReference } from '@/types';
import { Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';

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
    <div className={cn('flex h-full flex-col bg-transparent', className)}>
      {/* Messages */}
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto px-4 py-4 custom-scrollbar scroll-smooth"
      >
        {messages.length === 0 && !isLoading && (
          <div className="flex h-full flex-col items-center justify-center p-8 text-center">
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.5 }}
              className="mb-8 relative"
            >
              <div className="absolute inset-0 bg-brand-500/20 blur-2xl rounded-full" />
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-linear-to-br from-brand-500 to-brand-600 shadow-xl shadow-brand-500/20 border border-brand-400/20">
                <Sparkles className="h-8 w-8 text-black" />
              </div>
            </motion.div>
            <h3 className="mb-3 text-2xl font-light tracking-tight text-white">VeriVox Intelligence</h3>
            <p className="text-sm text-brand-100/60 max-w-sm leading-relaxed font-light">
              Analyze documents, verify integrity, and get precise answers with blockchain-backed citations.
            </p>
          </div>
        )}

        <div className="space-y-6">
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
            <div className="px-4">
              <div className="flex items-center gap-2 text-brand-500/50 text-sm">
                <div className="flex gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-brand-500/50 animate-bounce [animation-delay:-0.3s]"></span>
                  <span className="w-1.5 h-1.5 rounded-full bg-brand-500/50 animate-bounce [animation-delay:-0.15s]"></span>
                  <span className="w-1.5 h-1.5 rounded-full bg-brand-500/50 animate-bounce"></span>
                </div>
                Thinking...
              </div>
            </div>
          )}
        </div>

        <div ref={messagesEndRef} className="h-4" />
      </div>

      {/* Input */}
      <div className="pt-0">
        <ChatInput
          onSend={onSend}
          onVoiceStart={onVoiceStart}
          onVoiceEnd={onVoiceEnd}
          isLoading={isLoading}
          isRecording={isRecording}
          showVoice={!!onVoiceStart}
        />
      </div>
    </div>
  );
}

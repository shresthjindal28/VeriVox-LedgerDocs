'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { User, Bot, Copy, Check } from 'lucide-react';
import type { ChatMessage as ChatMessageType, SourceReference } from '@/types';
import { formatDate } from '@/lib/utils';
import { motion } from 'framer-motion';

interface ChatMessageProps {
  message: ChatMessageType;
  onSourceClick?: (source: SourceReference) => void;
  isStreaming?: boolean;
}

export function ChatMessage({ 
  message, 
  onSourceClick,
  isStreaming = false,
}: ChatMessageProps) {
  const [copied, setCopied] = React.useState(false);
  const isUser = message.role === 'user';
  
  const copyToClipboard = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'group flex gap-3 px-4 py-4',
        isUser ? 'bg-muted/50' : 'bg-background'
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
          isUser ? 'bg-primary text-primary-foreground' : 'bg-secondary text-secondary-foreground'
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>
      
      {/* Content */}
      <div className="flex-1 space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">
            {isUser ? 'You' : 'AI Assistant'}
          </span>
          <span className="text-xs text-muted-foreground">
            {formatDate(message.timestamp)}
          </span>
        </div>
        
        <div className={cn(
          'prose prose-sm dark:prose-invert max-w-none',
          isStreaming && 'animate-pulse'
        )}>
          {message.content}
          {isStreaming && (
            <span className="ml-1 inline-block h-4 w-1 animate-pulse bg-primary" />
          )}
        </div>
        
        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-3 space-y-1">
            <p className="text-xs font-medium text-muted-foreground">Sources:</p>
            <div className="flex flex-wrap gap-2">
              {message.sources.map((source, i) => (
                <button
                  key={i}
                  onClick={() => onSourceClick?.(source)}
                  className="inline-flex items-center gap-1 rounded-md bg-muted px-2 py-1 text-xs hover:bg-muted/80"
                >
                  <span>Page {source.page}</span>
                  {source.relevance_score && (
                    <span className="text-muted-foreground">
                      ({Math.round(source.relevance_score * 100)}%)
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}
        
        {/* Actions */}
        {!isUser && !isStreaming && (
          <div className="flex items-center gap-2 opacity-0 transition-opacity group-hover:opacity-100">
            <button
              onClick={copyToClipboard}
              className="flex items-center gap-1 rounded p-1 text-xs text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              {copied ? (
                <>
                  <Check className="h-3 w-3" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="h-3 w-3" />
                  Copy
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </motion.div>
  );
}

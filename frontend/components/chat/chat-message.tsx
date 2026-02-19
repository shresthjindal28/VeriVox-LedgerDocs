'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { User, Copy, Check, Sparkles, FileText } from 'lucide-react';
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
        'group flex gap-4 w-full',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex size-8 shrink-0 items-center justify-center rounded-lg shadow-lg ring-1 ring-inset',
          isUser
            ? 'bg-brand-500/20 text-brand-500 ring-brand-500/30'
            : 'bg-black/40 text-brand-400 ring-white/10'
        )}
      >
        {isUser ? <User className="size-4" /> : <Sparkles className="size-4" />}
      </div>

      {/* Content */}
      <div className={cn(
        "flex flex-col max-w-[85%]",
        isUser ? "items-end" : "items-start"
      )}>
        <div className="flex items-center gap-2 mb-1 px-1">
          <span className="text-xs font-medium text-brand-100/40">
            {isUser ? 'You' : 'VeriVox AI'}
          </span>
          <span className="text-[10px] text-brand-100/20">
            {formatDate(message.timestamp)}
          </span>
        </div>

        <div className={cn(
          'rounded-2xl px-5 py-3 text-sm leading-relaxed shadow-sm ring-1 ring-inset',
          isUser
            ? 'bg-brand-500/10 text-brand-50 ring-brand-500/20 rounded-tr-sm'
            : 'bg-brand-950/40 text-brand-100/90 ring-white/10 rounded-tl-sm backdrop-blur-sm',
          isStreaming && 'animate-pulse'
        )}>
          <div className="prose prose-sm prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-black/50 prose-pre:border prose-pre:border-white/10">
            {message.content}
            {isStreaming && (
              <span className="ml-1 inline-block h-4 w-1 animate-pulse bg-brand-500" />
            )}
          </div>
        </div>

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <div className={cn("mt-2 space-y-1.5", isUser && "items-end flex flex-col")}>
            <p className="text-[10px] font-medium text-brand-100/40 uppercase tracking-wider pl-1">Sources Reference</p>
            <div className={cn("flex flex-wrap gap-2", isUser && "justify-end")}>
              {message.sources.map((source, i) => (
                <button
                  key={i}
                  onClick={() => onSourceClick?.(source)}
                  className="group/source inline-flex items-center gap-1.5 rounded-md bg-brand-950/40 px-2.5 py-1.5 text-xs text-brand-200 ring-1 ring-white/10 hover:bg-brand-500/10 hover:ring-brand-500/30 hover:text-brand-100 transition-all"
                >
                  <FileText className="size-3 text-brand-500 opacity-70 group-hover/source:opacity-100" />
                  <span>Page {source.page}</span>
                  {source.relevance_score && (
                    <span className="text-brand-100/30 text-[10px] group-hover/source:text-brand-500/50">
                      {Math.round(source.relevance_score * 100)}%
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        {!isUser && !isStreaming && (
          <div className="mt-1 opacity-0 transition-opacity group-hover:opacity-100 px-1">
            <button
              onClick={copyToClipboard}
              className="flex items-center gap-1 rounded p-1 text-xs text-brand-100/40 hover:text-brand-100 transition-colors"
            >
              {copied ? (
                <>
                  <Check className="h-3 w-3 text-brand-500" />
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

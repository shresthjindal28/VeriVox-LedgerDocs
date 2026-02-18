'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { Send, Mic, MicOff, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ChatInputProps {
  onSend: (message: string) => void;
  onVoiceStart?: () => void;
  onVoiceEnd?: () => void;
  isLoading?: boolean;
  isRecording?: boolean;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  showVoice?: boolean;
}

export function ChatInput({
  onSend,
  onVoiceStart,
  onVoiceEnd,
  isLoading = false,
  isRecording = false,
  placeholder = 'Ask a question about the document...',
  disabled = false,
  className,
  showVoice = true,
}: ChatInputProps) {
  const [input, setInput] = React.useState('');
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading && !disabled) {
      onSend(input.trim());
      setInput('');
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };
  
  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    // Auto-resize textarea
    const textarea = e.target;
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
  };
  
  const handleVoiceToggle = () => {
    if (isRecording) {
      onVoiceEnd?.();
    } else {
      onVoiceStart?.();
    }
  };
  
  return (
    <form onSubmit={handleSubmit} className={cn('border-t bg-background p-4', className)}>
      <div className="flex items-end gap-2">
        <div className="relative flex-1">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled || isLoading}
            rows={1}
            className={cn(
              'w-full resize-none rounded-lg border bg-background px-4 py-3 pr-12 text-sm focus:outline-none focus:ring-2 focus:ring-ring',
              disabled && 'cursor-not-allowed opacity-50'
            )}
          />
          
          {/* Character count */}
          {input.length > 0 && (
            <span className="absolute bottom-2 right-2 text-xs text-muted-foreground">
              {input.length}
            </span>
          )}
        </div>
        
        {/* Voice button */}
        {showVoice && onVoiceStart && (
          <Button
            type="button"
            variant={isRecording ? 'destructive' : 'outline'}
            size="icon"
            onClick={handleVoiceToggle}
            disabled={disabled || isLoading}
            className={cn(isRecording && 'animate-pulse')}
          >
            {isRecording ? (
              <MicOff className="h-4 w-4" />
            ) : (
              <Mic className="h-4 w-4" />
            )}
          </Button>
        )}
        
        {/* Send button */}
        <Button
          type="submit"
          disabled={!input.trim() || isLoading || disabled}
          size="icon"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </div>
    </form>
  );
}

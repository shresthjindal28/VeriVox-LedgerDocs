'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { Send, Mic, MicOff, Loader2, Paperclip, ChevronUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { motion, AnimatePresence } from 'framer-motion';

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

  return (
    <form onSubmit={handleSubmit} className={cn('relative', className)}>
      <motion.div
        layout
        className={cn(
          "relative flex items-end gap-2 p-2 rounded-t-2xl border-t border-brand-500/10 transition-all duration-300",
          "bg-black/40 backdrop-blur-xl",
          input.trim().length > 0 ? "border-brand-500/20" : "border-transparent"
        )}
      >
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled || isLoading}
            rows={1}
            className={cn(
              'w-full resize-none bg-transparent px-4 py-3 text-[15px] leading-relaxed text-brand-50 placeholder:text-brand-100/30 focus:outline-none',
              'custom-scrollbar min-h-[48px] max-h-[200px]',
              disabled && 'cursor-not-allowed opacity-50'
            )}
            style={{ minHeight: '44px' }}
          />
        </div>

        <div className="flex items-center gap-1.5 pb-1.5 pr-1.5">
          {/* Voice Button */}
          {showVoice && onVoiceStart && (
            <div className="relative">
              <AnimatePresence>
                {isRecording && (
                  <motion.div
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1.2, opacity: 1 }}
                    exit={{ scale: 0.8, opacity: 0 }}
                    className="absolute inset-0 bg-red-500/20 rounded-xl blur-md"
                    transition={{ repeat: Infinity, duration: 1.5, repeatType: "reverse" }}
                  />
                )}
              </AnimatePresence>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={isRecording ? onVoiceEnd : onVoiceStart}
                disabled={disabled || isLoading}
                className={cn(
                  "relative h-9 w-9 rounded-xl transition-all duration-300",
                  isRecording
                    ? "text-red-400 bg-red-500/10 hover:bg-red-500/20"
                    : "text-brand-100/40 hover:text-brand-100 hover:bg-white/5"
                )}
              >
                {isRecording ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
              </Button>
            </div>
          )}

          <div className="h-5 w-px bg-white/10 mx-1" />

          {/* Send Button */}
          <Button
            type="submit"
            disabled={!input.trim() || isLoading || disabled}
            size="icon"
            className={cn(
              "h-9 w-9 rounded-xl transition-all duration-300 shadow-lg",
              input.trim()
                ? "bg-brand-500 text-black hover:bg-brand-400 hover:scale-105"
                : "bg-white/5 text-white/20"
            )}
          >
            {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5 ml-0.5" />}
          </Button>
        </div>
      </motion.div>

      {/* Keyboard Hint - Only visible when input has content */}
      <AnimatePresence>
        {input.trim().length > 0 && !isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="absolute -top-8 right-2 flex items-center gap-1.5 text-[10px] text-brand-100/30 font-medium pointer-events-none"
          >
            <span>Press</span>
            <kbd className="h-4 px-1.5 rounded bg-white/5 border border-white/10 flex items-center justify-center font-sans tracking-tight">Return</kbd>
            <span>to send</span>
          </motion.div>
        )}
      </AnimatePresence>
    </form>
  );
}

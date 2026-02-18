'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { Mic, MicOff, Volume2, Loader2, StopCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { motion, AnimatePresence } from 'framer-motion';
import { useVoiceStore } from '@/stores';
import type { ConversationState } from '@/types';

interface VoiceControlsProps {
  onStartListening: () => void;
  onStopListening: () => void;
  onInterrupt: () => void;
  className?: string;
}

export function VoiceControls({
  onStartListening,
  onStopListening,
  onInterrupt,
  className,
}: VoiceControlsProps) {
  const {
    conversationState,
    isRecording,
    isProcessing,
    isPlaying,
    audioLevel,
    transcription,
    lastResponse,
    isConnected,
    error,
  } = useVoiceStore();
  
  const getStateLabel = () => {
    switch (conversationState) {
      case 'listening':
        return 'Listening...';
      case 'processing':
        return 'Processing...';
      case 'speaking':
        return 'Speaking...';
      default:
        return 'Ready';
    }
  };
  
  const getStateColor = () => {
    switch (conversationState) {
      case 'listening':
        return 'bg-red-500';
      case 'processing':
        return 'bg-yellow-500';
      case 'speaking':
        return 'bg-green-500';
      default:
        return 'bg-muted';
    }
  };
  
  return (
    <div className={cn('flex flex-col items-center gap-6', className)}>
      {/* Status indicator */}
      <div className="flex items-center gap-2">
        <div className={cn('h-2 w-2 rounded-full', getStateColor())} />
        <span className="text-sm font-medium">{getStateLabel()}</span>
      </div>
      
      {/* Main controls */}
      <div className="flex items-center gap-4">
        <AnimatePresence mode="wait">
          {conversationState === 'speaking' ? (
            <motion.div
              key="interrupt"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
            >
              <Button
                size="lg"
                variant="destructive"
                onClick={onInterrupt}
                className="h-16 w-16 rounded-full"
              >
                <StopCircle className="h-8 w-8" />
              </Button>
            </motion.div>
          ) : conversationState === 'listening' ? (
            <motion.div
              key="listening"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              className="relative"
            >
              {/* Audio level ring */}
              <motion.div
                className="absolute inset-0 rounded-full bg-red-500/20"
                animate={{ scale: 1 + audioLevel * 0.3 }}
                transition={{ duration: 0.05 }}
              />
              <Button
                size="lg"
                variant="destructive"
                onClick={onStopListening}
                className="relative h-16 w-16 rounded-full"
              >
                <MicOff className="h-8 w-8" />
              </Button>
            </motion.div>
          ) : conversationState === 'processing' ? (
            <motion.div
              key="processing"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
            >
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="idle"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
            >
              <Button
                size="lg"
                onClick={onStartListening}
                disabled={!isConnected}
                className="h-16 w-16 rounded-full"
              >
                <Mic className="h-8 w-8" />
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      
      {/* Connection status */}
      {!isConnected && (
        <p className="text-sm text-destructive">Not connected</p>
      )}
      
      {/* Error */}
      {error && (
        <p className="text-sm text-destructive">{error}</p>
      )}
      
      {/* Transcription */}
      {transcription && (
        <div className="mt-4 w-full max-w-md rounded-lg bg-muted p-4">
          <p className="text-xs font-medium text-muted-foreground">You said:</p>
          <p className="mt-1 text-sm">{transcription}</p>
        </div>
      )}
      
      {/* Response */}
      {lastResponse && (
        <div className="mt-2 w-full max-w-md rounded-lg bg-primary/10 p-4">
          <p className="text-xs font-medium text-muted-foreground">AI Response:</p>
          <p className="mt-1 text-sm">{lastResponse}</p>
        </div>
      )}
    </div>
  );
}

'use client';

import * as React from 'react';
import { useVoiceCall } from '@/hooks/use-voice';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { HighlightItem } from '@/components/pdf';
import {
  Mic,
  MicOff,
  PhoneOff,
  Loader2,
  X
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface VoiceCallProps {
  documentId: string;
  className?: string;
  onHighlights?: (highlights: HighlightItem[]) => void;
  onClose?: () => void;
}

export function VoiceCall({ documentId, className, onHighlights, onClose }: VoiceCallProps) {
  const {
    callState,
    greeting,
    transcription,
    aiTranscript,
    callDuration,
    isMuted,
    error,
    highlights,
    startCall,
    endCall,
    interrupt,
    toggleMute,
    isInCall,
    formatDuration,
  } = useVoiceCall(documentId);

  // Forward highlights to parent when they change
  React.useEffect(() => {
    if (onHighlights && highlights && highlights.length > 0) {
      const mappedHighlights: HighlightItem[] = highlights
        .filter(h => h.bounding_box || h.normalized_box)
        .map((h) => ({
          id: h.id,
          text: h.text,
          page: h.page,
          bounding_box: h.bounding_box || h.normalized_box!,
          normalized_box: h.normalized_box,
          category: h.category,
          color: h.color,
          opacity: h.opacity,
        }));
      onHighlights(mappedHighlights);
    }
  }, [highlights, onHighlights]);

  // Auto-start call when component mounts if not already in call
  React.useEffect(() => {
    if (!isInCall() && callState === 'idle') {
      startCall();
    }
  }, [isInCall, callState, startCall]);

  // Handle closing: end the WebSocket call, then dismiss the overlay
  const handleClose = React.useCallback(() => {
    console.log("[VoiceCall UI] handleClose called, isInCall:", isInCall());
    endCall();
    onClose?.();
  }, [isInCall, endCall, onClose]);

  // Handle stop: end the WebSocket call, then dismiss after a brief pause
  const handleStop = React.useCallback(() => {
    console.log("[VoiceCall UI] handleStop called");
    endCall();
    // Short delay so the user sees "Session Ended" before the overlay closes
    setTimeout(() => {
      console.log("[VoiceCall UI] closing overlay after stop");
      onClose?.();
    }, 600);
  }, [endCall, onClose]);

  // Cleanup on unmount — always end the call if component is removed
  React.useEffect(() => {
    return () => {
      console.log("[VoiceCall UI] unmounting, calling endCall");
      endCall();
    };
  }, [endCall]);

  const renderVisualizer = () => {
    const isAiSpeaking = callState === 'ai_speaking';
    const isUserSpeaking = callState === 'user_speaking';
    const isProcessing = callState === 'processing';

    return (
      <div className="relative flex items-center justify-center h-64 w-64 mx-auto my-12">
        {/* Ambient Glow / Aura */}
        <motion.div
          animate={{
            scale: isAiSpeaking ? [1, 1.2, 1] : isUserSpeaking ? [1, 1.1, 1] : 1,
            rotate: [0, 180, 360],
          }}
          transition={{
            scale: { duration: 4, repeat: Infinity, ease: "easeInOut" },
            rotate: { duration: 20, repeat: Infinity, ease: "linear" }
          }}
          className={cn(
            "absolute inset-0 rounded-full blur-[60px] opacity-40",
            titleGradient(callState)
          )}
        />

        {/* Core Orb */}
        <div className="relative h-32 w-32">
          {/* Fluid Gradient Mesh */}
          <motion.div
            animate={{
              rotate: [0, -360],
              scale: isAiSpeaking ? [1, 1.1, 1] : isProcessing ? [1, 0.9, 1] : 1,
            }}
            transition={{
              rotate: { duration: 15, repeat: Infinity, ease: "linear" },
              scale: { duration: 2, repeat: Infinity, ease: "easeInOut" }
            }}
            className={cn(
              "absolute inset-0 rounded-full bg-gradient-to-br opacity-90 blur-xl",
              gradientColors(callState)
            )}
          />

          {/* Inner Core */}
          <motion.div
            animate={{
              scale: isUserSpeaking ? [1, 0.9, 1] : [1, 1.05, 1],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut"
            }}
            className="absolute inset-2 rounded-full bg-white/20 backdrop-blur-2xl border border-white/30 shadow-[inset_0_0_20px_rgba(255,255,255,0.2)]"
          />
        </div>
      </div>
    );
  };

  const titleGradient = (state: string) => {
    switch (state) {
      case 'ai_speaking': return "bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-500";
      case 'user_speaking': return "bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500";
      case 'processing': return "bg-gradient-to-r from-pink-500 via-rose-500 to-orange-500";
      case 'error': return "bg-gradient-to-r from-red-500 via-orange-500 to-red-500";
      default: return "bg-gradient-to-r from-brand-500 via-amber-500 to-yellow-500";
    }
  };

  const gradientColors = (state: string) => {
    switch (state) {
      case 'ai_speaking': return "from-cyan-400 via-blue-500 to-purple-600";
      case 'user_speaking': return "from-emerald-400 via-teal-500 to-cyan-600";
      case 'processing': return "from-pink-400 via-rose-500 to-orange-600";
      case 'error': return "from-red-500 via-orange-500 to-red-600";
      default: return "from-brand-400 via-amber-500 to-yellow-600";
    }
  };

  const getStatusText = () => {
    switch (callState) {
      case 'connecting': return 'Connecting...';
      case 'connected': return 'Listening...';
      case 'user_speaking': return 'Listening...';
      case 'processing': return 'Thinking...';
      case 'ai_speaking': return 'Speaking...';
      case 'error': return 'Connection Issue';
      case 'ended': return 'Session Ended';
      default: return 'Ready';
    }
  };

  return (
    <div className={cn("flex flex-col h-full bg-black/90 backdrop-blur-3xl text-white relative overflow-hidden", className)}>
      {/* Close Button (Top Right) — also terminates the WebSocket */}
      <Button
        variant="ghost"
        size="icon"
        className="absolute top-6 right-6 text-white/40 hover:text-white hover:bg-white/10 z-50 rounded-full"
        onClick={handleClose}
      >
        <X className="h-6 w-6" />
      </Button>

      {/* Main Content */}
      <div className="flex-1 flex flex-col items-center justify-center p-6 text-center z-10">

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4"
        >
          <h3 className="text-xl font-medium tracking-tight text-white/90">VeriVox Intelligence</h3>
        </motion.div>

        {renderVisualizer()}

        <motion.div className="h-8 mb-8 flex flex-col items-center justify-center">
          <p className={cn(
            "text-sm font-medium tracking-widest uppercase transition-colors duration-500 flex items-center gap-2",
            callState === 'error' ? "text-red-400" : "text-white/60"
          )}>
            {callState === 'processing' && <Loader2 className="h-3 w-3 animate-spin" />}
            {getStatusText()}
          </p>
          {isInCall() && (
            <span className="text-xs font-mono text-white/20 mt-1">
              {formatDuration()}
            </span>
          )}
        </motion.div>


        {/* Transcriptions */}
        <div className="h-24 w-full max-w-lg mx-auto flex items-end justify-center px-4 overflow-hidden relative">
          {/* Gradient fade at top */}
          <div className="absolute top-0 left-0 right-0 h-6 bg-gradient-to-b from-black/80 to-transparent z-10 pointer-events-none" />
          <AnimatePresence mode="wait">
            {aiTranscript ? (() => {
              // Strip markdown formatting: **bold**, __bold__, *italic*, _italic_, ## headers, etc.
              const clean = aiTranscript
                .replace(/#{1,6}\s?/g, '')      // remove ## headers
                .replace(/\*\*([^*]+)\*\*/g, '$1') // **bold** → bold
                .replace(/__([^_]+)__/g, '$1')    // __bold__ → bold
                .replace(/\*([^*]+)\*/g, '$1')    // *italic* → italic
                .replace(/_([^_]+)_/g, '$1')      // _italic_ → italic
                .replace(/`([^`]+)`/g, '$1')      // `code` → code
                .replace(/\n+/g, ' ')             // newlines → spaces
                .trim();
              // Show only the last ~200 characters
              const truncated = clean.length > 200
                ? '…' + clean.slice(-200)
                : clean;
              return (
                <motion.p
                  key="ai"
                  initial={{ opacity: 0, filter: "blur(10px)" }}
                  animate={{ opacity: 1, filter: "blur(0px)" }}
                  exit={{ opacity: 0, filter: "blur(10px)" }}
                  className="text-sm md:text-base text-white/80 font-light leading-relaxed text-center"
                >
                  {truncated}
                </motion.p>
              );
            })() : transcription ? (
              <motion.p
                key="user"
                initial={{ opacity: 0, filter: "blur(5px)" }}
                animate={{ opacity: 1, filter: "blur(0px)" }}
                exit={{ opacity: 0, filter: "blur(5px)" }}
                className="text-sm md:text-base text-white/50 font-light italic text-center"
              >
                &ldquo;{transcription.length > 150 ? '…' + transcription.slice(-150) : transcription}&rdquo;
              </motion.p>
            ) : greeting ? (
              <motion.p
                key="greeting"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-base text-white/40 font-light text-center"
              >
                {greeting}
              </motion.p>
            ) : null}
          </AnimatePresence>
        </div>

        {/* Controls */}
        <div className="mt-auto mb-12">
          {!isInCall() ? (
            <Button
              onClick={startCall}
              size="lg"
              className="h-16 px-8 rounded-full bg-white/10 hover:bg-white/20 backdrop-blur-md border border-white/10 text-white font-medium transition-all hover:scale-105"
            >
              <Mic className="h-5 w-5 mr-3" />
              Start Conversation
            </Button>
          ) : (
            <div className="flex items-center gap-4">
              {/* Mute / Unmute */}
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleMute}
                className={cn(
                  "h-14 w-14 rounded-full transition-all border",
                  isMuted
                    ? "text-red-400 bg-red-500/10 border-red-500/30 hover:bg-red-500/20"
                    : "text-white/80 bg-white/5 border-white/10 hover:bg-white/10"
                )}
              >
                {isMuted ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
              </Button>

              {/* End Call — prominent red button */}
              <Button
                onClick={handleStop}
                size="icon"
                className="h-16 w-16 rounded-full bg-red-500 hover:bg-red-600 text-white shadow-lg shadow-red-500/30 hover:shadow-red-500/50 transition-all hover:scale-105 active:scale-95"
              >
                <PhoneOff className="h-6 w-6" />
              </Button>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}


'use client';

import * as React from 'react';
import { useVoiceCall } from '@/hooks/use-voice';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { HighlightItem } from '@/components/pdf';
import { 
  PhoneCall, 
  PhoneOff, 
  Mic, 
  MicOff, 
  Square,
  Loader2,
  Volume2,
  User,
  Bot
} from 'lucide-react';

interface VoiceCallProps {
  documentId: string;
  className?: string;
  onHighlights?: (highlights: HighlightItem[]) => void;
}

export function VoiceCall({ documentId, className, onHighlights }: VoiceCallProps) {
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
      // Map to HighlightItem format
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

  const renderCallState = () => {
    switch (callState) {
      case 'connecting':
        return (
          <div className="flex items-center gap-2 text-yellow-600">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Connecting...</span>
          </div>
        );
      case 'connected':
        return (
          <div className="flex items-center gap-2 text-green-600">
            <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
            <span>Connected - Start speaking</span>
          </div>
        );
      case 'user_speaking':
        return (
          <div className="flex items-center gap-2 text-blue-600">
            <User className="h-4 w-4" />
            <span>Listening...</span>
          </div>
        );
      case 'processing':
        return (
          <div className="flex items-center gap-2 text-amber-600">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Processing...</span>
          </div>
        );
      case 'ai_speaking':
        return (
          <div className="flex items-center gap-2 text-purple-600">
            <Bot className="h-4 w-4" />
            <Volume2 className="h-4 w-4 animate-pulse" />
            <span>AI Speaking</span>
          </div>
        );
      case 'error':
        return (
          <div className="flex items-center gap-2 text-red-600">
            <span>Error: {error}</span>
          </div>
        );
      case 'ended':
        return (
          <div className="flex items-center gap-2 text-gray-600">
            <span>Call ended</span>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className={cn("flex flex-col gap-4 p-4 rounded-lg border bg-card", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-lg">Voice Call</h3>
        {isInCall() && (
          <span className="text-sm font-mono text-muted-foreground">
            {formatDuration()}
          </span>
        )}
      </div>

      {/* Call State Indicator */}
      <div className="min-h-[24px]">
        {renderCallState()}
      </div>

      {/* Greeting */}
      {greeting && callState === 'connected' && (
        <div className="p-3 rounded-md bg-muted/50 text-sm">
          <p className="text-muted-foreground">{greeting}</p>
        </div>
      )}

      {/* Transcriptions */}
      {isInCall() && (transcription || aiTranscript) && (
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {transcription && (
            <div className="flex gap-2">
              <User className="h-4 w-4 mt-1 text-blue-500 shrink-0" />
              <p className="text-sm">{transcription}</p>
            </div>
          )}
          {aiTranscript && (
            <div className="flex gap-2">
              <Bot className="h-4 w-4 mt-1 text-purple-500 shrink-0" />
              <p className="text-sm text-muted-foreground">{aiTranscript}</p>
            </div>
          )}
        </div>
      )}

      {/* Error Message */}
      {error && callState !== 'error' && (
        <div className="p-2 rounded-md bg-red-50 text-red-600 text-sm">
          {error}
        </div>
      )}

      {/* Call Controls */}
      <div className="flex items-center gap-2 justify-center pt-2">
        {!isInCall() ? (
          <Button
            onClick={startCall}
            size="lg"
            className="gap-2 bg-green-600 hover:bg-green-700"
          >
            <PhoneCall className="h-5 w-5" />
            Start Call
          </Button>
        ) : (
          <>
            {/* Mute Button */}
            <Button
              variant="outline"
              size="icon"
              onClick={toggleMute}
              className={cn(
                "h-12 w-12 rounded-full",
                isMuted && "bg-red-100 border-red-300"
              )}
            >
              {isMuted ? (
                <MicOff className="h-5 w-5 text-red-600" />
              ) : (
                <Mic className="h-5 w-5" />
              )}
            </Button>

            {/* Interrupt Button (when AI is speaking) */}
            {callState === 'ai_speaking' && (
              <Button
                variant="outline"
                size="icon"
                onClick={interrupt}
                className="h-12 w-12 rounded-full"
              >
                <Square className="h-5 w-5" />
              </Button>
            )}

            {/* End Call Button */}
            <Button
              onClick={endCall}
              size="icon"
              variant="destructive"
              className="h-12 w-12 rounded-full"
            >
              <PhoneOff className="h-5 w-5" />
            </Button>
          </>
        )}
      </div>

      {/* Call ended summary */}
      {callState === 'ended' && callDuration > 0 && (
        <div className="text-center text-sm text-muted-foreground">
          <p>Call duration: {formatDuration()}</p>
          <Button
            variant="link"
            size="sm"
            onClick={startCall}
            className="mt-2"
          >
            Start new call
          </Button>
        </div>
      )}
    </div>
  );
}

/**
 * Compact version for floating UI
 */
interface VoiceCallButtonProps {
  documentId: string;
  onClick?: () => void;
  className?: string;
}

export function VoiceCallButton({ documentId, onClick, className }: VoiceCallButtonProps) {
  const {
    callState,
    startCall,
    endCall,
    isInCall,
    formatDuration,
  } = useVoiceCall(documentId);

  const handleStartCall = () => {
    if (onClick) onClick();
    startCall();
  };

  if (!isInCall()) {
    return (
      <Button
        onClick={handleStartCall}
        size="icon"
        className={cn("h-14 w-14 rounded-full bg-green-600 hover:bg-green-700 shadow-lg", className)}
        title="Start voice call"
      >
        <PhoneCall className="h-6 w-6" />
      </Button>
    );
  }

  return (
    <div className={cn("flex items-center gap-2 bg-card rounded-full shadow-lg p-2 border", className)}>
      <span className="text-sm font-mono px-2">{formatDuration()}</span>
      <div className={cn(
        "h-3 w-3 rounded-full",
        callState === 'ai_speaking' ? "bg-purple-500 animate-pulse" :
        callState === 'user_speaking' ? "bg-blue-500 animate-pulse" :
        callState === 'processing' ? "bg-amber-500 animate-pulse" :
        "bg-green-500"
      )} />
      <Button
        onClick={endCall}
        size="icon"
        variant="destructive"
        className="h-10 w-10 rounded-full"
      >
        <PhoneOff className="h-4 w-4" />
      </Button>
    </div>
  );
}

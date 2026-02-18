'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { Mic, MicOff, Volume2, VolumeX, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { motion, AnimatePresence } from 'framer-motion';
import { useVoiceStore } from '@/stores';

interface VoiceRecorderProps {
  onRecordingComplete: (audioBlob: Blob) => void;
  onRecordingStart?: () => void;
  onRecordingCancel?: () => void;
  isProcessing?: boolean;
  className?: string;
}

export function VoiceRecorder({
  onRecordingComplete,
  onRecordingStart,
  onRecordingCancel,
  isProcessing = false,
  className,
}: VoiceRecorderProps) {
  const [isRecording, setIsRecording] = React.useState(false);
  const [duration, setDuration] = React.useState(0);
  const [audioLevel, setAudioLevel] = React.useState(0);
  
  const mediaRecorderRef = React.useRef<MediaRecorder | null>(null);
  const chunksRef = React.useRef<Blob[]>([]);
  const streamRef = React.useRef<MediaStream | null>(null);
  const analyserRef = React.useRef<AnalyserNode | null>(null);
  const animationRef = React.useRef<number | null>(null);
  const timerRef = React.useRef<NodeJS.Timeout | null>(null);
  
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      // Set up audio analysis
      const audioContext = new AudioContext();
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;
      
      // Start level monitoring
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const updateLevel = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
        setAudioLevel(average / 255);
        animationRef.current = requestAnimationFrame(updateLevel);
      };
      updateLevel();
      
      // Set up MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
      });
      
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        onRecordingComplete(blob);
        cleanup();
      };
      
      mediaRecorder.start(100);
      setIsRecording(true);
      setDuration(0);
      onRecordingStart?.();
      
      // Start duration timer
      timerRef.current = setInterval(() => {
        setDuration((d) => d + 1);
      }, 1000);
      
    } catch (error) {
      console.error('Failed to start recording:', error);
    }
  };
  
  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
  };
  
  const cancelRecording = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    cleanup();
    setIsRecording(false);
    onRecordingCancel?.();
  };
  
  const cleanup = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    analyserRef.current = null;
    setAudioLevel(0);
    setDuration(0);
  };
  
  React.useEffect(() => {
    return () => cleanup();
  }, []);
  
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };
  
  return (
    <div className={cn('flex flex-col items-center', className)}>
      <AnimatePresence mode="wait">
        {isProcessing ? (
          <motion.div
            key="processing"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            className="flex flex-col items-center"
          >
            <div className="mb-4 flex h-24 w-24 items-center justify-center rounded-full bg-primary/10">
              <Loader2 className="h-10 w-10 animate-spin text-primary" />
            </div>
            <p className="text-sm text-muted-foreground">Processing...</p>
          </motion.div>
        ) : isRecording ? (
          <motion.div
            key="recording"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            className="flex flex-col items-center"
          >
            {/* Audio level visualization */}
            <div className="relative mb-4">
              <motion.div
                className="absolute inset-0 rounded-full bg-red-500/20"
                animate={{ scale: 1 + audioLevel * 0.5 }}
                transition={{ duration: 0.1 }}
              />
              <Button
                size="lg"
                variant="destructive"
                onClick={stopRecording}
                className="relative h-24 w-24 rounded-full"
              >
                <MicOff className="h-10 w-10" />
              </Button>
            </div>
            
            <p className="mb-2 font-mono text-lg">{formatDuration(duration)}</p>
            <p className="text-sm text-muted-foreground">Click to stop recording</p>
            
            <button
              onClick={cancelRecording}
              className="mt-4 text-sm text-muted-foreground hover:text-foreground"
            >
              Cancel
            </button>
          </motion.div>
        ) : (
          <motion.div
            key="idle"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            className="flex flex-col items-center"
          >
            <Button
              size="lg"
              onClick={startRecording}
              className="h-24 w-24 rounded-full"
            >
              <Mic className="h-10 w-10" />
            </Button>
            <p className="mt-4 text-sm text-muted-foreground">Click to start recording</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

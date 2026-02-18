"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { voiceApi } from "@/lib/api";
import { useVoiceStore, useCallStore } from "@/stores";
import { useCallback, useRef, useEffect, useState } from "react";

// Query keys
export const voiceKeys = {
  all: ["voice"] as const,
  voices: () => [...voiceKeys.all, "voices"] as const,
  health: () => [...voiceKeys.all, "health"] as const,
};

// ============================================================================
// Voice API Hooks
// ============================================================================

export function useVoices() {
  const { setAvailableVoices } = useVoiceStore();

  return useQuery({
    queryKey: voiceKeys.voices(),
    queryFn: async () => {
      const data = await voiceApi.getVoices();
      setAvailableVoices(data);
      return data;
    },
    staleTime: 60 * 60 * 1000, // 1 hour
  });
}

export function useVoiceHealth() {
  return useQuery({
    queryKey: voiceKeys.health(),
    queryFn: () => voiceApi.getHealth(),
    staleTime: 30 * 1000,
    refetchInterval: 60 * 1000,
  });
}

export function useTranscribe() {
  const { setTranscription, setProcessing, setError } = useVoiceStore();

  return useMutation({
    mutationFn: (audio: Blob) => voiceApi.transcribe(audio),
    onMutate: () => {
      setProcessing(true);
    },
    onSuccess: (data) => {
      setTranscription(data.text);
    },
    onError: (error: Error) => {
      setError(error.message);
    },
    onSettled: () => {
      setProcessing(false);
    },
  });
}

export function useSynthesize() {
  const { setPlaying, setCurrentAudio, setError, selectedVoice } =
    useVoiceStore();

  return useMutation({
    mutationFn: ({ text, voice }: { text: string; voice?: string }) =>
      voiceApi.synthesize(text, voice || selectedVoice),
    onSuccess: async (blob) => {
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);

      audio.onended = () => {
        setPlaying(false);
        setCurrentAudio(null);
        URL.revokeObjectURL(url);
      };

      setCurrentAudio(audio);
      setPlaying(true);
      await audio.play();
    },
    onError: (error: Error) => {
      setError(error.message);
    },
  });
}

export function useVoiceChatWithAudio(documentId: string) {
  const {
    setProcessing,
    setPlaying,
    setCurrentAudio,
    setError,
    selectedVoice,
  } = useVoiceStore();

  return useMutation({
    mutationFn: async (audio: Blob) => {
      const formData = new FormData();
      formData.append("audio", audio, "recording.webm");
      formData.append("document_id", documentId);
      formData.append("voice", selectedVoice);
      return voiceApi.chatWithAudio(formData);
    },
    onMutate: () => {
      setProcessing(true);
    },
    onSuccess: async (blob) => {
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);

      audio.onended = () => {
        setPlaying(false);
        setCurrentAudio(null);
        URL.revokeObjectURL(url);
      };

      setCurrentAudio(audio);
      setPlaying(true);
      setProcessing(false);
      await audio.play();
    },
    onError: (error: Error) => {
      setError(error.message);
      setProcessing(false);
    },
  });
}

// ============================================================================
// Audio Recording Hook
// ============================================================================

export function useAudioRecorder() {
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationRef = useRef<number | null>(null);

  const { setRecording, setAudioLevel, setError, isRecording } =
    useVoiceStore();

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Set up audio analysis for level meter
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
        mimeType: "audio/webm;codecs=opus",
      });

      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.start(100); // Collect data every 100ms
      setRecording(true);
    } catch (error) {
      setError("Failed to access microphone");
      console.error("Recording error:", error);
    }
  }, [setRecording, setAudioLevel, setError]);

  const stopRecording = useCallback((): Promise<Blob> => {
    return new Promise((resolve, reject) => {
      const mediaRecorder = mediaRecorderRef.current;

      if (!mediaRecorder || mediaRecorder.state === "inactive") {
        reject(new Error("No active recording"));
        return;
      }

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        resolve(blob);

        // Cleanup
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }
        if (animationRef.current) {
          cancelAnimationFrame(animationRef.current);
          animationRef.current = null;
        }
        analyserRef.current = null;
        setAudioLevel(0);
      };

      mediaRecorder.stop();
      setRecording(false);
    });
  }, [setRecording, setAudioLevel]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []);

  return {
    startRecording,
    stopRecording,
    isRecording,
  };
}

// ============================================================================
// Real-time Voice WebSocket Hook
// ============================================================================

interface VoiceMessage {
  type:
    | "transcription"
    | "response_start"
    | "response_text"
    | "response_end"
    | "interrupted"
    | "error";
  text?: string;
  message?: string;
}

export function useRealtimeVoice(documentId: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<AudioBuffer[]>([]);
  const isPlayingRef = useRef(false);

  const {
    setConnected,
    setConnectionOpen,
    setConversationState,
    setTranscription,
    setLastResponse,
    setPlaying,
    setError,
    stopPlayback,
    selectedVoice,
  } = useVoiceStore();

  const playNextChunk = useCallback(() => {
    if (audioQueueRef.current.length === 0 || !audioContextRef.current) {
      isPlayingRef.current = false;
      return;
    }

    isPlayingRef.current = true;
    const buffer = audioQueueRef.current.shift()!;
    const source = audioContextRef.current.createBufferSource();
    source.buffer = buffer;
    source.connect(audioContextRef.current.destination);
    source.onended = () => playNextChunk();
    source.start();
  }, []);

  const playAudioChunk = useCallback(
    async (arrayBuffer: ArrayBuffer) => {
      if (!audioContextRef.current) {
        audioContextRef.current = new AudioContext();
      }

      try {
        const audioBuffer = await audioContextRef.current.decodeAudioData(
          arrayBuffer.slice(0),
        );
        audioQueueRef.current.push(audioBuffer);

        if (!isPlayingRef.current) {
          playNextChunk();
        }
      } catch (e) {
        console.error("Failed to decode audio:", e);
      }
    },
    [playNextChunk],
  );

  const handleMessage = useCallback(
    (data: VoiceMessage) => {
      switch (data.type) {
        case "transcription":
          setTranscription(data.text || "");
          setConversationState("processing");
          break;

        case "response_start":
          setConversationState("speaking");
          setPlaying(true);
          break;

        case "response_text":
          setLastResponse(data.text || "");
          break;

        case "response_end":
          setConversationState("idle");
          setPlaying(false);
          break;

        case "interrupted":
          stopPlayback();
          setConversationState("listening");
          break;

        case "error":
          setError(data.message || "Unknown error");
          setConversationState("idle");
          break;
      }
    },
    [
      setTranscription,
      setConversationState,
      setPlaying,
      setLastResponse,
      stopPlayback,
      setError,
    ],
  );

  const connect = useCallback(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8080";
    const ws = new WebSocket(`${wsUrl}/ws/voice/realtime/${documentId}`);

    ws.binaryType = "arraybuffer";

    ws.onopen = () => {
      setConnected(true);
      setConnectionOpen(true);
      setConversationState("idle");

      // Send initial config
      ws.send(
        JSON.stringify({
          type: "config",
          voice: selectedVoice,
        }),
      );
    };

    ws.onclose = () => {
      setConnected(false);
      setConnectionOpen(false);
      setConversationState("idle");
    };

    ws.onerror = () => {
      setError("Voice connection error");
      setConnected(false);
    };

    ws.onmessage = async (event) => {
      if (event.data instanceof ArrayBuffer) {
        // Audio data
        await playAudioChunk(event.data);
      } else {
        // JSON message
        try {
          const data = JSON.parse(event.data) as VoiceMessage;
          handleMessage(data);
        } catch (e) {
          console.error("Failed to parse voice message:", e);
        }
      }
    };

    wsRef.current = ws;
    return ws;
  }, [
    documentId,
    selectedVoice,
    setConnected,
    setConnectionOpen,
    setConversationState,
    setError,
    playAudioChunk,
    handleMessage,
  ]);

  const sendAudio = useCallback((audioData: ArrayBuffer) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(audioData);
    }
  }, []);

  const interrupt = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "interrupt" }));
      stopPlayback();
      audioQueueRef.current = [];
    }
  }, [stopPlayback]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    audioQueueRef.current = [];
    setConnected(false);
    setConnectionOpen(false);
  }, [setConnected, setConnectionOpen]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    connect,
    sendAudio,
    interrupt,
    disconnect,
    isConnected: () => wsRef.current?.readyState === WebSocket.OPEN,
  };
}

// ============================================================================
// Voice Call Hook (OpenAI Realtime API)
// ============================================================================

type CallState =
  | "idle"
  | "connecting"
  | "connected"
  | "user_speaking"
  | "ai_speaking"
  | "processing"
  | "ended"
  | "error";

interface CallMessage {
  type: string;
  session_id?: string;
  greeting?: string;
  voice_mode?: string;
  state?: string;
  role?: string;
  text?: string;
  data?: string;
  duration_seconds?: number;
  questions_asked?: number;
  message?: string;
  code?: string;
  reason?: string;
  highlights?: Array<{
    id: string;
    text: string;
    page: number;
    bounding_box?: {
      x1: number;
      y1: number;
      x2: number;
      y2: number;
    };
    normalized_box?: {
      x1: number;
      y1: number;
      x2: number;
      y2: number;
    };
    category?: string;
    color?: string;
    opacity?: number;
  }>;
}

/**
 * AudioWorklet processor for capturing PCM16 audio at 24kHz
 */
const PCM16_WORKLET_CODE = `
class PCM16Processor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.bufferSize = 2400; // 100ms at 24kHz
    this.buffer = new Float32Array(this.bufferSize);
    this.bufferIndex = 0;
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (input.length === 0) return true;
    
    const channelData = input[0];
    for (let i = 0; i < channelData.length; i++) {
      this.buffer[this.bufferIndex++] = channelData[i];
      
      if (this.bufferIndex >= this.bufferSize) {
        // Convert to PCM16
        const pcm16 = new Int16Array(this.bufferSize);
        for (let j = 0; j < this.bufferSize; j++) {
          const s = Math.max(-1, Math.min(1, this.buffer[j]));
          pcm16[j] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        
        this.port.postMessage({ pcm16: pcm16.buffer }, [pcm16.buffer]);
        this.bufferIndex = 0;
      }
    }
    
    return true;
  }
}

registerProcessor('pcm16-processor', PCM16Processor);
`;

export function useVoiceCall(documentId: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const playbackContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<Float32Array[]>([]);
  const isPlayingRef = useRef<boolean>(false);
  const gainNodeRef = useRef<GainNode | null>(null);
  const currentSourceRef = useRef<AudioBufferSourceNode | null>(null);

  const [callState, setCallState] = useState<CallState>("idle");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [greeting, setGreeting] = useState<string | null>(null);
  const [transcription, setTranscription] = useState<string | null>(null);
  const [aiTranscript, setAiTranscript] = useState<string>("");
  const [callDuration, setCallDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [highlights, setHighlights] = useState<CallMessage["highlights"]>([]);

  const callStartTimeRef = useRef<number | null>(null);
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Clear audio queue and stop current playback
  const clearAudioQueue = useCallback(() => {
    // Stop current playback
    if (currentSourceRef.current) {
      try {
        currentSourceRef.current.stop();
      } catch (e) {
        // Source may already be stopped
      }
      currentSourceRef.current = null;
    }

    // Clear queue
    audioQueueRef.current = [];
    isPlayingRef.current = false;
  }, []);

  // Process audio queue sequentially to prevent overlapping playback
  const processAudioQueue = useCallback(async () => {
    if (isPlayingRef.current || audioQueueRef.current.length === 0) {
      return;
    }

    if (!playbackContextRef.current) {
      playbackContextRef.current = new AudioContext({ sampleRate: 24000 });
      gainNodeRef.current = playbackContextRef.current.createGain();
      gainNodeRef.current.connect(playbackContextRef.current.destination);
      gainNodeRef.current.gain.value = 1.0;
    }

    isPlayingRef.current = true;
    const context = playbackContextRef.current;
    const gainNode = gainNodeRef.current!;

    while (audioQueueRef.current.length > 0) {
      const float32Data = audioQueueRef.current.shift()!;

      try {
        // Create audio buffer
        const audioBuffer = context.createBuffer(1, float32Data.length, 24000);
        audioBuffer.getChannelData(0).set(float32Data);

        // Create source and play
        const source = context.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(gainNode);
        currentSourceRef.current = source;

        // Wait for this chunk to finish before playing next
        await new Promise<void>((resolve) => {
          source.onended = () => {
            currentSourceRef.current = null;
            resolve();
          };
          source.start();
        });
      } catch (e) {
        // If stopped, that's fine - just exit
        if (e instanceof DOMException && e.name === "InvalidStateError") {
          currentSourceRef.current = null;
          break;
        }
        console.error("Failed to play audio chunk:", e);
      }
    }

    isPlayingRef.current = false;
    currentSourceRef.current = null;
  }, []);

  // Play PCM16 audio (queued)
  const playPCM16Audio = useCallback(
    async (base64Data: string) => {
      try {
        // Decode base64 to ArrayBuffer
        const binaryString = atob(base64Data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }

        // Convert PCM16 to Float32
        const pcm16 = new Int16Array(bytes.buffer);
        const float32 = new Float32Array(pcm16.length);
        for (let i = 0; i < pcm16.length; i++) {
          float32[i] = pcm16[i] / 32768;
        }

        // Add to queue
        audioQueueRef.current.push(float32);

        // Process queue
        processAudioQueue();
      } catch (e) {
        console.error("Failed to queue PCM16 audio:", e);
      }
    },
    [processAudioQueue],
  );

  // Handle WebSocket messages
  const handleMessage = useCallback(
    (data: CallMessage) => {
      switch (data.type) {
        case "call_started":
          setSessionId(data.session_id || null);
          setGreeting(data.greeting || null);
          setCallState("connected");
          break;

        case "state_change":
          if (data.state === "user_speaking") {
            // User started speaking - clear any queued AI audio immediately
            clearAudioQueue();
            setCallState("user_speaking");
          } else if (data.state === "ai_speaking") {
            setCallState("ai_speaking");
          } else if (data.state === "processing") {
            // Processing new response - clear old audio queue
            clearAudioQueue();
            setCallState("processing");
          } else if (data.state === "connected") {
            setCallState("connected");
          } else if (data.state === "muted") {
            setIsMuted(true);
          } else if (data.state === "unmuted") {
            setIsMuted(false);
          }
          break;

        case "transcription":
          if (data.role === "user") {
            setTranscription(data.text || null);
          } else if (data.role === "assistant") {
            setAiTranscript(data.text || "");
          } else if (data.role === "assistant_delta") {
            setAiTranscript((prev) => prev + (data.text || ""));
          }
          break;

        case "audio_chunk":
          if (data.data) {
            playPCM16Audio(data.data);
          }
          break;

        case "audio_end":
          // Audio streaming complete for this response
          break;

        case "highlights":
          // Received highlights from exhaustive extraction
          if (data.highlights && data.highlights.length > 0) {
            setHighlights(data.highlights);
          }
          break;

        case "call_ended":
          setCallState("ended");
          setCallDuration(data.duration_seconds || 0);
          break;

        case "fallback_activated":
          console.log("Fallback activated:", data.reason);
          break;

        case "error":
          setError(data.message || "Unknown error");
          if (
            data.code === "permission_denied" ||
            data.code === "call_start_failed"
          ) {
            setCallState("error");
          }
          break;

        case "pong":
          // Keep-alive response
          break;
      }
    },
    [playPCM16Audio, clearAudioQueue],
  );

  // Start call
  const startCall = useCallback(async () => {
    if (
      callState !== "idle" &&
      callState !== "ended" &&
      callState !== "error"
    ) {
      return;
    }

    setCallState("connecting");
    setError(null);
    setTranscription(null);
    setAiTranscript("");

    try {
      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 24000,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
      streamRef.current = stream;

      // Set up WebSocket (browsers cannot set headers; pass token in query for gateway auth)
      const token =
        typeof window !== "undefined"
          ? localStorage.getItem("access_token") ||
            localStorage.getItem("auth_token")
          : null;
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8080";
      const path = `/ws/voice/call/${documentId}`;
      const url = token
        ? `${wsUrl}${path}?token=${encodeURIComponent(token)}`
        : `${wsUrl}${path}`;
      const ws = new WebSocket(url);

      // Track if call has been started (wait for call_started message)
      let callStarted = false;

      ws.onopen = async () => {
        // Send start_call message immediately when WebSocket opens
        console.log("WebSocket opened, sending start_call");
        ws.send(JSON.stringify({ type: "start_call" }));

        // Set up AudioWorklet AFTER WebSocket is open
        // But don't start sending audio until call_started is received
        audioContextRef.current = new AudioContext({ sampleRate: 24000 });

        // Create worklet from inline code
        const blob = new Blob([PCM16_WORKLET_CODE], {
          type: "application/javascript",
        });
        const workletUrl = URL.createObjectURL(blob);
        await audioContextRef.current.audioWorklet.addModule(workletUrl);
        URL.revokeObjectURL(workletUrl);

        const source = audioContextRef.current.createMediaStreamSource(stream);
        const workletNode = new AudioWorkletNode(
          audioContextRef.current,
          "pcm16-processor",
        );

        workletNode.port.onmessage = (event) => {
          // Only send audio chunks after call has been started
          if (
            callStarted &&
            !isMuted &&
            ws.readyState === WebSocket.OPEN &&
            event.data.pcm16
          ) {
            // Convert ArrayBuffer to base64
            const bytes = new Uint8Array(event.data.pcm16);
            let binary = "";
            for (let i = 0; i < bytes.byteLength; i++) {
              binary += String.fromCharCode(bytes[i]);
            }
            const base64 = btoa(binary);

            ws.send(
              JSON.stringify({
                type: "audio_chunk",
                data: base64,
              }),
            );
          }
        };

        source.connect(workletNode);
        workletNode.connect(audioContextRef.current.destination);
        workletNodeRef.current = workletNode;
      };

      ws.onclose = () => {
        callStarted = false;
        if (callState !== "ended") {
          setCallState("ended");
        }
      };

      ws.onerror = () => {
        callStarted = false;
        setError("Connection error");
        setCallState("error");
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as CallMessage;

          // Mark call as started when we receive call_started message
          if (data.type === "call_started") {
            callStarted = true;
            console.log("Call started, audio capture enabled");
            // Start call duration timer
            callStartTimeRef.current = Date.now();
            durationIntervalRef.current = setInterval(() => {
              if (callStartTimeRef.current) {
                setCallDuration(
                  Math.floor((Date.now() - callStartTimeRef.current) / 1000),
                );
              }
            }, 1000);
          }

          handleMessage(data);
        } catch (e) {
          console.error("Failed to parse message:", e);
        }
      };

      wsRef.current = ws;
    } catch (e) {
      console.error("Failed to start call:", e);
      setError(e instanceof Error ? e.message : "Failed to start call");
      setCallState("error");
    }
  }, [documentId, callState, isMuted, handleMessage]);

  // End call
  const endCall = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "end_call" }));
    }

    // Cleanup
    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current);
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
    }
    if (playbackContextRef.current) {
      playbackContextRef.current.close();
    }
    if (wsRef.current) {
      wsRef.current.close();
    }

    // Clear audio queue and stop playback
    clearAudioQueue();

    wsRef.current = null;
    audioContextRef.current = null;
    playbackContextRef.current = null;
    streamRef.current = null;
    workletNodeRef.current = null;

    setCallState("ended");
  }, []);

  // Interrupt AI
  const interrupt = useCallback(() => {
    // Clear audio queue immediately when interrupting
    clearAudioQueue();

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "interrupt" }));
    }
  }, [clearAudioQueue]);

  // Mute/unmute
  const toggleMute = useCallback(() => {
    const newMuted = !isMuted;
    setIsMuted(newMuted);

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({ type: newMuted ? "mute" : "unmute" }),
      );
    }
  }, [isMuted]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      endCall();
    };
  }, [endCall]);

  // Keep-alive ping
  useEffect(() => {
    const interval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: "ping" }));
      }
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  return {
    // State
    callState,
    sessionId,
    greeting,
    transcription,
    aiTranscript,
    callDuration,
    isMuted,
    error,
    highlights,

    // Actions
    startCall,
    endCall,
    interrupt,
    toggleMute,

    // Helpers
    isInCall: () =>
      [
        "connecting",
        "connected",
        "user_speaking",
        "ai_speaking",
        "processing",
      ].includes(callState),
    formatDuration: () => {
      const mins = Math.floor(callDuration / 60);
      const secs = callDuration % 60;
      return `${mins}:${secs.toString().padStart(2, "0")}`;
    },
  };
}

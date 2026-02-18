import { create } from 'zustand';
import type { VoiceInfo, ConversationState } from '@/types';

interface VoiceState {
  // Voice settings
  selectedVoice: string;
  availableVoices: VoiceInfo[];
  
  // Recording state
  isRecording: boolean;
  isProcessing: boolean;
  audioLevel: number;
  
  // Playback state
  isPlaying: boolean;
  currentAudio: HTMLAudioElement | null;
  
  // Conversation state
  conversationState: ConversationState;
  transcription: string | null;
  lastResponse: string | null;
  
  // WebSocket state
  isConnected: boolean;
  isConnectionOpen: boolean;
  
  // Error state
  error: string | null;
  
  // Actions
  setSelectedVoice: (voice: string) => void;
  setAvailableVoices: (voices: VoiceInfo[]) => void;
  setRecording: (recording: boolean) => void;
  setProcessing: (processing: boolean) => void;
  setAudioLevel: (level: number) => void;
  setPlaying: (playing: boolean) => void;
  setCurrentAudio: (audio: HTMLAudioElement | null) => void;
  setConversationState: (state: ConversationState) => void;
  setTranscription: (text: string | null) => void;
  setLastResponse: (response: string | null) => void;
  setConnected: (connected: boolean) => void;
  setConnectionOpen: (open: boolean) => void;
  setError: (error: string | null) => void;
  stopPlayback: () => void;
  reset: () => void;
}

const initialState = {
  selectedVoice: 'alloy',
  availableVoices: [],
  isRecording: false,
  isProcessing: false,
  audioLevel: 0,
  isPlaying: false,
  currentAudio: null,
  conversationState: 'idle' as ConversationState,
  transcription: null,
  lastResponse: null,
  isConnected: false,
  isConnectionOpen: false,
  error: null,
};

export const useVoiceStore = create<VoiceState>()((set, get) => ({
  ...initialState,
  
  setSelectedVoice: (selectedVoice) => set({ selectedVoice }),
  
  setAvailableVoices: (availableVoices) => set({ availableVoices }),
  
  setRecording: (isRecording) => set({ 
    isRecording,
    conversationState: isRecording ? 'listening' : get().conversationState,
  }),
  
  setProcessing: (isProcessing) => set({ 
    isProcessing,
    conversationState: isProcessing ? 'processing' : get().conversationState,
  }),
  
  setAudioLevel: (audioLevel) => set({ audioLevel }),
  
  setPlaying: (isPlaying) => set({ 
    isPlaying,
    conversationState: isPlaying ? 'speaking' : 'idle',
  }),
  
  setCurrentAudio: (currentAudio) => set({ currentAudio }),
  
  setConversationState: (conversationState) => set({ conversationState }),
  
  setTranscription: (transcription) => set({ transcription }),
  
  setLastResponse: (lastResponse) => set({ lastResponse }),
  
  setConnected: (isConnected) => set({ isConnected }),
  
  setConnectionOpen: (isConnectionOpen) => set({ isConnectionOpen }),
  
  setError: (error) => set({ error }),
  
  stopPlayback: () => {
    const { currentAudio } = get();
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
    }
    set({
      isPlaying: false,
      currentAudio: null,
      conversationState: 'idle',
    });
  },
  
  reset: () => {
    const { currentAudio } = get();
    if (currentAudio) {
      currentAudio.pause();
    }
    set(initialState);
  },
}));

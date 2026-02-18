import { create } from 'zustand';

export type CallState = 
  | 'idle'
  | 'connecting' 
  | 'connected'
  | 'user_speaking'
  | 'ai_speaking'
  | 'processing'
  | 'ended'
  | 'error';

interface CallStoreState {
  // Call state
  callState: CallState;
  sessionId: string | null;
  documentId: string | null;
  
  // Timing
  callStartTime: number | null;
  callDuration: number;
  
  // Audio state
  isMuted: boolean;
  isAudioPlaying: boolean;
  userAudioLevel: number;
  
  // Transcriptions
  userTranscription: string | null;
  aiTranscript: string;
  
  // Greeting from AI
  greeting: string | null;
  
  // Error handling
  error: string | null;
  
  // Statistics
  questionsAsked: number;
  interruptionCount: number;
  
  // Actions
  setCallState: (state: CallState) => void;
  setSessionId: (id: string | null) => void;
  setDocumentId: (id: string | null) => void;
  startCallTimer: () => void;
  stopCallTimer: () => void;
  updateCallDuration: () => void;
  setMuted: (muted: boolean) => void;
  toggleMute: () => void;
  setAudioPlaying: (playing: boolean) => void;
  setUserAudioLevel: (level: number) => void;
  setUserTranscription: (text: string | null) => void;
  setAiTranscript: (text: string) => void;
  appendAiTranscript: (text: string) => void;
  setGreeting: (greeting: string | null) => void;
  setError: (error: string | null) => void;
  incrementQuestions: () => void;
  incrementInterruptions: () => void;
  resetCall: () => void;
}

const initialState = {
  callState: 'idle' as CallState,
  sessionId: null,
  documentId: null,
  callStartTime: null,
  callDuration: 0,
  isMuted: false,
  isAudioPlaying: false,
  userAudioLevel: 0,
  userTranscription: null,
  aiTranscript: '',
  greeting: null,
  error: null,
  questionsAsked: 0,
  interruptionCount: 0,
};

let durationInterval: NodeJS.Timeout | null = null;

export const useCallStore = create<CallStoreState>()((set, get) => ({
  ...initialState,
  
  setCallState: (callState) => set({ callState }),
  
  setSessionId: (sessionId) => set({ sessionId }),
  
  setDocumentId: (documentId) => set({ documentId }),
  
  startCallTimer: () => {
    const startTime = Date.now();
    set({ callStartTime: startTime, callDuration: 0 });
    
    // Clear any existing interval
    if (durationInterval) {
      clearInterval(durationInterval);
    }
    
    // Update duration every second
    durationInterval = setInterval(() => {
      const state = get();
      if (state.callStartTime) {
        set({ callDuration: Math.floor((Date.now() - state.callStartTime) / 1000) });
      }
    }, 1000);
  },
  
  stopCallTimer: () => {
    if (durationInterval) {
      clearInterval(durationInterval);
      durationInterval = null;
    }
  },
  
  updateCallDuration: () => {
    const state = get();
    if (state.callStartTime) {
      set({ callDuration: Math.floor((Date.now() - state.callStartTime) / 1000) });
    }
  },
  
  setMuted: (isMuted) => set({ isMuted }),
  
  toggleMute: () => set((state) => ({ isMuted: !state.isMuted })),
  
  setAudioPlaying: (isAudioPlaying) => set({ isAudioPlaying }),
  
  setUserAudioLevel: (userAudioLevel) => set({ userAudioLevel }),
  
  setUserTranscription: (userTranscription) => set({ userTranscription }),
  
  setAiTranscript: (aiTranscript) => set({ aiTranscript }),
  
  appendAiTranscript: (text) => set((state) => ({ 
    aiTranscript: state.aiTranscript + text 
  })),
  
  setGreeting: (greeting) => set({ greeting }),
  
  setError: (error) => set({ error }),
  
  incrementQuestions: () => set((state) => ({ 
    questionsAsked: state.questionsAsked + 1 
  })),
  
  incrementInterruptions: () => set((state) => ({ 
    interruptionCount: state.interruptionCount + 1 
  })),
  
  resetCall: () => {
    if (durationInterval) {
      clearInterval(durationInterval);
      durationInterval = null;
    }
    set(initialState);
  },
}));

// Helper function to format duration
export function formatCallDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

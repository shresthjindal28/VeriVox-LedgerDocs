import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { User, TokenResponse, Profile, StudyPreferences } from '@/types';

interface AuthState {
  // User data
  user: User | null;
  profile: Profile | null;
  preferences: StudyPreferences | null;
  
  // Auth tokens
  accessToken: string | null;
  refreshToken: string | null;
  
  // Status
  isAuthenticated: boolean;
  isLoading: boolean;
  isInitialized: boolean;
  error: string | null;
  
  // Actions
  setUser: (user: User | null) => void;
  setProfile: (profile: Profile | null) => void;
  setPreferences: (preferences: StudyPreferences | null) => void;
  setTokens: (tokens: TokenResponse) => void;
  clearTokens: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setInitialized: (initialized: boolean) => void;
  login: (tokens: TokenResponse, user?: User) => void;
  logout: () => void;
  reset: () => void;
}

const initialState = {
  user: null,
  profile: null,
  preferences: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: false,
  isInitialized: false,
  error: null,
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      ...initialState,
      
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      
      setProfile: (profile) => set({ profile }),
      
      setPreferences: (preferences) => set({ preferences }),
      
      setTokens: (tokens) => set({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        isAuthenticated: true,
      }),
      
      clearTokens: () => set({
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
      }),
      
      setLoading: (isLoading) => set({ isLoading }),
      
      setError: (error) => set({ error }),
      
      setInitialized: (isInitialized) => set({ isInitialized }),
      
      login: (tokens, user) => {
        // Also store in localStorage for API client
        if (typeof window !== 'undefined') {
          localStorage.setItem('access_token', tokens.access_token);
          localStorage.setItem('refresh_token', tokens.refresh_token);
        }
        const updates: Partial<AuthState> = {
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token,
          isAuthenticated: true,
          error: null,
        };
        if (user) {
          updates.user = user;
        }
        set(updates);
      },
      
      logout: () => {
        // Clear localStorage tokens
        if (typeof window !== 'undefined') {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        }
        set({
          ...initialState,
          isInitialized: true,
        });
      },
      
      reset: () => set(initialState),
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

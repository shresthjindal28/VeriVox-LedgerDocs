'use client';

import * as React from 'react';
import { useAuthStore } from '@/stores';
import { authApi, profileApi } from '@/lib/api';
import { LoadingOverlay } from '@/components/ui/loading';

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const {
    accessToken,
    refreshToken,
    isInitialized,
    setInitialized,
    setUser,
    setProfile,
    setPreferences,
    logout,
  } = useAuthStore();
  
  React.useEffect(() => {
    const initAuth = async () => {
      // Sync tokens to localStorage for API client
      if (typeof window !== 'undefined' && accessToken) {
        localStorage.setItem('access_token', accessToken);
        if (refreshToken) {
          localStorage.setItem('refresh_token', refreshToken);
        }
      }
      
      if (!accessToken) {
        setInitialized(true);
        return;
      }
      
      try {
        // Fetch current user
        const user = await authApi.getCurrentUser();
        setUser(user);
        
        // Fetch profile and preferences in parallel
        const [profile, preferences] = await Promise.all([
          profileApi.getProfile().catch(() => null),
          profileApi.getPreferences().catch(() => null),
        ]);
        
        if (profile) setProfile(profile);
        if (preferences) setPreferences(preferences);
        
      } catch (error) {
        // Token invalid, logout
        logout();
      } finally {
        setInitialized(true);
      }
    };
    
    initAuth();
  }, [accessToken, setInitialized, setUser, setProfile, setPreferences, logout]);
  
  if (!isInitialized) {
    return <LoadingOverlay message="Loading..." />;
  }
  
  return <>{children}</>;
}

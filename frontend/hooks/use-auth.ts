'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { authApi, profileApi } from '@/lib/api';
import { useAuthStore } from '@/stores';
import type { LoginRequest, RegisterRequest, ProfileUpdate, StudyPreferences } from '@/types';

// Query keys
export const authKeys = {
  all: ['auth'] as const,
  user: () => [...authKeys.all, 'user'] as const,
  profile: () => [...authKeys.all, 'profile'] as const,
  fullProfile: () => [...authKeys.all, 'fullProfile'] as const,
  preferences: () => [...authKeys.all, 'preferences'] as const,
};

// ============================================================================
// Auth Hooks
// ============================================================================

export function useCurrentUser() {
  const { isAuthenticated, setUser, setLoading, setInitialized } = useAuthStore();
  
  return useQuery({
    queryKey: authKeys.user(),
    queryFn: async () => {
      const data = await authApi.getCurrentUser();
      setUser(data);
      return data;
    },
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  const { login, setLoading, setError } = useAuthStore();
  
  return useMutation({
    mutationFn: (data: LoginRequest) => authApi.login(data),
    onMutate: () => {
      setLoading(true);
      setError(null);
    },
    onSuccess: (data) => {
      login(data);
      queryClient.invalidateQueries({ queryKey: authKeys.all });
    },
    onError: (error: Error) => {
      setError(error.message);
    },
    onSettled: () => {
      setLoading(false);
    },
  });
}

export function useRegister() {
  const { setLoading, setError } = useAuthStore();
  
  return useMutation({
    mutationFn: (data: RegisterRequest) => authApi.register(data),
    onMutate: () => {
      setLoading(true);
      setError(null);
    },
    onError: (error: Error) => {
      setError(error.message);
    },
    onSettled: () => {
      setLoading(false);
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  const { logout } = useAuthStore();
  
  return useMutation({
    mutationFn: () => authApi.logout(),
    onSuccess: () => {
      logout();
      queryClient.clear();
    },
    onError: () => {
      // Still logout on error
      logout();
      queryClient.clear();
    },
  });
}

export function useRefreshToken() {
  const { refreshToken, setTokens, logout } = useAuthStore();
  
  return useMutation({
    mutationFn: () => {
      if (!refreshToken) throw new Error('No refresh token');
      return authApi.refreshToken(refreshToken);
    },
    onSuccess: (data) => {
      setTokens(data);
    },
    onError: () => {
      logout();
    },
  });
}

export function useResetPassword() {
  return useMutation({
    mutationFn: (email: string) => authApi.resetPassword(email),
  });
}

export function useUpdatePassword() {
  return useMutation({
    mutationFn: (password: string) => authApi.updatePassword(password),
  });
}

// ============================================================================
// Profile Hooks
// ============================================================================

export function useProfile() {
  const { setProfile, isAuthenticated } = useAuthStore();
  
  return useQuery({
    queryKey: authKeys.profile(),
    queryFn: async () => {
      const data = await profileApi.getProfile();
      setProfile(data);
      return data;
    },
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000,
  });
}

export function useFullProfile() {
  const { isAuthenticated } = useAuthStore();
  
  return useQuery({
    queryKey: authKeys.fullProfile(),
    queryFn: () => profileApi.getFullProfile(),
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000,
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  const { setProfile } = useAuthStore();
  
  return useMutation({
    mutationFn: (data: ProfileUpdate) => profileApi.updateProfile(data),
    onSuccess: (data) => {
      setProfile(data);
      queryClient.invalidateQueries({ queryKey: authKeys.profile() });
      queryClient.invalidateQueries({ queryKey: authKeys.fullProfile() });
    },
  });
}

export function usePreferences() {
  const { setPreferences, isAuthenticated } = useAuthStore();
  
  return useQuery({
    queryKey: authKeys.preferences(),
    queryFn: async () => {
      const data = await profileApi.getPreferences();
      setPreferences(data);
      return data;
    },
    enabled: isAuthenticated,
    staleTime: 10 * 60 * 1000,
  });
}

export function useUpdatePreferences() {
  const queryClient = useQueryClient();
  const { setPreferences } = useAuthStore();
  
  return useMutation({
    mutationFn: (data: Partial<StudyPreferences>) => profileApi.updatePreferences(data),
    onSuccess: (data) => {
      setPreferences(data);
      queryClient.invalidateQueries({ queryKey: authKeys.preferences() });
    },
  });
}

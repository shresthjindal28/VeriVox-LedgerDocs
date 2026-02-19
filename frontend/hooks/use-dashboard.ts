'use client';

import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '@/lib/api';
import type { DashboardStats, RecentSessionsResponse, BlockchainProofsResponse } from '@/types';

// Query keys
export const dashboardKeys = {
  all: ['dashboard'] as const,
  stats: () => [...dashboardKeys.all, 'stats'] as const,
  documents: (page?: number) => [...dashboardKeys.all, 'documents', { page }] as const,
  sessions: () => [...dashboardKeys.all, 'sessions'] as const,
  sessionsList: (limit?: number, offset?: number) => 
    [...dashboardKeys.sessions(), 'list', { limit, offset }] as const,
  proofs: () => [...dashboardKeys.all, 'proofs'] as const,
  proofsList: (limit?: number, offset?: number, proofType?: string) => 
    [...dashboardKeys.proofs(), 'list', { limit, offset, proofType }] as const,
};

// ============================================================================
// Dashboard Hooks
// ============================================================================

export function useDashboardStats() {
  return useQuery({
    queryKey: dashboardKeys.stats(),
    queryFn: () => dashboardApi.getStats(),
    staleTime: 30000, // 30s per plan
    refetchOnWindowFocus: false,
  });
}

export function useDashboardDocuments(page: number = 1, limit: number = 50) {
  return useQuery({
    queryKey: dashboardKeys.documents(page),
    queryFn: () => dashboardApi.getDocuments(page, limit),
    staleTime: 60 * 1000,
  });
}

export function useRecentSessions(limit: number = 20, offset: number = 0) {
  return useQuery({
    queryKey: dashboardKeys.sessionsList(limit, offset),
    queryFn: () => dashboardApi.getRecentSessions(limit, offset),
    staleTime: 60 * 1000, // 1 minute
  });
}

export function useBlockchainProofs(
  limit: number = 50,
  offset: number = 0,
  proofType?: string
) {
  return useQuery({
    queryKey: dashboardKeys.proofsList(limit, offset, proofType),
    queryFn: () => dashboardApi.getBlockchainProofs(limit, offset, proofType),
    staleTime: 60 * 1000, // 1 minute
  });
}

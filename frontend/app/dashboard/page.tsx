'use client';

import * as React from 'react';
import { StatsCards, DocumentsTable, RecentCalls, RecentExtractions, BlockchainProofCard } from '@/components/dashboard';
import { useDashboardStats, useDashboardDocuments, useRecentSessions, useRecentExtractions, useBlockchainProofs, useProfile } from '@/hooks';
import { AppLayout } from '@/components/layout';
import { Bell, Search } from 'lucide-react';
import { useAuthStore } from '@/stores';
import Image from 'next/image';
import Link from 'next/link';

export default function DashboardPage() {
  const { user, profile } = useAuthStore();
  const { data: profileData } = useProfile();
  const { data: stats, isLoading: statsLoading, error: statsError } = useDashboardStats();
  const { data: docsData, isLoading: documentsLoading, error: documentsError } = useDashboardDocuments(1, 50);
  const { data: sessionsData, isLoading: sessionsLoading, error: sessionsError } = useRecentSessions(20, 0);
  const { data: proofsData, isLoading: proofsLoading, error: proofsError } = useBlockchainProofs(50, 0);
  const { data: extractionsData, isLoading: extractionsLoading, error: extractionsError } = useRecentExtractions(20, 0);

  const currentProfile = profileData || profile;
  const avatarUrl = currentProfile?.avatar_url;
  const userName = currentProfile?.display_name || user?.display_name || 'User';
  const initials = userName[0]?.toUpperCase() || 'U';

  return (
    <AppLayout>
      <div className="min-h-screen text-white p-8">
        {/* Top Header */}
        <div className="flex items-center justify-between mb-10">
          <h1 className="text-2xl font-semibold text-white">Dashboard</h1>
          <div className="flex items-center gap-4">
            <button className="text-brand-100/60 hover:text-white transition-colors">
              <Search className="w-5 h-5" />
            </button>
            <button className="text-brand-100/60 hover:text-white transition-colors relative">
              <Bell className="w-5 h-5" />
              <div className="absolute top-0 right-0 w-2 h-2 bg-brand-500 rounded-full border border-black"></div>
            </button>
            <Link href="/profile" className="block">
              <div className="h-8 w-8 rounded-full overflow-hidden border border-brand-500/30 relative cursor-pointer hover:border-brand-500/60 transition-colors">
                {avatarUrl ? (
                  <Image
                    src={avatarUrl}
                    alt={userName}
                    fill
                    className="object-cover"
                    unoptimized
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-xs font-bold text-black bg-gradient-to-br from-brand-400 to-brand-600">
                    {initials}
                  </div>
                )}
              </div>
            </Link>
          </div>
        </div>

        <div className="max-w-7xl mx-auto space-y-8">
          {/* Greeting */}
          <div>
            <h2 className="text-3xl font-medium text-white">
              Welcome back, <span className="text-white">{userName.split(' ')[0]}</span>
            </h2>
          </div>

          {/* Stats Cards */}
          <StatsCards
            stats={stats ? {
              ...stats,
              total_documents: docsData?.pagination?.total ?? stats.total_documents,
              active_sessions: sessionsData?.total ?? stats.active_sessions,
              total_proofs: proofsData?.total ||
                (docsData?.documents?.filter(d => d.blockchain_status === 'anchored' || d.blockchain_status === 'verified').length ?? stats.total_proofs),
            } : undefined}
            isLoading={statsLoading}
            error={statsError ?? undefined}
          />

          {/* Main Content Grid */}
          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Top Row: Documents & Proofs */}
            <div className="lg:col-span-2 space-y-6">
              <DocumentsTable
                documents={docsData?.documents}
                pagination={docsData?.pagination}
                isLoading={documentsLoading}
                error={documentsError ?? undefined}
              />
            </div>

            <div className="space-y-6">
              <BlockchainProofCard
                proofs={proofsData?.proofs}
                anchoredDocuments={docsData?.documents}
                isLoading={proofsLoading}
                error={proofsError ?? undefined}
              />
            </div>

            {/* Bottom Row: Recent Voice Sessions */}
            <div className="lg:col-span-3">
              <RecentCalls
                sessions={sessionsData?.sessions}
                isLoading={sessionsLoading}
                error={sessionsError ?? undefined}
              />
            </div>

            {/* Recent RAG Extractions (fetched details for Total Extractions) */}
            <div className="lg:col-span-3">
              <RecentExtractions
                extractions={extractionsData?.extractions}
                isLoading={extractionsLoading}
                error={extractionsError ?? undefined}
              />
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

'use client';

import * as React from 'react';
import { StatsCards, DocumentsTable, RecentCalls, BlockchainProofCard } from '@/components/dashboard';
import { useDashboardStats, useDashboardDocuments, useRecentSessions, useBlockchainProofs } from '@/hooks';
import { AppLayout } from '@/components/layout';
import { Bell, Search } from 'lucide-react';
import { useAuthStore } from '@/stores';
import Image from 'next/image';

export default function DashboardPage() {
  const { user } = useAuthStore();
  const { data: stats, isLoading: statsLoading, error: statsError } = useDashboardStats();
  const { data: docsData, isLoading: documentsLoading, error: documentsError } = useDashboardDocuments(1, 50);
  const { data: sessionsData, isLoading: sessionsLoading, error: sessionsError } = useRecentSessions(20, 0);
  const { data: proofsData, isLoading: proofsLoading, error: proofsError } = useBlockchainProofs(50, 0);

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
            <div className="h-8 w-8 rounded-full bg-brand-500/20 overflow-hidden border border-brand-500/30">
              {/* Placeholder Avatar */}
              <Image
                src="/avatar-placeholder.png"
                alt="User"
                width={32}
                height={32}
                className="object-cover"
                onError={(e) => {
                  // Fallback to initial if image fails
                  e.currentTarget.style.display = 'none';
                }}
              />
              <div className="w-full h-full flex items-center justify-center text-xs font-bold text-brand-500 bg-brand-900">
                {user?.display_name ? user.display_name[0].toUpperCase() : 'M'}
              </div>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto space-y-8">
          {/* Greeting */}
          <div>
            <h2 className="text-3xl font-medium text-white">
              Welcome back, <span className="text-white">{user?.display_name?.split(' ')[0] || 'Matthew'}</span>
            </h2>
          </div>

          {/* Stats Cards */}
          <StatsCards stats={stats} isLoading={statsLoading} error={statsError ?? undefined} />

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column: Documents */}
            <div className="lg:col-span-2 space-y-6">
              <DocumentsTable
                documents={docsData?.documents}
                pagination={docsData?.pagination}
                isLoading={documentsLoading}
                error={documentsError ?? undefined}
              />

              {/* Second Table for Mobile/Other view if needed, or just let the main one fill space. 
                         Screenshot shows two "Your Documents" tables. I'll stick to one huge one for now 
                         or duplicate if user really wants exact layout. 
                         Actually, let's keep it clean with one main Documents table. 
                     */}
            </div>

            {/* Right Column: Sessions & Proofs */}
            <div className="space-y-6">
              <RecentCalls
                sessions={sessionsData?.sessions}
                isLoading={sessionsLoading}
                error={sessionsError ?? undefined}
              />
              <BlockchainProofCard
                proofs={proofsData?.proofs}
                isLoading={proofsLoading}
                error={proofsError ?? undefined}
              />
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

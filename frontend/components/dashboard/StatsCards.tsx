'use client';

import { Layers, Activity, Box, Shield } from 'lucide-react';
import type { DashboardStats } from '@/types';

interface StatsCardsProps {
  stats?: DashboardStats;
  isLoading?: boolean;
  error?: Error | null;
}

export function StatsCards({ stats, isLoading, error }: StatsCardsProps) {
  if (isLoading) {
    return (
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-32 rounded-xl bg-brand-900/10 border border-brand-500/10 animate-pulse" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-destructive/20 bg-destructive/5 p-4 text-destructive text-sm">
        {error.message}
      </div>
    );
  }

  const total_documents = stats?.total_documents ?? 0;
  const active_sessions = stats?.active_sessions ?? 0;
  const total_extractions = stats?.total_extractions ?? 0;
  const total_proofs = stats?.total_proofs ?? 0;

  const cards = [
    { title: 'Total Documents', value: total_documents, icon: Layers, sub: 'Uploaded' },
    { title: 'Active Voice Sessions', value: active_sessions, icon: Activity, sub: 'Sessions' },
    { title: 'Total Extractions', value: total_extractions, icon: Box, sub: 'RAG extractions' },
    { title: 'Blockchain Proofs', value: total_proofs, icon: Shield, sub: 'Anchored' },
  ];

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
      {cards.map(({ title, value, icon: Icon, sub }) => (
        <div
          key={title}
          className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-[#0c1a12] to-[#050a07] border border-brand-500/10 hover:border-brand-500/20 transition-all group"
        >
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <Icon className="w-24 h-24 text-brand-500" />
          </div>
          <div className="p-6 relative z-10">
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-gradient-to-br from-brand-500/20 to-transparent border border-brand-500/20">
                <Icon className="w-8 h-8 text-brand-400" />
              </div>
              <div>
                <h3 className="text-brand-100/60 font-medium text-sm">{title}</h3>
                <div className="text-4xl font-bold text-white mt-1">{value}</div>
                <p className="text-xs text-brand-100/40 mt-1">{sub}</p>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

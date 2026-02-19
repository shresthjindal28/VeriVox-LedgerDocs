'use client';

import { Skeleton } from '@/components/ui';
import { formatDuration } from '@/lib/utils';
import { ArrowRight, ShieldCheck, ShieldAlert, Clock } from 'lucide-react';
import Link from 'next/link';
import type { VoiceSession } from '@/types';

interface RecentCallsProps {
  sessions?: VoiceSession[];
  isLoading?: boolean;
  error?: Error | null;
}

function VerificationBadge({
  status,
}: {
  status: 'verified' | 'pending' | 'failed';
}) {
  if (status === 'verified') {
    return (
      <div className="flex items-center gap-1 text-xs text-emerald-400 font-medium">
        <ShieldCheck className="h-3 w-3" /> Verified
      </div>
    );
  }
  if (status === 'pending') {
    return (
      <div className="flex items-center gap-1 text-xs text-amber-400 font-medium">
        <Clock className="h-3 w-3" /> Pending
      </div>
    );
  }
  return (
    <div className="flex items-center gap-1 text-xs text-red-400 font-medium">
      <ShieldAlert className="h-3 w-3" /> Failed
    </div>
  );
}

export function RecentCalls({
  sessions = [],
  isLoading,
  error,
}: RecentCallsProps) {
  if (isLoading) {
    return (
      <div className="rounded-2xl border border-brand-500/10 bg-[#080c0a] overflow-hidden flex flex-col h-full">
        <div className="p-6 border-b border-brand-500/10">
          <div className="h-6 w-40 bg-white/5 rounded animate-pulse" />
        </div>
        <div className="p-6 space-y-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-12 w-full bg-white/5" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-brand-500/10 bg-[#080c0a] p-6">
        <p className="text-destructive text-sm">{error.message}</p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-brand-500/10 bg-[#080c0a] overflow-hidden flex flex-col h-full">
      <div className="flex items-center justify-between p-6 border-b border-brand-500/10 bg-white/2">
        <h2 className="text-lg font-semibold text-white">Recent Voice Sessions</h2>
        <Link
          href="/voice-sessions"
          className="text-xs text-brand-100/40 hover:text-brand-500 flex items-center gap-1 transition-colors"
        >
          See all <ArrowRight className="h-3 w-3" />
        </Link>
      </div>

      <div className="overflow-x-auto flex-1">
        <table className="w-full text-left text-sm">
          <thead className="text-xs text-brand-100/40 uppercase bg-white/2">
            <tr>
              <th className="px-5 py-4 font-medium">Session</th>
              <th className="px-5 py-4 font-medium">Document</th>
              <th className="px-5 py-4 font-medium">Duration</th>
              <th className="px-5 py-4 font-medium">Verification</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-brand-500/5">
            {sessions.length > 0 ? (
              sessions.map((session) => (
                <tr
                  key={session.session_id}
                  className="hover:bg-brand-500/5 transition-colors"
                >
                  <td className="px-5 py-4 font-mono text-brand-100/80 text-xs">
                    {session.session_id.slice(0, 8)}...
                  </td>
                  <td className="px-5 py-4 text-brand-100/80 truncate max-w-[120px]">
                    {session.document_name ?? '—'}
                  </td>
                  <td className="px-5 py-4 text-brand-100/60 font-mono text-xs">
                    {formatDuration(session.duration_seconds ?? 0)}
                  </td>
                  <td className="px-5 py-4">
                    <VerificationBadge
                      status={session.verification_status ?? 'pending'}
                    />
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td
                  colSpan={4}
                  className="px-5 py-8 text-center text-brand-100/40"
                >
                  No recent voice sessions.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="p-4 border-t border-brand-500/10 bg-white/1">
        <Link
          href="/proofs"
          className="text-xs text-brand-100/30 hover:text-brand-500 transition-colors block text-right"
        >
          View All Proofs
        </Link>
      </div>
    </div>
  );
}

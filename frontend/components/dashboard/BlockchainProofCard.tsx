'use client';

import { Skeleton } from '@/components/ui';
import { formatPartialHash } from '@/lib/utils';
import { ShieldCheck, ShieldAlert, Clock, ArrowRight } from 'lucide-react';
import type { BlockchainProof } from '@/types';
import Link from 'next/link';

interface BlockchainProofCardProps {
  proofs?: BlockchainProof[];
  isLoading?: boolean;
  error?: Error | null;
}

function ProofStatusBadge({ verified }: { verified: boolean }) {
  if (verified) {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 text-xs font-medium">
        <ShieldCheck className="h-3.5 w-3.5" />
        Verified
      </div>
    );
  }
  return (
    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-500/20 border border-amber-500/30 text-amber-400 text-xs font-medium">
      <Clock className="h-3.5 w-3.5" />
      Pending
    </div>
  );
}

export function BlockchainProofCard({
  proofs = [],
  isLoading,
  error,
}: BlockchainProofCardProps) {
  if (isLoading) {
    return (
      <Skeleton className="h-48 w-full bg-white/5 rounded-2xl border border-brand-500/10" />
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
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-[#0c1a12] to-[#050a07] border border-brand-500/10 p-6 group hover:border-brand-500/20 transition-all">
      <div className="absolute inset-0 bg-[url('/noise.png')] opacity-5 mix-blend-overlay pointer-events-none" />
      <div className="absolute -top-10 -right-10 w-32 h-32 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Blockchain Proofs</h3>
          <Link
            href="/proofs"
            className="text-xs text-brand-100/40 hover:text-brand-500 flex items-center gap-1 transition-colors"
          >
            View all <ArrowRight className="h-3 w-3" />
          </Link>
        </div>

        {proofs.length > 0 ? (
          <div className="space-y-3">
            {proofs.slice(0, 5).map((proof) => (
              <div
                key={proof.proof_id}
                className="flex items-center justify-between py-2 border-b border-brand-500/10 last:border-0"
              >
                <div className="min-w-0 flex-1">
                  <div className="font-mono text-xs text-brand-100/80 capitalize">
                    {proof.proof_type}
                  </div>
                  <div className="text-xs text-brand-100/50 font-mono mt-0.5">
                    {formatPartialHash(proof.hash_value)}
                    {proof.tx_hash && (
                      <span className="ml-2">tx {formatPartialHash(proof.tx_hash)}</span>
                    )}
                  </div>
                </div>
                <ProofStatusBadge verified={proof.verified} />
              </div>
            ))}
            {proofs.length > 5 && (
              <p className="text-xs text-brand-100/40 pt-1">
                +{proofs.length - 5} more
              </p>
            )}
          </div>
        ) : (
          <div className="py-8 text-center text-brand-100/40 text-sm">
            No blockchain proofs yet.
          </div>
        )}
      </div>
    </div>
  );
}

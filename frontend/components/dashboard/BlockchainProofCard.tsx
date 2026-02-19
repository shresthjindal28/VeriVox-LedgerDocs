'use client';

import * as React from 'react';
import { Skeleton } from '@/components/ui';
import { formatPartialHash, formatDate } from '@/lib/utils';
import { getChainName, getExplorerUrl } from '@/lib/blockchain';
import { ShieldCheck, Clock, ArrowRight, ExternalLink, Copy, Check } from 'lucide-react';
import type { BlockchainProof, DashboardDocument } from '@/types';
import Link from 'next/link';

interface BlockchainProofCardProps {
  proofs?: BlockchainProof[];
  anchoredDocuments?: DashboardDocument[];
  isLoading?: boolean;
  error?: Error | null;
}

/** Derive proof-like entries from anchored documents when proofs list is empty */
function documentsToProofs(docs: DashboardDocument[]): BlockchainProof[] {
  return docs
    .filter((d) => (d.blockchain_status === 'anchored' || d.blockchain_status === 'verified') && d.blockchain_hash)
    .map((d, i) => ({
      proof_id: `doc-${d.id}-${i}`,
      proof_type: 'document' as const,
      hash_value: d.blockchain_hash!,
      document_id: d.id,
      tx_hash: d.tx_hash,
      chain_id: d.chain_id,
      verified: d.blockchain_status === 'verified',
      timestamp: d.upload_date,
      metadata: { name: d.name },
    }));
}

function CopyHashButton({ hash }: { hash: string }) {
  const [copied, setCopied] = React.useState(false);
  const copy = () => {
    navigator.clipboard.writeText(hash);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <button
      type="button"
      onClick={copy}
      className="p-0.5 rounded hover:bg-white/10 text-brand-100/50 hover:text-brand-400 transition-colors"
      title="Copy hash"
    >
      {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
    </button>
  );
}

function ProofRow({ proof }: { proof: BlockchainProof }) {
  const explorerUrl = getExplorerUrl(proof.tx_hash, proof.chain_id);
  const chainName = getChainName(proof.chain_id);

  return (
    <div className="py-3 border-b border-brand-500/10 last:border-0 space-y-2">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="font-medium text-sm text-white capitalize">
              {proof.proof_type.replace('_', ' ')}
            </span>
            <ProofStatusBadge verified={proof.verified} />
          </div>
          <div className="flex items-center gap-1.5 mt-1 text-xs text-brand-100/60 font-mono">
            <span title={proof.hash_value}>{formatPartialHash(proof.hash_value)}</span>
            <CopyHashButton hash={proof.hash_value} />
          </div>
          {proof.tx_hash && (
            <div className="flex items-center gap-1.5 mt-1 text-xs text-brand-100/50">
              <span>tx {formatPartialHash(proof.tx_hash)}</span>
              {explorerUrl && (
                <a
                  href={explorerUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-0.5 text-brand-500 hover:text-brand-400 transition-colors"
                >
                  View <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </div>
          )}
          {(chainName !== 'Unknown' || proof.block_number) && (
            <div className="flex items-center gap-3 mt-1 text-[10px] text-brand-100/40">
              {chainName !== 'Unknown' && <span>{chainName}</span>}
              {proof.block_number != null && (
                <span>Block #{proof.block_number}</span>
              )}
            </div>
          )}
          {proof.timestamp && (
            <p className="text-[10px] text-brand-100/40 mt-1">
              {formatDate(proof.timestamp)}
            </p>
          )}
        </div>
        {proof.document_id && (
          <Link
            href={`/documents/${proof.document_id}`}
            className="text-[10px] text-brand-500 hover:text-brand-400 whitespace-nowrap"
          >
            View doc →
          </Link>
        )}
      </div>
    </div>
  );
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
  anchoredDocuments = [],
  isLoading,
  error,
}: BlockchainProofCardProps) {
  const displayProofs = proofs.length > 0 ? proofs : documentsToProofs(anchoredDocuments);
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

        {displayProofs.length > 0 ? (
          <div className="space-y-3">
            {displayProofs.slice(0, 5).map((proof) => (
              <ProofRow key={proof.proof_id} proof={proof} />
            ))}
            {displayProofs.length > 5 && (
              <p className="text-xs text-brand-100/40 pt-1">
                +{displayProofs.length - 5} more
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

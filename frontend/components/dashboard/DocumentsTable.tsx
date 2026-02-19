'use client';

import * as React from 'react';
import { Skeleton } from '@/components/ui';
import { formatDate, formatPartialHash } from '@/lib/utils';
import { getExplorerUrl } from '@/lib/blockchain';
import { FileText, ArrowRight, ShieldCheck, Clock, ShieldAlert, ExternalLink, Copy, Check } from 'lucide-react';
import Link from 'next/link';
import type { DashboardDocument } from '@/types';

interface DocumentsTableProps {
  documents?: DashboardDocument[];
  pagination?: { page: number; limit: number; total: number };
  isLoading?: boolean;
  error?: Error | null;
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
      title="Copy full hash"
    >
      {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
    </button>
  );
}

function ExplorerLink({ txHash, chainId }: { txHash: string; chainId: number }) {
  const url = getExplorerUrl(txHash, chainId);
  if (!url) return null;
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="p-0.5 rounded hover:bg-white/10 text-brand-100/50 hover:text-brand-400 transition-colors"
      title="View on block explorer"
    >
      <ExternalLink className="h-3 w-3" />
    </a>
  );
}

function StatusBadge({
  status,
}: {
  status: 'verified' | 'pending' | 'failed' | 'anchored';
}) {
  if (status === 'verified') {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 text-xs font-medium">
        <ShieldCheck className="h-3 w-3" />
        <span>Verified</span>
      </div>
    );
  }
  if (status === 'anchored') {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-teal-500/20 border border-teal-500/30 text-teal-400 text-xs font-medium">
        <ShieldCheck className="h-3 w-3" />
        <span>Anchored</span>
      </div>
    );
  }
  if (status === 'pending') {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-500/20 border border-amber-500/30 text-amber-400 text-xs font-medium">
        <Clock className="h-3 w-3" />
        <span>Pending</span>
      </div>
    );
  }
  return (
    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-500/20 border border-red-500/30 text-red-400 text-xs font-medium">
      <ShieldAlert className="h-3 w-3" />
      <span>Failed</span>
    </div>
  );
}

export function DocumentsTable({
  documents = [],
  pagination,
  isLoading,
  error,
}: DocumentsTableProps) {
  if (isLoading) {
    return (
      <div className="rounded-2xl border border-brand-500/10 bg-[#080c0a] overflow-hidden">
        <div className="p-6 border-b border-brand-500/10">
          <div className="h-6 w-32 bg-white/5 rounded animate-pulse" />
        </div>
        <div className="p-6 space-y-4">
          {[1, 2, 3, 4].map((i) => (
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
    <div className="rounded-2xl border border-brand-500/10 bg-[#080c0a] overflow-hidden">
      <div className="flex items-center justify-between p-6 border-b border-brand-500/10 bg-white/2">
        <h2 className="text-lg font-semibold text-white">Your Documents</h2>
        <Link
          href="/documents"
          className="text-xs text-brand-100/40 hover:text-brand-500 flex items-center gap-1 transition-colors"
        >
          See all <ArrowRight className="h-3 w-3" />
        </Link>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-xs text-brand-100/40 uppercase bg-white/2">
            <tr>
              <th className="px-6 py-4 font-medium">Name</th>
              <th className="px-6 py-4 font-medium">Upload Date</th>
              <th className="px-6 py-4 font-medium">Pages</th>
              <th className="px-6 py-4 font-medium">Blockchain</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-brand-500/5">
            {documents.length > 0 ? (
              documents.map((doc) => (
                <tr
                  key={doc.id}
                  className="hover:bg-brand-500/5 transition-colors group"
                >
                  <td className="px-6 py-4">
                    <Link
                      href={`/documents/${doc.id}`}
                      className="flex items-center gap-3"
                    >
                      <div className="flex h-8 w-8 items-center justify-center rounded bg-white/10 text-brand-100 group-hover:text-brand-500 group-hover:bg-brand-500/20 transition-all">
                        <FileText className="h-4 w-4" />
                      </div>
                      <span className="font-medium text-brand-100/90 group-hover:text-white transition-colors">
                        {doc.name}
                      </span>
                    </Link>
                  </td>
                  <td className="px-6 py-4 text-brand-100/60">
                    {formatDate(doc.upload_date)}
                  </td>
                  <td className="px-6 py-4 text-brand-100/60">
                    {doc.pages ?? 0}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-col gap-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <StatusBadge status={doc.blockchain_status} />
                        {doc.blockchain_hash && (
                          <div className="flex items-center gap-1.5">
                            <code
                              className="font-mono text-xs text-brand-100/50"
                              title={doc.blockchain_hash}
                            >
                              {formatPartialHash(doc.blockchain_hash)}
                            </code>
                            <CopyHashButton hash={doc.blockchain_hash} />
                            {doc.tx_hash && doc.chain_id && (
                              <ExplorerLink txHash={doc.tx_hash} chainId={doc.chain_id} />
                            )}
                          </div>
                        )}
                      </div>
                      {(doc.blockchain_status === 'anchored' || doc.blockchain_status === 'verified') && doc.id && (
                        <Link
                          href={`/documents/${doc.id}`}
                          className="text-[10px] text-brand-500 hover:text-brand-400 transition-colors"
                        >
                          View full proof →
                        </Link>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td
                  colSpan={4}
                  className="px-6 py-8 text-center text-brand-100/40"
                >
                  No documents found. Upload one to get started.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

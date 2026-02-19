'use client';

import { Skeleton } from '@/components/ui';
import { formatDate } from '@/lib/utils';
import { ArrowRight, Box } from 'lucide-react';
import Link from 'next/link';
import type { RAGExtraction } from '@/types';

interface RecentExtractionsProps {
  extractions?: RAGExtraction[];
  isLoading?: boolean;
  error?: Error | null;
}

export function RecentExtractions({
  extractions = [],
  isLoading,
  error,
}: RecentExtractionsProps) {
  if (isLoading) {
    return (
      <div className="rounded-2xl border border-brand-500/10 bg-[#080c0a] overflow-hidden flex flex-col h-full">
        <div className="p-6 border-b border-brand-500/10">
          <div className="h-6 w-44 bg-white/5 rounded animate-pulse" />
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
        <h2 className="text-lg font-semibold text-white">Recent RAG Extractions</h2>
        <span className="text-xs text-brand-100/40 flex items-center gap-1">
          <Box className="h-3.5 w-3.5" />
          Total Extractions
        </span>
      </div>

      <div className="overflow-x-auto flex-1">
        <table className="w-full text-left text-sm">
          <thead className="text-xs text-brand-100/40 uppercase bg-white/2">
            <tr>
              <th className="px-5 py-4 font-medium">Query</th>
              <th className="px-5 py-4 font-medium">Document</th>
              <th className="px-5 py-4 font-medium">Items</th>
              <th className="px-5 py-4 font-medium">Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-brand-500/5">
            {extractions.length > 0 ? (
              extractions.map((ext) => (
                <tr
                  key={ext.id}
                  className="hover:bg-brand-500/5 transition-colors"
                >
                  <td className="px-5 py-4 text-brand-100/90 max-w-[220px]" title={ext.query}>
                    <span className="line-clamp-2">{ext.query}</span>
                  </td>
                  <td className="px-5 py-4 text-brand-100/80 truncate max-w-[140px]">
                    <Link
                      href={`/documents/${ext.document_id}`}
                      className="hover:text-brand-500 transition-colors"
                    >
                      {ext.document_name ?? '—'}
                    </Link>
                  </td>
                  <td className="px-5 py-4 text-brand-100/60 font-mono text-xs">
                    {ext.item_count}
                  </td>
                  <td className="px-5 py-4 text-brand-100/60 text-xs">
                    {formatDate(ext.created_at)}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td
                  colSpan={4}
                  className="px-5 py-8 text-center text-brand-100/40"
                >
                  No RAG extractions yet. Use &quot;list all...&quot; or exhaustive extraction on a document.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

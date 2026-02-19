'use client';

import * as React from 'react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import {
  Shield,
  CheckCircle,
  XCircle,
  Clock,
  ExternalLink,
  FileCheck,
  Link as LinkIcon,
  Loader2,
  ChevronDown,
  ChevronUp,
  Fingerprint
} from 'lucide-react';
import { useAuthStore } from '@/stores';
import { motion, AnimatePresence } from 'framer-motion';

interface BlockchainProof {
  proof_type: string;
  hash_value: string;
  timestamp: string;
  tx_hash?: string;
  block_number?: number;
  chain_id?: number;
  verified: boolean;
  metadata?: Record<string, unknown>;
}

interface VerificationPanelProps {
  documentId: string;
  className?: string;
}

// Chain ID to name mapping
const CHAIN_NAMES: Record<number, string> = {
  1: 'Ethereum Mainnet',
  137: 'Polygon Mainnet',
  80001: 'Polygon Mumbai',
  11155111: 'Sepolia Testnet',
  5: 'Goerli Testnet',
};

// Chain ID to explorer URL
const CHAIN_EXPLORERS: Record<number, string> = {
  1: 'https://etherscan.io/tx/',
  137: 'https://polygonscan.com/tx/',
  80001: 'https://mumbai.polygonscan.com/tx/',
  11155111: 'https://sepolia.etherscan.io/tx/',
  5: 'https://goerli.etherscan.io/tx/',
};

export function VerificationPanel({ documentId, className }: VerificationPanelProps) {
  const [proofs, setProofs] = React.useState<BlockchainProof[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [isExpanded, setIsExpanded] = React.useState(false);
  const { accessToken } = useAuthStore();

  const fetchProofs = React.useCallback(async () => {
    if (!documentId || !accessToken) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'}/api/verify/document/${documentId}/proofs`,
        {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch proofs');
      }

      const data = await response.json();
      setProofs(data.proofs || []);
    } catch (err) {
      setError('Unable to load verification status');
      console.error('Verification fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [documentId, accessToken]);

  React.useEffect(() => {
    fetchProofs();
  }, [fetchProofs]);

  const documentProof = proofs.find(p => p.proof_type === 'document');
  const hasBlockchainVerification = documentProof?.tx_hash;

  const formatHash = (hash: string, length = 8) => {
    if (!hash) return '';
    return `${hash.slice(0, length)}...${hash.slice(-length)}`;
  };

  const formatDate = (timestamp: string) => {
    if (!timestamp) return '';
    return new Date(timestamp).toLocaleString();
  };

  const getExplorerUrl = (proof: BlockchainProof) => {
    if (!proof.tx_hash || !proof.chain_id) return null;
    const baseUrl = CHAIN_EXPLORERS[proof.chain_id];
    return baseUrl ? `${baseUrl}${proof.tx_hash}` : null;
  };

  const getChainName = (chainId?: number) => {
    if (!chainId) return 'Unknown';
    return CHAIN_NAMES[chainId] || `Chain ${chainId}`;
  };

  return (
    <div className={cn("overflow-hidden rounded-xl border border-white/5 bg-white/5 backdrop-blur-md", className)}>
      {/* Header */}
      <div
        className="flex items-center justify-between p-4 cursor-pointer hover:bg-white/5 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <div className={cn(
            "p-2 rounded-lg ring-1 ring-inset shadow-lg",
            hasBlockchainVerification
              ? "bg-brand-500/20 text-brand-400 ring-brand-500/30"
              : "bg-amber-500/20 text-amber-400 ring-amber-500/30"
          )}>
            <Shield className="h-5 w-5" />
          </div>
          <div>
            <h3 className="font-medium text-white/90">Document Integrity</h3>
            <p className="text-xs text-white/50">
              {hasBlockchainVerification
                ? 'Blockchain verified immutable record'
                : 'Hash recorded locally'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin text-brand-500" />
          ) : hasBlockchainVerification ? (
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-brand-500/10 border border-brand-500/20">
              <CheckCircle className="h-3.5 w-3.5 text-brand-400" />
              <span className="text-[10px] font-medium text-brand-300">Verified</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-brand-500/10 border border-brand-500/20">
              <FileCheck className="h-3.5 w-3.5 text-brand-400" />
              <span className="text-[10px] font-medium text-brand-300">Recorded</span>
            </div>
          )}
          <div className={cn("transition-transform duration-300", isExpanded && "rotate-180")}>
            <ChevronDown className="h-4 w-4 text-white/40" />
          </div>
        </div>
      </div>

      {/* Expanded Content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="border-t border-white/5 bg-black/20"
          >
            <div className="p-4 space-y-5">
              {error ? (
                <div className="flex items-center gap-2 text-red-400 text-sm bg-red-500/10 p-3 rounded-lg border border-red-500/20">
                  <XCircle className="h-4 w-4" />
                  {error}
                </div>
              ) : (
                <>
                  {/* Document Hash */}
                  {documentProof && (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-xs font-semibold text-white/40 uppercase tracking-wider">
                        <Fingerprint className="h-3 w-3" />
                        Digital Fingerprint (SHA-256)
                      </div>
                      <code className="block p-3 bg-black/40 rounded-lg text-xs font-mono text-brand-100/70 break-all border border-white/5">
                        {documentProof.hash_value}
                      </code>
                      <p className="text-[11px] text-white/30 pl-1">
                        Recorded: {formatDate(documentProof.timestamp)}
                      </p>
                    </div>
                  )}

                  {/* Blockchain Details */}
                  {hasBlockchainVerification && (
                    <div className="space-y-3 pt-3 border-t border-white/5">
                      <div className="flex items-center gap-2 text-xs font-semibold text-white/40 uppercase tracking-wider">
                        <LinkIcon className="h-3 w-3" />
                        Blockchain Anchor
                      </div>

                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div className="bg-white/5 p-2 rounded-lg border border-white/5">
                          <span className="text-[10px] text-white/40 block mb-0.5">Network</span>
                          <span className="text-white/80 font-medium">{getChainName(documentProof?.chain_id)}</span>
                        </div>
                        <div className="bg-white/5 p-2 rounded-lg border border-white/5">
                          <span className="text-[10px] text-white/40 block mb-0.5">Block Height</span>
                          <span className="font-mono text-brand-400">#{documentProof?.block_number}</span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between bg-white/5 p-2 rounded-lg border border-white/5">
                        <div className="flex items-center gap-2 overflow-hidden">
                          <span className="text-[10px] text-white/40">TX</span>
                          <code className="text-xs font-mono text-white/60 truncate">
                            {formatHash(documentProof?.tx_hash || '', 16)}
                          </code>
                        </div>
                        {getExplorerUrl(documentProof!) && (
                          <a
                            href={getExplorerUrl(documentProof!)!}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 text-[10px] font-medium text-brand-400 hover:text-brand-300 transition-colors bg-brand-500/10 px-2 py-1 rounded"
                          >
                            View
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Other Proofs */}
                  {proofs.filter(p => p.proof_type !== 'document').length > 0 && (
                    <div className="space-y-2 pt-3 border-t border-white/5">
                      <div className="text-xs font-semibold text-white/40 uppercase tracking-wider">Additional Proofs</div>
                      <div className="space-y-2">
                        {proofs
                          .filter(p => p.proof_type !== 'document')
                          .map((proof, idx) => (
                            <div
                              key={idx}
                              className="flex items-center justify-between text-xs py-2 px-3 bg-white/5 rounded-lg border border-white/5"
                            >
                              <span className="capitalize text-white/70 font-medium">
                                {proof.proof_type.replace('_', ' ')}
                              </span>
                              <div className="flex items-center gap-3">
                                <code className="text-[10px] font-mono text-white/40">
                                  {formatHash(proof.hash_value)}
                                </code>
                                {proof.verified ? (
                                  <CheckCircle className="h-3 w-3 text-brand-400" />
                                ) : (
                                  <Clock className="h-3 w-3 text-amber-500" />
                                )}
                              </div>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}

                  {/* Refresh Button */}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={fetchProofs}
                    disabled={isLoading}
                    className="w-full text-xs h-8 bg-white/5 border-white/10 text-white/60 hover:text-white hover:bg-white/10 hover:border-white/20"
                  >
                    {isLoading ? (
                      <Loader2 className="h-3 w-3 animate-spin mr-2" />
                    ) : null}
                    Refresh Verification
                  </Button>
                </>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/**
 * Compact verification badge for use in lists
 */
export function VerificationBadge({ verified }: { verified?: boolean }) {
  return (
    <div className={cn(
      "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-medium ring-1 ring-inset shadow-sm",
      verified
        ? "bg-brand-500/10 text-brand-300 ring-brand-500/20"
        : "bg-white/5 text-white/40 ring-white/10"
    )}>
      {verified ? (
        <>
          <Shield className="h-3 w-3 text-brand-400" />
          Verified
        </>
      ) : (
        <>
          <Clock className="h-3 w-3" />
          Pending
        </>
      )}
    </div>
  );
}

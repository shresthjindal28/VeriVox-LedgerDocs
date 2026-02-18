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
  ChevronUp
} from 'lucide-react';
import { useAuthStore } from '@/stores';

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
    <div className={cn("rounded-lg border bg-card", className)}>
      {/* Header */}
      <div 
        className="flex items-center justify-between p-4 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <div className={cn(
            "p-2 rounded-full",
            hasBlockchainVerification 
              ? "bg-green-100 text-green-600" 
              : "bg-amber-100 text-amber-600"
          )}>
            <Shield className="h-5 w-5" />
          </div>
          <div>
            <h3 className="font-medium">Document Integrity</h3>
            <p className="text-sm text-muted-foreground">
              {hasBlockchainVerification 
                ? 'Blockchain verified' 
                : 'Hash recorded locally'}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : hasBlockchainVerification ? (
            <CheckCircle className="h-5 w-5 text-green-500" />
          ) : (
            <Clock className="h-5 w-5 text-amber-500" />
          )}
          {isExpanded ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t p-4 space-y-4">
          {error ? (
            <div className="flex items-center gap-2 text-destructive text-sm">
              <XCircle className="h-4 w-4" />
              {error}
            </div>
          ) : (
            <>
              {/* Document Hash */}
              {documentProof && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <FileCheck className="h-4 w-4" />
                    Document Hash
                  </div>
                  <code className="block p-2 bg-muted rounded text-xs font-mono break-all">
                    {documentProof.hash_value}
                  </code>
                  <p className="text-xs text-muted-foreground">
                    Recorded: {formatDate(documentProof.timestamp)}
                  </p>
                </div>
              )}

              {/* Blockchain Details */}
              {hasBlockchainVerification && (
                <div className="space-y-2 pt-2 border-t">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <LinkIcon className="h-4 w-4" />
                    Blockchain Record
                  </div>
                  
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-muted-foreground">Network:</span>
                      <span className="ml-2">{getChainName(documentProof?.chain_id)}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Block:</span>
                      <span className="ml-2">#{documentProof?.block_number}</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <code className="text-xs font-mono text-muted-foreground">
                      Tx: {formatHash(documentProof?.tx_hash || '', 12)}
                    </code>
                    {getExplorerUrl(documentProof!) && (
                      <a
                        href={getExplorerUrl(documentProof!)!}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline"
                      >
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    )}
                  </div>
                </div>
              )}

              {/* Other Proofs */}
              {proofs.filter(p => p.proof_type !== 'document').length > 0 && (
                <div className="space-y-2 pt-2 border-t">
                  <div className="text-sm font-medium">Additional Proofs</div>
                  <div className="space-y-1">
                    {proofs
                      .filter(p => p.proof_type !== 'document')
                      .map((proof, idx) => (
                        <div 
                          key={idx}
                          className="flex items-center justify-between text-sm py-1"
                        >
                          <span className="capitalize text-muted-foreground">
                            {proof.proof_type.replace('_', ' ')}
                          </span>
                          <div className="flex items-center gap-2">
                            <code className="text-xs font-mono">
                              {formatHash(proof.hash_value)}
                            </code>
                            {proof.verified ? (
                              <CheckCircle className="h-3 w-3 text-green-500" />
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
                className="w-full"
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : null}
                Refresh Status
              </Button>
            </>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Compact verification badge for use in lists
 */
export function VerificationBadge({ verified }: { verified?: boolean }) {
  return (
    <div className={cn(
      "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs",
      verified 
        ? "bg-green-100 text-green-700" 
        : "bg-muted text-muted-foreground"
    )}>
      {verified ? (
        <>
          <CheckCircle className="h-3 w-3" />
          Verified
        </>
      ) : (
        <>
          <Shield className="h-3 w-3" />
          Recorded
        </>
      )}
    </div>
  );
}

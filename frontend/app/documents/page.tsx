'use client';

import * as React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useDocuments, useUploadDocument, useDeleteDocument, usePrefetchDocument } from '@/hooks';
import { useDocumentStore, useAuthStore } from '@/stores';
import { FileUpload, Button, Card, DocumentCardSkeleton, ConfirmModal, LoadingOverlay } from '@/components/ui';
import { FileText, Trash2, MessageSquare, Calendar, HardDrive, Plus, Loader2 } from 'lucide-react';
import { formatFileSize, formatDate, cn } from '@/lib/utils';
import { AppLayout } from '@/components/layout';
import type { DocumentInfo } from '@/types';
import { motion } from 'framer-motion';

export default function DocumentsPage() {
  const router = useRouter();
  const { isAuthenticated, isInitialized } = useAuthStore();
  const { data: documents, isLoading } = useDocuments();
  const uploadDocument = useUploadDocument();
  const deleteDocument = useDeleteDocument();
  const prefetchDocument = usePrefetchDocument();
  const { uploadProgress, isUploading, uploadError } = useDocumentStore();

  const [deleteTarget, setDeleteTarget] = React.useState<DocumentInfo | null>(null);

  // Redirect to login if not authenticated
  React.useEffect(() => {
    if (isInitialized && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isInitialized, router]);

  const handleFileSelect = (file: File) => {
    uploadDocument.mutate(file);
  };

  const handleDelete = (doc: DocumentInfo) => {
    setDeleteTarget(doc);
  };

  const confirmDelete = () => {
    if (deleteTarget) {
      deleteDocument.mutate(deleteTarget.document_id);
      setDeleteTarget(null);
    }
  };

  // Show loading while checking auth
  if (!isInitialized || !isAuthenticated) {
    return <LoadingOverlay message="Loading..." />;
  }

  return (
    <AppLayout>
      <div className="min-h-screen bg-black text-white selection:bg-brand-500/30">
        {/* Background Effects */}
        <div className="fixed inset-0 z-0 pointer-events-none">
          <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] bg-brand-500/5 rounded-full blur-[128px]" />
          <div className="absolute bottom-[-10%] left-[-5%] w-[500px] h-[500px] bg-blue-500/5 rounded-full blur-[128px]" />
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff05_1px,transparent_1px),linear-gradient(to_bottom,#ffffff05_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)]" />
        </div>

        <div className="relative z-10 container mx-auto px-4 pt-10 pb-12 max-w-6xl">
          <div className="mb-10 flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <h1 className="text-4xl font-bold tracking-tight mb-2 text-white">
                Your <span className="text-brand-500">Documents</span>
              </h1>
              <p className="text-brand-100/60 text-lg max-w-2xl">
                Upload PDFs to start asking questions with AI assistance. Secure, encrypted, and powered by blockchain verification.
              </p>
            </div>
          </div>

          {/* Upload Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-12"
          >
            <Card className="p-8 border-brand-500/20 bg-brand-950/20 backdrop-blur-sm shadow-xl shadow-brand-500/5">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 rounded-lg bg-brand-500/10 text-brand-500">
                  <Plus className="h-5 w-5" />
                </div>
                <h2 className="text-xl font-semibold text-white">Upload New Document</h2>
              </div>

              <div className="bg-black/40 border border-brand-500/10 rounded-xl overflow-hidden hover:border-brand-500/30 transition-colors">
                <FileUpload
                  onFileSelect={handleFileSelect}
                  accept=".pdf"
                  maxSize={50 * 1024 * 1024}
                  isUploading={isUploading}
                  uploadProgress={uploadProgress}
                  error={uploadError}
                />
              </div>
            </Card>
          </motion.div>

          {/* Documents List */}
          <div className="space-y-6">
            <h2 className="text-xl font-semibold flex items-center gap-2 text-white">
              <FileText className="h-5 w-5 text-brand-500" />
              Library
            </h2>

            {isLoading ? (
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-48 rounded-xl bg-brand-900/10 border border-brand-500/10 animate-pulse" />
                ))}
              </div>
            ) : documents && documents.length > 0 ? (
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {documents.map((doc, index) => (
                  <DocumentCard
                    key={doc.document_id}
                    document={doc}
                    onDelete={() => handleDelete(doc)}
                    onHover={() => prefetchDocument(doc.document_id)}
                    index={index}
                  />
                ))}
              </div>
            ) : (
              <Card className="py-16 text-center border-brand-500/10 bg-brand-950/10 backdrop-blur-sm">
                <div className="w-16 h-16 rounded-full bg-brand-500/10 flex items-center justify-center mx-auto mb-4">
                  <FileText className="h-8 w-8 text-brand-500" />
                </div>
                <h3 className="mb-2 text-xl font-semibold text-white">No documents yet</h3>
                <p className="text-brand-100/60 max-w-sm mx-auto">
                  Upload your first PDF above to get started with AI-powered document analysis.
                </p>
              </Card>
            )}
          </div>

          {/* Delete Confirmation Modal */}
          <ConfirmModal
            isOpen={!!deleteTarget}
            onClose={() => setDeleteTarget(null)}
            onConfirm={confirmDelete}
            title="Delete Document"
            description={`Are you sure you want to delete "${deleteTarget?.filename}"? This action cannot be undone.`}
            confirmText="Delete"
            destructive
            isLoading={deleteDocument.isPending}
          />
        </div>
      </div>
    </AppLayout>
  );
}

interface DocumentCardProps {
  document: DocumentInfo;
  onDelete: () => void;
  onHover: () => void;
  index: number;
}

function DocumentCard({ document, onDelete, onHover, index }: DocumentCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.05 }}
    >
      <Card
        className="group relative overflow-hidden transition-all duration-300 hover:shadow-lg hover:shadow-brand-500/10 hover:border-brand-500/30 border-brand-500/10 bg-brand-950/30 backdrop-blur-md h-full"
        onMouseEnter={onHover}
      >
        <Link href={`/documents/${document.document_id}`} className="block p-5 h-full">
          <div className="flex items-start gap-4">
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-lg bg-brand-500/10 text-brand-500 group-hover:scale-105 group-hover:bg-brand-500/20 transition-all">
              <FileText className="h-7 w-7" />
            </div>
            <div className="min-w-0 flex-1">
              <h3 className="mb-2 truncate font-semibold text-white group-hover:text-brand-500 transition-colors text-lg" title={document.filename}>
                {document.filename}
              </h3>
              <div className="flex flex-col gap-1.5 text-xs text-brand-100/50">
                <span className="flex items-center gap-1.5">
                  <Calendar className="h-3.5 w-3.5" />
                  {formatDate(document.upload_timestamp || document.upload_date || '')}
                </span>
                <span className="flex items-center gap-1.5 bg-brand-500/5 w-fit px-2 py-0.5 rounded-full border border-brand-500/5">
                  <HardDrive className="h-3.5 w-3.5" />
                  {document.file_size ? formatFileSize(document.file_size) : 'N/A'} • {document.page_count} pages
                </span>
              </div>
            </div>
          </div>
          <div className="absolute inset-x-0 bottom-0 h-1 bg-gradient-to-r from-transparent via-brand-500/0 to-transparent group-hover:via-brand-500/50 transition-all duration-500" />
        </Link>

        {/* Actions */}
        <div className="absolute right-3 top-3 flex gap-1 opacity-0 translate-x-2 transition-all duration-200 group-hover:opacity-100 group-hover:translate-x-0">
          <Link href={`/documents/${document.document_id}`}>
            <Button variant="ghost" size="icon" className="h-8 w-8 text-brand-200 hover:text-white hover:bg-brand-500/20">
              <MessageSquare className="h-4 w-4" />
            </Button>
          </Link>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-red-400 hover:bg-red-500/10 hover:text-red-300"
            onClick={(e) => {
              e.preventDefault();
              onDelete();
            }}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </Card>
    </motion.div>
  );
}

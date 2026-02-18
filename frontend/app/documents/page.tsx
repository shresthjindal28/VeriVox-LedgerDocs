'use client';

import * as React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useDocuments, useUploadDocument, useDeleteDocument, usePrefetchDocument } from '@/hooks';
import { useDocumentStore, useAuthStore } from '@/stores';
import { FileUpload, Button, Card, DocumentCardSkeleton, ConfirmModal, LoadingOverlay } from '@/components/ui';
import { FileText, Trash2, MessageSquare, Calendar, HardDrive } from 'lucide-react';
import { formatFileSize, formatDate } from '@/lib/utils';
import type { DocumentInfo } from '@/types';

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
    <div className="mx-auto max-w-6xl px-4 py-8">
      <div className="mb-8">
        <h1 className="mb-2 text-3xl font-bold">Your Documents</h1>
        <p className="text-muted-foreground">
          Upload PDFs to start asking questions with AI assistance
        </p>
      </div>
      
      {/* Upload Section */}
      <Card className="mb-8 p-6">
        <h2 className="mb-4 text-lg font-semibold">Upload New Document</h2>
        <FileUpload
          onFileSelect={handleFileSelect}
          accept=".pdf"
          maxSize={50 * 1024 * 1024}
          isUploading={isUploading}
          uploadProgress={uploadProgress}
          error={uploadError}
        />
      </Card>
      
      {/* Documents List */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold">Your Documents</h2>
        
        {isLoading ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <DocumentCardSkeleton key={i} />
            ))}
          </div>
        ) : documents && documents.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {documents.map((doc) => (
              <DocumentCard
                key={doc.document_id}
                document={doc}
                onDelete={() => handleDelete(doc)}
                onHover={() => prefetchDocument(doc.document_id)}
              />
            ))}
          </div>
        ) : (
          <Card className="p-8 text-center">
            <FileText className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
            <h3 className="mb-2 text-lg font-medium">No documents yet</h3>
            <p className="text-muted-foreground">
              Upload your first PDF to get started
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
  );
}

interface DocumentCardProps {
  document: DocumentInfo;
  onDelete: () => void;
  onHover: () => void;
}

function DocumentCard({ document, onDelete, onHover }: DocumentCardProps) {
  return (
    <Card
      className="group relative overflow-hidden transition-shadow hover:shadow-md"
      onMouseEnter={onHover}
    >
      <Link href={`/documents/${document.document_id}`} className="block p-4">
        <div className="flex items-start gap-4">
          <div className="flex h-16 w-12 shrink-0 items-center justify-center rounded bg-primary/10">
            <FileText className="h-8 w-8 text-primary" />
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="mb-1 truncate font-medium" title={document.filename}>
              {document.filename}
            </h3>
            <div className="flex flex-col gap-1 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                {formatDate(document.upload_timestamp || document.upload_date || '')}
              </span>
              <span className="flex items-center gap-1">
                <HardDrive className="h-3 w-3" />
                {document.file_size ? formatFileSize(document.file_size) : 'N/A'} • {document.page_count} pages
              </span>
            </div>
          </div>
        </div>
      </Link>
      
      {/* Actions */}
      <div className="absolute right-2 top-2 flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
        <Link href={`/documents/${document.document_id}`}>
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <MessageSquare className="h-4 w-4" />
          </Button>
        </Link>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-destructive hover:bg-destructive/10 hover:text-destructive"
          onClick={(e) => {
            e.preventDefault();
            onDelete();
          }}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
    </Card>
  );
}

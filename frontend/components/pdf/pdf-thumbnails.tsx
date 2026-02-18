'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { Document, Page, pdfjs } from 'react-pdf';

interface PDFThumbnailsProps {
  url: string;
  numPages: number;
  currentPage: number;
  onPageSelect: (page: number) => void;
  className?: string;
}

export function PDFThumbnails({
  url,
  numPages,
  currentPage,
  onPageSelect,
  className,
}: PDFThumbnailsProps) {
  return (
    <div className={cn('flex flex-col gap-2 overflow-auto p-2', className)}>
      <Document file={url}>
        {Array.from({ length: numPages }, (_, i) => i + 1).map((pageNum) => (
          <button
            key={pageNum}
            onClick={() => onPageSelect(pageNum)}
            className={cn(
              'relative mb-2 overflow-hidden rounded border-2 transition-all hover:border-primary/50',
              pageNum === currentPage
                ? 'border-primary ring-2 ring-primary/20'
                : 'border-transparent'
            )}
          >
            <Page
              pageNumber={pageNum}
              width={120}
              renderTextLayer={false}
              renderAnnotationLayer={false}
            />
            <span className="absolute bottom-1 right-1 rounded bg-black/50 px-1.5 py-0.5 text-xs text-white">
              {pageNum}
            </span>
          </button>
        ))}
      </Document>
    </div>
  );
}

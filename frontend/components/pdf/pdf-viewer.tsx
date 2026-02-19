'use client';

import * as React from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';
import { cn } from '@/lib/utils';
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Download,
  RotateCw,
  Loader2,
  Minimize2
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/stores';
import type { SourceReference } from '@/types';
import { motion, AnimatePresence } from 'framer-motion';

// Set up worker from public folder
pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.js';

// Types for bounding box highlights
export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface HighlightItem {
  id: string;
  text: string;
  page: number;
  bounding_box: BoundingBox;
  normalized_box?: BoundingBox;  // Percentage-based
  category?: string;
  color?: string;
  opacity?: number;
}

interface PDFViewerProps {
  url: string;
  className?: string;
  initialPage?: number;
  onPageChange?: (page: number) => void;
  highlightedSources?: SourceReference[];
  highlights?: HighlightItem[];  // New: bounding box highlights
  activeHighlightId?: string;  // New: currently speaking highlight
  onHighlightClick?: (highlight: HighlightItem) => void;
}

export function PDFViewer({
  url,
  className,
  initialPage = 1,
  onPageChange,
  highlightedSources = [],
  highlights = [],
  activeHighlightId,
  onHighlightClick,
}: PDFViewerProps) {
  const [numPages, setNumPages] = React.useState<number | null>(null);
  const [currentPage, setCurrentPage] = React.useState(initialPage);
  const [scale, setScale] = React.useState(1.0);
  const [rotation, setRotation] = React.useState(0);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [pdfData, setPdfData] = React.useState<string | null>(null);
  const [pageDimensions, setPageDimensions] = React.useState({ width: 0, height: 0 });
  const containerRef = React.useRef<HTMLDivElement>(null);
  const pdfDataRef = React.useRef<string | null>(null);
  const pageRef = React.useRef<HTMLDivElement>(null);
  const { accessToken } = useAuthStore();

  // Filter highlights for current page
  const currentPageHighlights = React.useMemo(() => {
    return highlights.filter(h => h.page === currentPage);
  }, [highlights, currentPage]);

  // Get highlighted text for current page (legacy source references)
  const currentPageSourceTexts = React.useMemo(() => {
    return highlightedSources
      .filter(s => s.page === currentPage)
      .map(s => s.text);
  }, [highlightedSources, currentPage]);

  // Auto-navigate to page when active highlight changes
  React.useEffect(() => {
    if (activeHighlightId) {
      const activeHighlight = highlights.find(h => h.id === activeHighlightId);
      if (activeHighlight && activeHighlight.page !== currentPage) {
        goToPage(activeHighlight.page);
      }
    }
  }, [activeHighlightId, highlights]);

  // Highlight text in the PDF text layer (legacy)
  React.useEffect(() => {
    if (!pageRef.current || currentPageSourceTexts.length === 0) return;

    // Small delay to ensure text layer is rendered
    const timer = setTimeout(() => {
      highlightTextInPage(currentPageSourceTexts);
    }, 500);

    return () => clearTimeout(timer);
  }, [currentPageSourceTexts, pdfData, currentPage]);

  const highlightTextInPage = (textsToHighlight: string[]) => {
    if (!pageRef.current) return;

    // Find the text layer
    const textLayer = pageRef.current.querySelector('.react-pdf__Page__textContent');
    if (!textLayer) return;

    // Remove existing highlights
    const existingHighlights = textLayer.querySelectorAll('.ai-highlight');
    existingHighlights.forEach(el => {
      el.classList.remove('ai-highlight');
      (el as HTMLElement).style.backgroundColor = '';
    });

    // Get all text spans
    const textSpans = textLayer.querySelectorAll('span');

    textsToHighlight.forEach(searchText => {
      // Normalize search text
      const normalizedSearch = searchText.toLowerCase().trim();
      const searchWords = normalizedSearch.split(/\s+/).slice(0, 15); // First 15 words

      textSpans.forEach(span => {
        const spanText = span.textContent?.toLowerCase() || '';

        // Check if any search words appear in this span
        const hasMatch = searchWords.some(word =>
          word.length > 3 && spanText.includes(word)
        );

        if (hasMatch) {
          span.classList.add('ai-highlight');
          (span as HTMLElement).style.backgroundColor = 'rgba(234, 179, 8, 0.4)'; // Brand yellow/gold
          (span as HTMLElement).style.borderRadius = '2px';
          (span as HTMLElement).style.transition = 'background-color 0.3s ease';
        }
      });
    });

    // Scroll first highlight into view
    const firstHighlight = textLayer.querySelector('.ai-highlight');
    if (firstHighlight) {
      firstHighlight.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  // Update current page when initialPage changes (from parent)
  React.useEffect(() => {
    if (initialPage !== currentPage) {
      setCurrentPage(initialPage);
    }
  }, [initialPage]);

  // Fetch PDF with authentication
  React.useEffect(() => {
    let blobUrl: string | null = null;

    async function fetchPdf() {
      if (!url || !accessToken) {
        setError('No access token');
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);
        const response = await fetch(url, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch PDF: ${response.status}`);
        }

        const blob = await response.blob();
        blobUrl = URL.createObjectURL(blob);
        pdfDataRef.current = blobUrl;
        setPdfData(blobUrl);
        setIsLoading(false);
      } catch (err) {
        console.error('PDF fetch error:', err);
        setError('Failed to load PDF');
        setIsLoading(false);
      }
    }

    fetchPdf();

    // Cleanup blob URL on unmount
    return () => {
      if (pdfDataRef.current) {
        URL.revokeObjectURL(pdfDataRef.current);
        pdfDataRef.current = null;
      }
    };
  }, [url, accessToken]);

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setIsLoading(false);
    setError(null);
  };

  const onDocumentLoadError = (error: Error) => {
    setError('Failed to load PDF');
    setIsLoading(false);
    console.error('PDF load error:', error);
  };

  const goToPage = (page: number) => {
    if (page >= 1 && page <= (numPages || 1)) {
      setCurrentPage(page);
      onPageChange?.(page);
    }
  };

  const zoomIn = () => setScale((s) => Math.min(s + 0.25, 3));
  const zoomOut = () => setScale((s) => Math.max(s - 0.25, 0.5));
  const resetZoom = () => setScale(1.0);
  const rotate = () => setRotation((r) => (r + 90) % 360);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowLeft':
        goToPage(currentPage - 1);
        break;
      case 'ArrowRight':
        goToPage(currentPage + 1);
        break;
      case '+':
        zoomIn();
        break;
      case '-':
        zoomOut();
        break;
    }
  };

  return (
    <div
      className={cn('flex flex-col relative h-full group/viewer', className)}
      onKeyDown={handleKeyDown}
      tabIndex={0}
    >

      {/* PDF Container */}
      <div
        ref={containerRef}
        className="flex-1 overflow-auto bg-transparent custom-scrollbar flex items-center justify-center p-8"
      >
        {error ? (
          <div className="flex h-full items-center justify-center">
            <div className="text-center">
              <div className="bg-red-500/10 p-4 rounded-full w-fit mx-auto mb-3">
                <Minimize2 className="h-6 w-6 text-red-400" />
              </div>
              <p className="text-red-400 font-medium">{error}</p>
              <Button variant="outline" size="sm" onClick={() => window.location.reload()} className="mt-4 border-red-500/30 hover:bg-red-500/10">Retry</Button>
            </div>
          </div>
        ) : !pdfData ? (
          <div className="flex h-full items-center justify-center">
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
              <p className="text-brand-100/50 text-sm">Loading document...</p>
            </div>
          </div>
        ) : (
          <Document
            file={pdfData}
            onLoadSuccess={onDocumentLoadSuccess}
            onLoadError={onDocumentLoadError}
            className="shadow-2xl shadow-black/50"
            loading={
              <div className="flex items-center justify-center p-8">
                <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
              </div>
            }
          >
            <div ref={pageRef} className="relative transition-transform duration-200 ease-out">
              <Page
                pageNumber={currentPage}
                scale={scale}
                rotate={rotation}
                renderTextLayer={true}
                renderAnnotationLayer={true}
                className="shadow-2xl border border-white/5"
                onRenderSuccess={(page) => {
                  setPageDimensions({
                    width: page.width,
                    height: page.height,
                  });
                }}
                loading={
                  <div className="flex h-[800px] w-[600px] items-center justify-center bg-white/5 rounded-lg border border-white/10">
                    <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
                  </div>
                }
              />

              {/* Highlight Overlay */}
              {currentPageHighlights.length > 0 && pageDimensions.width > 0 && (
                <div
                  className="absolute top-0 left-0 pointer-events-none"
                  style={{
                    width: pageDimensions.width * scale,
                    height: pageDimensions.height * scale,
                  }}
                >
                  {currentPageHighlights.map((highlight) => {
                    const box = highlight.normalized_box || highlight.bounding_box;
                    const isNormalized = !!highlight.normalized_box;

                    const left = isNormalized
                      ? box.x1 * 100
                      : (box.x1 / pageDimensions.width) * 100 * scale;
                    const top = isNormalized
                      ? box.y1 * 100
                      : (box.y1 / pageDimensions.height) * 100 * scale;
                    const width = isNormalized
                      ? (box.x2 - box.x1) * 100
                      : ((box.x2 - box.x1) / pageDimensions.width) * 100 * scale;
                    const height = isNormalized
                      ? (box.y2 - box.y1) * 100
                      : ((box.y2 - box.y1) / pageDimensions.height) * 100 * scale;

                    const isActive = activeHighlightId === highlight.id;

                    return (
                      <div
                        key={highlight.id}
                        className={cn(
                          "absolute transition-all duration-300 pointer-events-auto cursor-pointer mix-blend-multiply",
                          isActive && "z-10 ring-2 ring-brand-500"
                        )}
                        style={{
                          left: `${left}%`,
                          top: `${top}%`,
                          width: `${width}%`,
                          height: `${height}%`,
                          backgroundColor: highlight.color || 'rgba(234, 179, 8, 0.3)',
                          opacity: isActive ? 0.8 : (highlight.opacity || 0.4),
                          borderRadius: '2px',
                        }}
                        onClick={() => onHighlightClick?.(highlight)}
                        title={highlight.text}
                      />
                    );
                  })}
                </div>
              )}
            </div>
          </Document>
        )}
      </div>

      {/* Floating Control Bar */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-30 opacity-0 group-hover/viewer:opacity-100 transition-opacity duration-300">
        <div className="flex items-center gap-1 p-1.5 rounded-2xl bg-black/60 backdrop-blur-xl border border-white/10 shadow-2xl">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => goToPage(currentPage - 1)}
            disabled={currentPage <= 1}
            className="h-8 w-8 rounded-lg text-white/70 hover:text-white hover:bg-white/10"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>

          <div className="flex items-center gap-1 mx-1 px-2 py-1 bg-white/5 rounded-md min-w-[80px] justify-center">
            <span className="text-xs font-medium text-white/90">
              {currentPage} <span className="text-white/30">/</span> {numPages || '-'}
            </span>
          </div>

          <Button
            variant="ghost"
            size="icon"
            onClick={() => goToPage(currentPage + 1)}
            disabled={currentPage >= (numPages || 1)}
            className="h-8 w-8 rounded-lg text-white/70 hover:text-white hover:bg-white/10"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>

          <div className="w-px h-4 bg-white/10 mx-1" />

          <Button variant="ghost" size="icon" onClick={zoomOut} className="h-8 w-8 rounded-lg text-white/70 hover:text-white hover:bg-white/10">
            <ZoomOut className="h-4 w-4" />
          </Button>
          <span className="text-[10px] w-8 text-center font-medium text-white/50">{Math.round(scale * 100)}%</span>
          <Button variant="ghost" size="icon" onClick={zoomIn} className="h-8 w-8 rounded-lg text-white/70 hover:text-white hover:bg-white/10">
            <ZoomIn className="h-4 w-4" />
          </Button>

          <div className="w-px h-4 bg-white/10 mx-1" />

          <Button variant="ghost" size="icon" onClick={rotate} className="h-8 w-8 rounded-lg text-white/70 hover:text-white hover:bg-white/10">
            <RotateCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

    </div>
  );
}

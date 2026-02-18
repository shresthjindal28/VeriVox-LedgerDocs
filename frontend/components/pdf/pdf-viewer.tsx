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
  RotateCw 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/stores';
import type { SourceReference } from '@/types';

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
          (span as HTMLElement).style.backgroundColor = 'rgba(255, 215, 0, 0.4)';
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
      className={cn('flex flex-col', className)}
      onKeyDown={handleKeyDown}
      tabIndex={0}
    >
      {/* Toolbar */}
      <div className="flex items-center justify-between border-b bg-muted/50 px-4 py-2">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => goToPage(currentPage - 1)}
            disabled={currentPage <= 1}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          
          <span className="text-sm">
            Page{' '}
            <input
              type="number"
              value={currentPage}
              onChange={(e) => goToPage(parseInt(e.target.value) || 1)}
              className="w-12 rounded border bg-background px-1 text-center"
              min={1}
              max={numPages || 1}
            />{' '}
            of {numPages || '...'}
          </span>
          
          <Button
            variant="ghost"
            size="icon"
            onClick={() => goToPage(currentPage + 1)}
            disabled={currentPage >= (numPages || 1)}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
        
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon" onClick={zoomOut}>
            <ZoomOut className="h-4 w-4" />
          </Button>
          
          <span className="w-16 text-center text-sm">
            {Math.round(scale * 100)}%
          </span>
          
          <Button variant="ghost" size="icon" onClick={zoomIn}>
            <ZoomIn className="h-4 w-4" />
          </Button>
          
          <Button variant="ghost" size="icon" onClick={resetZoom}>
            <Maximize2 className="h-4 w-4" />
          </Button>
          
          <Button variant="ghost" size="icon" onClick={rotate}>
            <RotateCw className="h-4 w-4" />
          </Button>
          
          <a href={url} download>
            <Button variant="ghost" size="icon">
              <Download className="h-4 w-4" />
            </Button>
          </a>
        </div>
      </div>
      
      {/* PDF Container */}
      <div
        ref={containerRef}
        className="flex-1 overflow-auto bg-muted/30"
      >
        {error ? (
          <div className="flex h-full items-center justify-center">
            <p className="text-destructive">{error}</p>
          </div>
        ) : !pdfData ? (
          <div className="flex h-full items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary" />
          </div>
        ) : (
          <div className="flex justify-center p-4">
            <Document
              file={pdfData}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={onDocumentLoadError}
              loading={
                <div className="flex items-center justify-center p-8">
                  <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary" />
                </div>
              }
            >
              <div ref={pageRef} className="relative">
                <Page
                  pageNumber={currentPage}
                  scale={scale}
                  rotate={rotation}
                  renderTextLayer={true}
                  renderAnnotationLayer={true}
                  className="shadow-lg"
                  onRenderSuccess={(page) => {
                    setPageDimensions({
                      width: page.width,
                      height: page.height,
                    });
                  }}
                  loading={
                    <div className="flex h-[800px] w-[600px] items-center justify-center bg-white">
                      <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary" />
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
                      // Use normalized box (percentage) if available, otherwise calculate
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
                            "absolute transition-all duration-300 pointer-events-auto cursor-pointer",
                            isActive && "animate-pulse z-10"
                          )}
                          style={{
                            left: `${left}%`,
                            top: `${top}%`,
                            width: `${width}%`,
                            height: `${height}%`,
                            backgroundColor: highlight.color || '#FFFF00',
                            opacity: isActive ? 0.6 : (highlight.opacity || 0.4),
                            borderRadius: '2px',
                            border: isActive ? '2px solid #FF6B00' : 'none',
                            boxShadow: isActive ? '0 0 8px rgba(255, 107, 0, 0.5)' : 'none',
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
          </div>
        )}
      </div>
    </div>
  );
}

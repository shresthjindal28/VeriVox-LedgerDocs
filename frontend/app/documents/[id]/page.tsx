'use client';

import * as React from 'react';
import { useParams } from 'next/navigation';
import { useDocument, useAskQuestion } from '@/hooks';
import { useAudioRecorder, useVoiceChatWithAudio } from '@/hooks/use-voice';
import { useChatStore } from '@/stores';
import { PDFViewer, HighlightItem } from '@/components/pdf';
import { ChatPanel } from '@/components/chat';
import { VoiceCall } from '@/components/voice/voice-call';
import { VerificationPanel } from '@/components/verification';
import { LoadingOverlay } from '@/components/ui';
import { cn, formatFileSize } from '@/lib/utils';
import { PanelLeftClose, PanelLeft, Phone, Shield, ChevronLeft, Download, MoreVertical, FileText } from 'lucide-react';
import { Button } from '@/components/ui';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import type { SourceReference } from '@/types';
import { AppLayout } from '@/components/layout';

export default function DocumentPage() {
  const params = useParams();
  const documentId = params.id as string;

  const { data: document, isLoading: isDocLoading } = useDocument(documentId);
  const askQuestion = useAskQuestion(documentId);
  const voiceChat = useVoiceChatWithAudio(documentId);
  const { startRecording, stopRecording, isRecording } = useAudioRecorder();

  const { messagesByDocument, streamingMessage, isLoading: isChatLoading } = useChatStore();
  const messages = messagesByDocument[documentId] || [];

  const [isPdfVisible, setIsPdfVisible] = React.useState(true);
  const [currentPage, setCurrentPage] = React.useState(1);
  const [highlightedSources, setHighlightedSources] = React.useState<SourceReference[]>([]);
  const [showVoiceCall, setShowVoiceCall] = React.useState(false);
  const [showVerification, setShowVerification] = React.useState(false);
  const [highlights, setHighlights] = React.useState<HighlightItem[]>([]);
  const [activeHighlightId, setActiveHighlightId] = React.useState<string | undefined>();

  // Highlight sources when a new message with sources arrives
  React.useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    if (lastMessage?.role === 'assistant' && lastMessage.sources?.length) {
      setHighlightedSources(lastMessage.sources);
      // Navigate to the first source page
      setCurrentPage(lastMessage.sources[0].page);
    }
  }, [messages]);

  const handleSend = (message: string) => {
    // Clear previous highlights when asking new question
    setHighlightedSources([]);
    askQuestion.mutate(message);
  };

  const handleVoiceStart = () => {
    startRecording();
  };

  const handleVoiceEnd = async () => {
    try {
      const audioBlob = await stopRecording();
      setHighlightedSources([]); // Clear highlights for new question
      voiceChat.mutate(audioBlob);
    } catch (err) {
      console.error('Voice recording error:', err);
    }
  };

  const handleSourceClick = (source: SourceReference) => {
    setCurrentPage(source.page);
    setHighlightedSources([source]); // Highlight just this source
    if (!isPdfVisible) {
      setIsPdfVisible(true);
    }
  };

  const handleHighlightClick = (highlight: HighlightItem) => {
    setActiveHighlightId(highlight.id);
    setCurrentPage(highlight.page);
    // Clear active after 2 seconds
    setTimeout(() => setActiveHighlightId(undefined), 2000);
  };

  if (isDocLoading) {
    return <LoadingOverlay message="Loading workspace..." />;
  }

  if (!document) {
    return (
      <div className="flex h-screen items-center justify-center bg-black text-white">
        <div className="text-center space-y-4">
          <div className="size-16 rounded-full bg-brand-900/20 flex items-center justify-center mx-auto border border-brand-500/20">
            <FileText className="size-8 text-brand-500/50" />
          </div>
          <h2 className="text-xl font-medium text-white">Document not found</h2>
          <Link href="/dashboard">
            <Button variant="outline" className="mt-4 border-brand-500/30 hover:bg-brand-500/10">Return to Dashboard</Button>
          </Link>
        </div>
      </div>
    );
  }

  const pdfUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'}/api/documents/${documentId}/file`;

  return (
    <AppLayout layoutMode="fullscreen">
      <div className="flex flex-col h-full w-full bg-black overflow-hidden selection:bg-brand-500/30">
        {/* Main Content Area */}
        <div className="flex flex-1 overflow-hidden relative z-10 text-brand-100">

          {/* PDF Viewer Section - width controlled by state */}
          <motion.div
            initial={false}
            animate={{
              width: isPdfVisible ? '55%' : '0%',
              opacity: isPdfVisible ? 1 : 0
            }}
            transition={{ duration: 0.4, ease: [0.32, 0.72, 0, 1] }}
            className="relative flex flex-col border-r border-brand-800/20 bg-black/40 backdrop-blur-sm h-full"
          >
            {/* PDF Toolbar */}
            <div className="h-14 border-b border-brand-800/20 flex items-center justify-between px-4 bg-brand-950/10 backdrop-blur-md sticky top-0 z-20 shrink-0">
              <div className="flex items-center gap-3 overflow-hidden">
                <Link href="/documents" className="p-2 rounded-lg hover:bg-white/5 text-brand-100/60 hover:text-brand-100 transition-colors">
                  <ChevronLeft className="h-5 w-5" />
                </Link>
                <div className="flex flex-col overflow-hidden">
                  <span className="text-sm font-medium text-white truncate max-w-[300px]">{document.filename}</span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <div className="flex items-center gap-2 bg-black/20 rounded-full px-3 py-1 border border-brand-500/10">
                  <span className="text-xs text-brand-100/60">Page</span>
                  <span className="text-xs font-mono text-brand-500 font-bold">{currentPage}</span>
                  <span className="text-xs text-brand-100/40">/ {document.page_count}</span>
                </div>
                <div className="h-4 w-px bg-brand-800/20 mx-1" />
                <Button size="icon" variant="ghost" className="h-8 w-8 text-brand-100/60 hover:text-white hover:bg-white/5">
                  <Download className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* PDF Content - fills remaining height */}
            <div className="flex-1 overflow-hidden relative bg-brand-950/5 h-full">
              <div className="absolute inset-0 overflow-auto custom-scrollbar">
                <PDFViewer
                  url={pdfUrl}
                  className="min-h-full"
                  initialPage={currentPage}
                  onPageChange={setCurrentPage}
                  highlightedSources={highlightedSources}
                  highlights={highlights}
                  activeHighlightId={activeHighlightId}
                  onHighlightClick={handleHighlightClick}
                />
              </div>
            </div>
          </motion.div>

          {/* Intelligence Panel (Right Side) - fills remaining width */}
          <div className="flex-1 flex flex-col relative bg-black/60 backdrop-blur-xl h-full border-l border-white/5">

            {/* Intelligence Header */}
            <div className="h-14 border-b border-brand-800/20 flex items-center justify-between px-6 bg-brand-950/20 backdrop-blur-md z-20 shrink-0">
              <div className="flex items-center gap-3">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setIsPdfVisible(!isPdfVisible)}
                  className="h-8 w-8 rounded-lg text-brand-100/60 hover:text-white hover:bg-brand-500/10"
                >
                  {isPdfVisible ? <PanelLeftClose className="h-4 w-4" /> : <PanelLeft className="h-4 w-4" />}
                </Button>
                <div>
                  <h2 className="text-sm font-semibold text-white tracking-tight flex items-center gap-2">
                    VeriVox Intelligence
                    <span className="flex size-2 relative">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-500 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-brand-500"></span>
                    </span>
                  </h2>
                </div>
              </div>

              <div className="flex items-center gap-1.5 bg-black/20 p-1 rounded-lg border border-brand-800/20">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowVerification(!showVerification)}
                  className={cn(
                    "h-8 text-xs font-medium rounded-md transition-all gap-1.5",
                    showVerification
                      ? "bg-brand-500 text-black shadow-lg shadow-brand-500/20"
                      : "text-brand-100/60 hover:text-white hover:bg-white/5"
                  )}
                >
                  <Shield className="h-3.5 w-3.5" />
                  Verify
                </Button>
                <div className="w-px h-4 bg-white/10" />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowVoiceCall(true)}
                  className={cn(
                    "h-8 text-xs font-medium rounded-md transition-all gap-1.5",
                    showVoiceCall
                      ? "bg-brand-500 text-black shadow-lg shadow-brand-500/20"
                      : "text-brand-100/60 hover:text-white hover:bg-white/5"
                  )}
                >
                  <Phone className="h-3.5 w-3.5" />
                  AI Voice
                </Button>
              </div>
            </div>

            {/* Content Container */}
            <div className="relative flex-1 flex flex-col overflow-hidden">

              {/* Verification Panel - Collapsible */}
              <AnimatePresence>
                {showVerification && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="border-b border-brand-800/20 bg-brand-950/30 overflow-hidden shrink-0 z-10"
                  >
                    <div className="p-4">
                      <VerificationPanel documentId={documentId} className="w-full" />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Chat Interface - Fills remaining space */}
              <div className="flex-1 overflow-hidden relative">
                <ChatPanel
                  documentId={documentId}
                  messages={messages}
                  streamingContent={streamingMessage}
                  onSend={handleSend}
                  onVoiceStart={handleVoiceStart}
                  onVoiceEnd={handleVoiceEnd}
                  onSourceClick={handleSourceClick}
                  isLoading={isChatLoading || askQuestion.isPending}
                  isRecording={isRecording}
                  className="flex-1 h-full pb-0"
                />
              </div>

              {/* Voice Call Overlay - Full Coverage of Intelligence Panel */}
              <AnimatePresence>
                {showVoiceCall && (
                  <motion.div
                    initial={{ opacity: 0, backdropFilter: "blur(0px)" }}
                    animate={{ opacity: 1, backdropFilter: "blur(12px)" }}
                    exit={{ opacity: 0, backdropFilter: "blur(0px)" }}
                    transition={{ duration: 0.3 }}
                    className="absolute inset-0 z-50 bg-black/80 flex flex-col"
                  >
                    <VoiceCall
                      documentId={documentId}
                      onHighlights={(newHighlights) => {
                        setHighlights(newHighlights);
                        if (newHighlights.length > 0) {
                          setActiveHighlightId(newHighlights[0].id);
                          setCurrentPage(newHighlights[0].page);
                        }
                      }}
                      onClose={() => setShowVoiceCall(false)}
                      className="w-full h-full bg-transparent"
                    />
                  </motion.div>
                )}
              </AnimatePresence>

            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

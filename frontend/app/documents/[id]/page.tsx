'use client';

import * as React from 'react';
import { useParams } from 'next/navigation';
import { useDocument, useAskQuestion } from '@/hooks';
import { useAudioRecorder, useVoiceChatWithAudio, useVoiceCall } from '@/hooks/use-voice';
import { useChatStore } from '@/stores';
import { PDFViewer, HighlightItem } from '@/components/pdf';
import { ChatPanel } from '@/components/chat';
import { VoiceCall, VoiceCallButton } from '@/components/voice/voice-call';
import { VerificationPanel } from '@/components/verification';
import { LoadingOverlay, Spinner } from '@/components/ui';
import { cn, formatFileSize } from '@/lib/utils';
import { PanelLeftClose, PanelLeft, Mic, MicOff, Phone, Shield, ChevronLeft, FileText, Download, Share2 } from 'lucide-react';
import { Button } from '@/components/ui';
import { AppLayout } from '@/components/layout';
import Link from 'next/link';
import type { SourceReference } from '@/types';

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
    return <LoadingOverlay message="Loading document..." />;
  }

  if (!document) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center bg-black text-white">
        <p className="text-muted-foreground">Document not found</p>
      </div>
    );
  }

  const pdfUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'}/api/documents/${documentId}/file`;

  return (
    <div className="flex h-screen flex-col bg-black overflow-hidden">
      <div className="relative z-50">
        {/* Navbar removed */}
      </div>

      <div className="flex flex-1 overflow-hidden pt-20 relative z-0">
        {/* Background Effects */}
        <div className="fixed inset-0 z-0 pointer-events-none opacity-20">
          <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] bg-brand-500/10 rounded-full blur-[128px]" />
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff05_1px,transparent_1px),linear-gradient(to_bottom,#ffffff05_1px,transparent_1px)] bg-[size:4rem_4rem]" />
        </div>

        {/* PDF Viewer Area */}
        <div
          className={cn(
            'transition-all duration-300 relative z-10 bg-white/5 border-r border-white/10 flex flex-col',
            isPdfVisible ? 'w-1/2' : 'w-0 overflow-hidden'
          )}
        >
          {isPdfVisible && (
            <>
              <div className="h-12 border-b border-white/10 flex items-center justify-between px-4 bg-white/5 backdrop-blur-sm">
                <div className="flex items-center gap-2">
                  <Link href="/documents" className="text-brand-100/60 hover:text-brand-500 transition-colors">
                    <ChevronLeft className="h-5 w-5" />
                  </Link>
                  <span className="text-sm font-medium text-white truncate max-w-[200px]">{document.filename}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-xs text-brand-100/40 bg-white/5 px-2 py-1 rounded-full">
                    Page {currentPage} of {document.page_count}
                  </div>
                </div>
              </div>
              <div className="flex-1 overflow-auto bg-gray-900/50">
                <PDFViewer
                  url={pdfUrl}
                  className="h-full"
                  initialPage={currentPage}
                  onPageChange={setCurrentPage}
                  highlightedSources={highlightedSources}
                  highlights={highlights}
                  activeHighlightId={activeHighlightId}
                  onHighlightClick={handleHighlightClick}
                />
              </div>
            </>
          )}
        </div>

        {/* Chat Panel */}
        <div className={cn('flex flex-1 flex-col relative z-10 bg-black/40 backdrop-blur-sm', isPdfVisible ? 'w-1/2' : 'w-full')}>
          {/* Header */}
          <div className="flex items-center justify-between border-b border-white/10 px-6 h-16 bg-black/20">
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsPdfVisible(!isPdfVisible)}
                title={isPdfVisible ? 'Hide PDF' : 'Show PDF'}
                className="text-brand-100/60 hover:text-white hover:bg-white/10"
              >
                {isPdfVisible ? (
                  <PanelLeftClose className="h-5 w-5" />
                ) : (
                  <PanelLeft className="h-5 w-5" />
                )}
              </Button>
              <div>
                <h1 className="truncate font-semibold text-white/90 text-sm md:text-base max-w-[200px] md:max-w-md" title={document.filename}>
                  AI Chat Assistant
                </h1>
                <p className="text-xs text-brand-500 font-mono">
                  {document.file_size ? formatFileSize(document.file_size) : ''} • Secure Session
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {/* Verification toggle */}
              <Button
                variant={showVerification ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setShowVerification(!showVerification)}
                title="Document Verification"
                className={cn("gap-2 text-xs", showVerification ? "bg-brand-500/20 text-brand-500 hover:bg-brand-500/30" : "text-brand-100/60 hover:text-white hover:bg-white/10")}
              >
                <Shield className="h-4 w-4" />
                <span className="hidden sm:inline">Verify</span>
              </Button>

              {/* Voice call toggle */}
              <Button
                variant={showVoiceCall ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setShowVoiceCall(!showVoiceCall)}
                title="Voice Call"
                className={cn("gap-2 text-xs", showVoiceCall ? "bg-brand-500/20 text-brand-500 hover:bg-brand-500/30" : "text-brand-100/60 hover:text-white hover:bg-white/10")}
              >
                <Phone className="h-4 w-4" />
                <span className="hidden sm:inline">Call</span>
              </Button>

              {/* Voice Record Toggle - Handled in Chat Input mostly, but keeping global control here if needed */}
            </div>
          </div>

          {/* Verification Panel */}
          {showVerification && (
            <div className="border-b border-white/10 p-4 bg-brand-950/30 animate-in slide-in-from-top-2">
              <VerificationPanel
                documentId={documentId}
                className="w-full"
              />
            </div>
          )}

          {/* Voice Call Panel */}
          {showVoiceCall && (
            <div className="border-b border-white/10 p-4 bg-brand-950/30 animate-in slide-in-from-top-2">
              <VoiceCall
                documentId={documentId}
                onHighlights={(newHighlights) => {
                  setHighlights(newHighlights);
                  if (newHighlights.length > 0) {
                    setActiveHighlightId(newHighlights[0].id);
                    setCurrentPage(newHighlights[0].page);
                  }
                }}
                className="w-full"
              />
            </div>
          )}

          {/* Chat */}
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
              className="flex-1 h-full"
            />
          </div>

        </div>

        {/* Floating Voice Call Button */}
        {!showVoiceCall && !isRecording && (
          <VoiceCallButton
            documentId={documentId}
            onClick={() => setShowVoiceCall(true)}
            className="fixed bottom-6 right-6 shadow-xl shadow-brand-500/20 z-50 hover:scale-105 transition-transform"
          />
        )}
      </div>
    </div>
  );
}

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
import { cn } from '@/lib/utils';
import { PanelLeftClose, PanelLeft, Mic, MicOff, Phone, Shield } from 'lucide-react';
import { Button } from '@/components/ui';
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
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <p className="text-muted-foreground">Document not found</p>
      </div>
    );
  }
  
  const pdfUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'}/api/documents/${documentId}/file`;
  
  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* PDF Viewer */}
      <div
        className={cn(
          'transition-all duration-300',
          isPdfVisible ? 'w-1/2 border-r' : 'w-0'
        )}
      >
        {isPdfVisible && (
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
        )}
      </div>
      
      {/* Chat Panel */}
      <div className={cn('flex flex-1 flex-col', isPdfVisible ? 'w-1/2' : 'w-full')}>
        {/* Header */}
        <div className="flex items-center justify-between border-b px-4 py-2">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsPdfVisible(!isPdfVisible)}
              title={isPdfVisible ? 'Hide PDF' : 'Show PDF'}
            >
              {isPdfVisible ? (
                <PanelLeftClose className="h-4 w-4" />
              ) : (
                <PanelLeft className="h-4 w-4" />
              )}
            </Button>
            <div>
              <h1 className="truncate font-medium" title={document.filename}>
                {document.filename}
              </h1>
              <p className="text-xs text-muted-foreground">
                {document.page_count} pages
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {/* Verification toggle */}
            <Button
              variant={showVerification ? 'default' : 'outline'}
              size="icon"
              onClick={() => setShowVerification(!showVerification)}
              title="Document Verification"
            >
              <Shield className="h-4 w-4" />
            </Button>
            
            {/* Voice call toggle */}
            <Button
              variant={showVoiceCall ? 'default' : 'outline'}
              size="icon"
              onClick={() => setShowVoiceCall(!showVoiceCall)}
              title="Voice Call"
            >
              <Phone className="h-4 w-4" />
            </Button>
            
            {/* Voice recording toggle */}
            <Button
              variant={isRecording ? 'destructive' : 'outline'}
              size="icon"
              onClick={isRecording ? handleVoiceEnd : handleVoiceStart}
              className={cn(isRecording && 'animate-pulse')}
            >
              {isRecording ? (
                <MicOff className="h-4 w-4" />
              ) : (
                <Mic className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
        
        {/* Verification Panel */}
        {showVerification && (
          <div className="border-b p-4">
            <VerificationPanel
              documentId={documentId}
              className="w-full"
            />
          </div>
        )}
        
        {/* Voice Call Panel */}
        {showVoiceCall && (
          <div className="border-b p-4">
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
          className="flex-1"
        />
      </div>
      
      {/* Floating Voice Call Button */}
      {!showVoiceCall && (
        <VoiceCallButton
          documentId={documentId}
          onClick={() => setShowVoiceCall(true)}
          className="fixed bottom-6 right-6"
        />
      )}
    </div>
  );
}

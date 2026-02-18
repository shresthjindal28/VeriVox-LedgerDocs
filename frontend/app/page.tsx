import Link from "next/link";
import { FileText, MessageSquare, Mic, Upload, ArrowRight } from "lucide-react";

export default function Home() {
  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-primary/10 to-background px-4 py-24 md:py-32">
        <div className="mx-auto max-w-4xl text-center">
          <h1 className="mb-6 text-4xl font-bold tracking-tight md:text-6xl">
            Learn Smarter with{" "}
            <span className="text-primary">AI-Powered</span> PDF Analysis
          </h1>
          <p className="mb-8 text-lg text-muted-foreground md:text-xl">
            Upload your study materials and instantly chat with an AI that understands
            every page. Get answers, summaries, and insights in seconds.
          </p>
          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link
              href="/documents"
              className="inline-flex h-12 items-center justify-center gap-2 rounded-lg bg-primary px-8 text-lg font-medium text-primary-foreground transition-colors hover:bg-primary/90"
            >
              <Upload className="h-5 w-5" />
              Upload PDF
            </Link>
            <Link
              href="/login"
              className="inline-flex h-12 items-center justify-center gap-2 rounded-lg border px-8 text-lg font-medium transition-colors hover:bg-accent"
            >
              Get Started
              <ArrowRight className="h-5 w-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="px-4 py-20">
        <div className="mx-auto max-w-6xl">
          <h2 className="mb-12 text-center text-3xl font-bold">
            Everything you need to study effectively
          </h2>
          <div className="grid gap-8 md:grid-cols-3">
            {/* Feature 1 */}
            <div className="rounded-lg border bg-card p-6">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                <FileText className="h-6 w-6 text-primary" />
              </div>
              <h3 className="mb-2 text-xl font-semibold">PDF Processing</h3>
              <p className="text-muted-foreground">
                Upload any PDF document and our AI will extract and understand all
                the content, making it searchable and queryable.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="rounded-lg border bg-card p-6">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                <MessageSquare className="h-6 w-6 text-primary" />
              </div>
              <h3 className="mb-2 text-xl font-semibold">Smart Chat</h3>
              <p className="text-muted-foreground">
                Ask questions about your documents and get accurate answers with
                source references. Perfect for studying and research.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="rounded-lg border bg-card p-6">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                <Mic className="h-6 w-6 text-primary" />
              </div>
              <h3 className="mb-2 text-xl font-semibold">Voice Interaction</h3>
              <p className="text-muted-foreground">
                Talk to your documents using voice. Ask questions naturally and
                listen to AI responses hands-free while studying.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section className="bg-muted/50 px-4 py-20">
        <div className="mx-auto max-w-4xl">
          <h2 className="mb-12 text-center text-3xl font-bold">How it works</h2>
          <div className="space-y-8">
            <div className="flex gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary text-lg font-bold text-primary-foreground">
                1
              </div>
              <div>
                <h3 className="mb-1 text-lg font-semibold">Upload your PDF</h3>
                <p className="text-muted-foreground">
                  Simply drag and drop your study materials, textbooks, or research
                  papers.
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary text-lg font-bold text-primary-foreground">
                2
              </div>
              <div>
                <h3 className="mb-1 text-lg font-semibold">AI processes your content</h3>
                <p className="text-muted-foreground">
                  Our AI reads and understands every page, creating a searchable
                  knowledge base.
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary text-lg font-bold text-primary-foreground">
                3
              </div>
              <div>
                <h3 className="mb-1 text-lg font-semibold">Ask anything</h3>
                <p className="text-muted-foreground">
                  Chat or speak with your documents. Get instant answers with
                  references to the exact pages.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-4 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="mb-4 text-3xl font-bold">Ready to study smarter?</h2>
          <p className="mb-8 text-muted-foreground">
            Join thousands of students using AI to understand their study materials
            better.
          </p>
          <Link
            href="/register"
            className="inline-flex h-12 items-center justify-center gap-2 rounded-lg bg-primary px-8 text-lg font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Start Free Today
            <ArrowRight className="h-5 w-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t px-4 py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 md:flex-row">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            <span className="font-semibold">Study With Me</span>
          </div>
          <p className="text-sm text-muted-foreground">
            © 2024 Study With Me. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}

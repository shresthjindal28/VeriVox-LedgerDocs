import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Mic, Brain, FileText, Eye, Database, Lock, CheckCircle } from "lucide-react";

const features = [
    {
        title: "Real-Time Voice-to-Voice Interaction",
        description: "Bidirectional voice conversation with PDFs using real-time speech-to-text and text-to-speech. Speak naturally and receive immediate spoken responses sourced directly from your document content.",
        icon: <Mic className="size-6 text-brand-950" />,
        color: "bg-brand-500",
        stats: ["Real-time STT/TTS", "Bidirectional Audio"]
    },
    {
        title: "Strict Document-Bound RAG",
        description: "Retrieval-augmented generation constrained exclusively to your uploaded PDFs. The AI cannot access external knowledge bases or training data—only content retrieved from your documents. Every response includes source citations.",
        icon: <Brain className="size-6 text-brand-950" />,
        color: "bg-brand-500",
        stats: ["Zero External Context", "Source-Verified Responses"]
    },
    {
        title: "Exhaustive Structured Extraction",
        description: "Automated extraction of structured data including skills, projects, certifications, work experience, and document metadata. Parse resumes, contracts, technical specifications, and legal documents into JSON, CSV, or custom schemas.",
        icon: <FileText className="size-6 text-brand-950" />,
        color: "bg-brand-500",
        stats: ["Skills & Projects", "Metadata Extraction"]
    },
    {
        title: "Visual Highlight Synchronization",
        description: "AI responses automatically highlight corresponding sections within the PDF viewer in real-time. Visual indicators show exactly which document passages were used to generate each answer, with precise page and paragraph references.",
        icon: <Eye className="size-6 text-brand-950" />,
        color: "bg-brand-500",
        stats: ["Live Highlighting", "Source Visualization"]
    },
    {
        title: "Blockchain-Backed Integrity",
        description: "Every uploaded document and voice session receives a SHA-256 cryptographic hash recorded on an immutable ledger. Verify document authenticity, detect tampering, and prove session integrity with cryptographic proofs.",
        icon: <Database className="size-6 text-brand-950" />,
        color: "bg-brand-500",
        stats: ["SHA-256 Hashing", "Session Verification"]
    },
    {
        title: "Secure Authentication & Ownership Validation",
        description: "Multi-factor authentication (MFA) required for all access. Cryptographic ownership validation ensures document ownership is verifiable on-chain. Your documents remain yours with provable, permanent ownership records.",
        icon: <Lock className="size-6 text-brand-950" />,
        color: "bg-brand-500",
        stats: ["MFA Required", "Ownership Proof"]
    }
];

export function Features() {
    return (
        <section id="features" className="py-20 lg:py-32 bg-black border-y border-brand-800/20">
            <div className="container mx-auto px-4">
                <div className="text-left mb-16 px-4">
                    <h2 className="text-3xl lg:text-4xl font-bold mb-4 tracking-tight text-white">
                        AI That Stays <span className="text-brand-500">Within Your Documents</span>
                    </h2>
                    <p className="text-muted-foreground max-w-2xl text-lg font-light">
                        VeriVox LedgerDocs enforces strict document-bound RAG—no external knowledge, no hallucinations. Every AI response is retrieved exclusively from your uploaded PDFs, with cryptographic verification on an immutable ledger for document and session integrity.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 px-4">
                    {features.map((feature, index) => (
                        <Card key={index} className="bg-brand-950/40 backdrop-blur-sm border-brand-800/50 hover:border-brand-500/50 transition-all hover:shadow-lg hover:shadow-brand-500/10 hover:-translate-y-1">
                            <CardHeader>
                                <div className={`w-12 h-12 rounded-full ${feature.color} flex items-center justify-center mb-6`}>
                                    {feature.icon}
                                </div>
                                <CardTitle className="text-xl text-brand-100">{feature.title}</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <CardDescription className="text-base text-brand-100/70 mb-6 leading-relaxed">
                                    {feature.description}
                                </CardDescription>
                                <ul className="space-y-3">
                                    {feature.stats.map((stat, i) => (
                                        <li key={i} className="flex items-center gap-2 text-sm text-brand-500 font-medium">
                                            <CheckCircle className="size-4 fill-brand-500 text-black" />
                                            <span>{stat}</span>
                                        </li>
                                    ))}
                                </ul>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </div>
        </section>
    );
}

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Mic, Brain, FileText, Eye, Database, Lock, CheckCircle } from "lucide-react";

const features = [
    {
        title: "Voice-to-Voice PDF Interaction",
        description: "Real-time bidirectional voice conversation with your PDFs. Speak naturally and receive spoken responses with zero latency.",
        icon: <Mic className="size-6 text-brand-950" />,
        color: "bg-brand-500",
        stats: ["Real-time STT/TTS", "Bidirectional Audio"]
    },
    {
        title: "Document-Bound RAG",
        description: "Strict retrieval-augmented generation that operates exclusively within your uploaded documents. No external knowledge, no hallucinations.",
        icon: <Brain className="size-6 text-brand-950" />,
        color: "bg-brand-500",
        stats: ["Zero External Context", "Source-Verified Responses"]
    },
    {
        title: "Exhaustive Structured Extraction",
        description: "Automated extraction of skills, projects, certifications, and metadata into structured formats. Parse resumes, contracts, and technical documents with precision.",
        icon: <FileText className="size-6 text-brand-950" />,
        color: "bg-brand-500",
        stats: ["Skills & Projects", "Metadata Extraction"]
    },
    {
        title: "Visual Highlight Synchronization",
        description: "AI responses automatically highlight relevant sections within the PDF viewer. See exactly where answers are sourced in real-time.",
        icon: <Eye className="size-6 text-brand-950" />,
        color: "bg-brand-500",
        stats: ["Live Highlighting", "Source Visualization"]
    },
    {
        title: "Blockchain Document Integrity",
        description: "Every document and session receives a cryptographic hash on an immutable ledger. Verify authenticity and detect tampering instantly.",
        icon: <Database className="size-6 text-brand-950" />,
        color: "bg-brand-500",
        stats: ["SHA-256 Hashing", "Session Verification"]
    },
    {
        title: "Secure Authentication & Ownership",
        description: "Multi-factor authentication with cryptographic ownership validation. Your documents remain yours, verifiably and permanently.",
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
                        VeriVox LedgerDocs uses document-bound RAG to ensure every AI response is sourced directly from your PDFs, with blockchain verification for complete integrity.
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

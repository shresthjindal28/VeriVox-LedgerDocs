import { ShieldCheck, Lock, Server, FileKey } from "lucide-react";

export function Security() {
    return (
        <section id="security" className="py-20 bg-background text-center">
            <div className="container mx-auto px-4">
                <h2 className="text-3xl lg:text-4xl font-bold mb-6">Blockchain-Backed Document Integrity</h2>
                <p className="text-muted-foreground max-w-2xl mx-auto mb-16">
                    Every document and voice session receives a cryptographic hash on an immutable ledger. Verify authenticity, detect tampering, and prove ownership with mathematical certainty.
                </p>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-5xl mx-auto mb-20">
                    {/* Mock Badges */}
                    {[
                        { label: "SOC2 Type II", sub: "Compliant" },
                        { label: "HIPAA", sub: "Ready" },
                        { label: "GDPR", sub: "Compliant" },
                        { label: "ISO 27001", sub: "Certified" }
                    ].map((badge, i) => (
                        <div key={i} className="flex flex-col items-center justify-center p-6 rounded-2xl bg-brand-500/5 border border-brand-500/10">
                            <ShieldCheck className="size-8 text-brand-700 mb-2" />
                            <span className="font-bold text-lg text-brand-900">{badge.label}</span>
                            <span className="text-xs text-brand-700/70 uppercase tracking-wider">{badge.sub}</span>
                        </div>
                    ))}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-left max-w-5xl mx-auto">
                    <div className="p-6">
                        <Lock className="size-8 text-primary mb-4" />
                        <h3 className="font-bold text-xl mb-2">Secure Authentication</h3>
                        <p className="text-muted-foreground text-sm">
                            Multi-factor authentication with cryptographic ownership validation. Your documents remain yours, verifiably and permanently.
                        </p>
                    </div>
                    <div className="p-6">
                        <Server className="size-8 text-primary mb-4" />
                        <h3 className="font-bold text-xl mb-2">Blockchain Verification</h3>
                        <p className="text-muted-foreground text-sm">
                            SHA-256 document hashes and session integrity proofs anchored to an immutable ledger. Detect any modification instantly.
                        </p>
                    </div>
                    <div className="p-6">
                        <FileKey className="size-8 text-primary mb-4" />
                        <h3 className="font-bold text-xl mb-2">Document-Bound AI</h3>
                        <p className="text-muted-foreground text-sm">
                            RAG architecture ensures AI responses are sourced exclusively from your PDFs. No external knowledge, no data leakage.
                        </p>
                    </div>
                </div>
            </div>
        </section>
    );
}

import { ShieldCheck, Lock, Server, FileKey } from "lucide-react";

export function Security() {
    return (
        <section id="security" className="py-20 bg-background text-center">
            <div className="container mx-auto px-4">
                <h2 className="text-3xl lg:text-4xl font-bold mb-6">Blockchain-Backed Document Integrity</h2>
                <p className="text-muted-foreground max-w-2xl mx-auto mb-16">
                    Every uploaded document and voice session receives a SHA-256 cryptographic hash recorded on an immutable blockchain ledger. Verify document authenticity, detect tampering, and prove ownership with cryptographic proofs.
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
                        <h3 className="font-bold text-xl mb-2">Secure Authentication & Ownership Validation</h3>
                        <p className="text-muted-foreground text-sm">
                            Multi-factor authentication (MFA) required for all access. Cryptographic ownership validation ensures document ownership is verifiable on-chain with provable, permanent records.
                        </p>
                    </div>
                    <div className="p-6">
                        <Server className="size-8 text-primary mb-4" />
                        <h3 className="font-bold text-xl mb-2">Blockchain-Backed Integrity</h3>
                        <p className="text-muted-foreground text-sm">
                            SHA-256 cryptographic hashing for documents and sessions, recorded on an immutable blockchain ledger. Verify authenticity and detect tampering with cryptographic proofs.
                        </p>
                    </div>
                    <div className="p-6">
                        <FileKey className="size-8 text-primary mb-4" />
                        <h3 className="font-bold text-xl mb-2">Strict Document-Bound RAG</h3>
                        <p className="text-muted-foreground text-sm">
                            Retrieval-augmented generation constrained exclusively to your uploaded PDFs. The AI cannot access external knowledge bases—only content retrieved from your documents. Zero data leakage.
                        </p>
                    </div>
                </div>
            </div>
        </section>
    );
}

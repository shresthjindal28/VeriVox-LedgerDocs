import { ShieldCheck, Lock, Server, FileKey } from "lucide-react";

export function Security() {
    return (
        <section id="security" className="py-20 bg-background text-center">
            <div className="container mx-auto px-4">
                <h2 className="text-3xl lg:text-4xl font-bold mb-6">Bank-Grade Security & Compliance</h2>
                <p className="text-muted-foreground max-w-2xl mx-auto mb-16">
                    Your data is your most valuable asset. We protect it with industry-leading encryption and blockchain immutability.
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
                        <h3 className="font-bold text-xl mb-2">End-to-End Encryption</h3>
                        <p className="text-muted-foreground text-sm">
                            Data is encrypted at rest (AES-256) and in transit (TLS 1.3). You hold the keys to your data.
                        </p>
                    </div>
                    <div className="p-6">
                        <Server className="size-8 text-primary mb-4" />
                        <h3 className="font-bold text-xl mb-2">Immutable Ledger</h3>
                        <p className="text-muted-foreground text-sm">
                            Every document hash is anchored to the Ethereum blockchain, ensuring it can never be altered without detection.
                        </p>
                    </div>
                    <div className="p-6">
                        <FileKey className="size-8 text-primary mb-4" />
                        <h3 className="font-bold text-xl mb-2">Granular Access Control</h3>
                        <p className="text-muted-foreground text-sm">
                            Role-based access control (RBAC) ensures only authorized personnel can view sensitive financial data.
                        </p>
                    </div>
                </div>
            </div>
        </section>
    );
}

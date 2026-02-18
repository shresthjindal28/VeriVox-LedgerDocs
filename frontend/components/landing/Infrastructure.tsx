import { ArrowRight, Database, FileText, Lock, Network, Server, Shield } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export function Infrastructure() {
    return (
        <section id="infrastructure" className="py-24 bg-black relative overflow-hidden text-center">
            {/* Background Grids */}
            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-brand-500/20 to-transparent" />
            <div className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-brand-500/20 to-transparent" />
            <div className="absolute inset-0 bg-[linear-gradient(to_right,#000_1px,transparent_1px),linear-gradient(to_bottom,#000_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] opacity-20 pointer-events-none" />

            <div className="container mx-auto px-4 relative z-10">
                <div className="mb-20 max-w-3xl mx-auto">
                    <Badge variant="outline" className="mb-6 border-brand-500/50 text-brand-500 bg-brand-500/10">Architecture</Badge>
                    <h2 className="text-3xl lg:text-5xl font-bold mb-6 text-white tracking-tight">
                        Built on <span className="text-brand-500">Zero-Knowledge</span> Infrastructure
                    </h2>
                    <p className="text-lg text-brand-100/60 font-light">
                        Observe the flow of data from your document to the blockchain. Secure, private, and verifiable at every step.
                    </p>
                </div>

                {/* Pipeline Visual */}
                <div className="relative max-w-5xl mx-auto">
                    {/* Connecting Line */}
                    <div className="hidden lg:block absolute top-1/2 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-brand-500/30 to-transparent -translate-y-1/2 z-0" />

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 relative z-10">
                        {/* Step 1: Ingestion */}
                        <div className="bg-brand-950/80 backdrop-blur-md border border-brand-800/50 p-6 rounded-xl relative group hover:border-brand-500/50 transition-all shadow-lg hover:shadow-brand-500/10">
                            <div className="size-12 rounded-full bg-brand-900/50 flex items-center justify-center mx-auto mb-4 text-brand-500 group-hover:bg-brand-500 group-hover:text-black transition-colors">
                                <FileText className="size-6" />
                            </div>
                            <h3 className="text-white font-bold mb-2">Ingestion & OCR</h3>
                            <p className="text-brand-100/50 text-sm">PDFs are processed locally. Text is extracted via OCR and chunked for embedding.</p>
                            <div className="absolute inset-0 border border-brand-500/0 group-hover:border-brand-500/20 rounded-xl transition-all" />
                        </div>

                        {/* Step 2: Vectorization */}
                        <div className="bg-brand-950/80 backdrop-blur-md border border-brand-800/50 p-6 rounded-xl relative group hover:border-brand-500/50 transition-all shadow-lg hover:shadow-brand-500/10">
                            <div className="size-12 rounded-full bg-brand-900/50 flex items-center justify-center mx-auto mb-4 text-brand-500 group-hover:bg-brand-500 group-hover:text-black transition-colors">
                                <Server className="size-6" />
                            </div>
                            <h3 className="text-white font-bold mb-2">Vector Embedding</h3>
                            <p className="text-brand-100/50 text-sm">Chunks are converted to vector embeddings and stored in an isolated namespace.</p>
                        </div>

                        {/* Step 3: RAG & Voice */}
                        <div className="bg-brand-950/80 backdrop-blur-md border border-brand-800/50 p-6 rounded-xl relative group hover:border-brand-500/50 transition-all shadow-lg hover:shadow-brand-500/10">
                            <div className="size-12 rounded-full bg-brand-900/50 flex items-center justify-center mx-auto mb-4 text-brand-500 group-hover:bg-brand-500 group-hover:text-black transition-colors">
                                <Network className="size-6" />
                            </div>
                            <h3 className="text-white font-bold mb-2">Voice Synthesis</h3>
                            <p className="text-brand-100/50 text-sm">LLM generates answers from strict context. Responses are synthesized to speech in real-time.</p>
                        </div>

                        {/* Step 4: Verification */}
                        <div className="bg-brand-950/80 backdrop-blur-md border border-brand-800/50 p-6 rounded-xl relative group hover:border-brand-500/50 transition-all shadow-lg hover:shadow-brand-500/10">
                            <div className="size-12 rounded-full bg-brand-900/50 flex items-center justify-center mx-auto mb-4 text-brand-500 group-hover:bg-brand-500 group-hover:text-black transition-colors">
                                <Shield className="size-6" />
                            </div>
                            <h3 className="text-white font-bold mb-2">On-Chain Proof</h3>
                            <p className="text-brand-100/50 text-sm">Session hashes and document fingerprints are committed to the VeriVox Ledger.</p>
                        </div>
                    </div>
                </div>

                <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto text-left">
                    <div className="flex items-start gap-4 p-4 rounded-lg bg-white/5 border border-white/5 hover:bg-white/10 transition-colors">
                        <Lock className="size-5 text-brand-500 mt-1 shrink-0" />
                        <div>
                            <h4 className="text-white font-bold text-sm">AES-256 GCM</h4>
                            <p className="text-brand-100/50 text-xs mt-1">Data at rest is encrypted with military-grade standards.</p>
                        </div>
                    </div>
                    <div className="flex items-start gap-4 p-4 rounded-lg bg-white/5 border border-white/5 hover:bg-white/10 transition-colors">
                        <Database className="size-5 text-brand-500 mt-1 shrink-0" />
                        <div>
                            <h4 className="text-white font-bold text-sm">Isolated Namespaces</h4>
                            <p className="text-brand-100/50 text-xs mt-1">Tenant data is strictly separated at the database level.</p>
                        </div>
                    </div>
                    <div className="flex items-start gap-4 p-4 rounded-lg bg-white/5 border border-white/5 hover:bg-white/10 transition-colors">
                        <Shield className="size-5 text-brand-500 mt-1 shrink-0" />
                        <div>
                            <h4 className="text-white font-bold text-sm">SOC 2 Compliant</h4>
                            <p className="text-brand-100/50 text-xs mt-1">Infrastructure meets rigorous security and privacy audits.</p>
                        </div>
                    </div>
                </div>

            </div>
        </section>
    );
}

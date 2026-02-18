import { Button } from "@/components/ui/button";
import { Check, Zap } from "lucide-react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";

export function Pricing() {
    return (
        <section id="pricing" className="py-24 lg:py-32 bg-black relative overflow-hidden">
            {/* Background Glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-brand-500/5 rounded-full blur-[120px] pointer-events-none" />

            <div className="container mx-auto px-4 text-center relative z-10">
                <div className="mb-20 max-w-3xl mx-auto">
                    <h2 className="text-3xl lg:text-5xl font-bold mb-6 text-white tracking-tight">
                        Transparent, <span className="text-brand-500">Verifiable</span> Pricing
                    </h2>
                    <p className="text-lg text-brand-100/60 font-light">
                        Transparent pricing for voice sessions, document processing, and blockchain verification. All usage is recorded and verifiable on-chain.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-7xl mx-auto">
                    {/* Starter */}
                    <Card className="border-brand-800/30 bg-brand-950/20 backdrop-blur-sm flex flex-col hover:border-brand-500/30 transition-all duration-300 group">
                        <CardHeader>
                            <CardTitle className="text-brand-100 text-xl">Protocol Starter</CardTitle>
                            <CardDescription className="text-brand-100/50">For individuals exploring document-bound RAG and voice interaction.</CardDescription>
                            <div className="text-5xl font-bold mt-6 text-white">$0 <span className="text-lg font-normal text-brand-100/40">/mo</span></div>
                        </CardHeader>
                        <CardContent className="space-y-4 text-sm text-left flex-1 mt-6">
                            <div className="flex items-center gap-3 text-brand-100/80"><Check className="size-5 text-brand-500 shrink-0" /> 5 Hours Voice Interaction</div>
                            <div className="flex items-center gap-3 text-brand-100/80"><Check className="size-5 text-brand-500 shrink-0" /> Document-Bound RAG (No External Knowledge)</div>
                            <div className="flex items-center gap-3 text-brand-100/80"><Check className="size-5 text-brand-500 shrink-0" /> 10 Document Uploads</div>
                            <div className="flex items-center gap-3 text-brand-100/40"><Check className="size-5 text-brand-500/40 shrink-0" /> Blockchain Verification</div>
                        </CardContent>
                        <CardFooter>
                            <Button variant="outline" className="w-full border-brand-800 text-brand-100 hover:bg-brand-950 hover:text-white hover:border-brand-500 transition-all">Get Started</Button>
                        </CardFooter>
                    </Card>

                    {/* Pro */}
                    <Card className="border-brand-500 relative bg-brand-950/60 backdrop-blur-md shadow-2xl shadow-brand-500/20 scale-105 z-10 flex flex-col">
                        <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-brand-500 text-black text-xs font-bold px-4 py-1.5 rounded-full uppercase tracking-wider shadow-lg shadow-brand-500/40 flex items-center gap-2">
                            <Zap className="size-3 fill-black" /> Most Popular
                        </div>
                        <CardHeader>
                            <CardTitle className="text-brand-50 text-2xl">Ledger Pro</CardTitle>
                            <CardDescription className="text-brand-100/60">For power users and teams requiring full feature access.</CardDescription>
                            <div className="text-6xl font-bold mt-6 text-brand-500">$49 <span className="text-lg font-normal text-brand-100/40 text-white">/mo</span></div>
                        </CardHeader>
                        <CardContent className="space-y-4 text-sm text-left flex-1 mt-6">
                            <div className="flex items-center gap-3 text-white font-medium"><Check className="size-5 text-brand-500 shrink-0" /> Unlimited Voice Sessions</div>
                            <div className="flex items-center gap-3 text-white font-medium"><Check className="size-5 text-brand-500 shrink-0" /> SHA-256 Blockchain Verification</div>
                            <div className="flex items-center gap-3 text-white font-medium"><Check className="size-5 text-brand-500 shrink-0" /> Exhaustive Structured Extraction API</div>
                            <div className="flex items-center gap-3 text-white font-medium"><Check className="size-5 text-brand-500 shrink-0" /> Real-Time Visual Highlight Sync</div>
                            <div className="flex items-center gap-3 text-white font-medium"><Check className="size-5 text-brand-500 shrink-0" /> Priority Support</div>
                        </CardContent>
                        <CardFooter>
                            <Button className="w-full bg-brand-500 hover:bg-brand-400 text-black font-bold h-12 text-base shadow-lg shadow-brand-500/25">Start Free Trial</Button>
                        </CardFooter>
                    </Card>

                    {/* Enterprise */}
                    <Card className="border-brand-800/30 bg-brand-950/20 backdrop-blur-sm flex flex-col hover:border-brand-500/30 transition-all duration-300 group">
                        <CardHeader>
                            <CardTitle className="text-brand-100 text-xl">Enterprise Node</CardTitle>
                            <CardDescription className="text-brand-100/50">Custom infrastructure, private RAG models, and dedicated validator nodes.</CardDescription>
                            <div className="text-5xl font-bold mt-6 text-white">Custom</div>
                        </CardHeader>
                        <CardContent className="space-y-4 text-sm text-left flex-1 mt-6">
                            <div className="flex items-center gap-3 text-brand-100/80"><Check className="size-5 text-brand-500 shrink-0" /> Private Document-Bound RAG Models</div>
                            <div className="flex items-center gap-3 text-brand-100/80"><Check className="size-5 text-brand-500 shrink-0" /> Dedicated Blockchain Validator Node</div>
                            <div className="flex items-center gap-3 text-brand-100/80"><Check className="size-5 text-brand-500 shrink-0" /> Governance Voting Power</div>
                            <div className="flex items-center gap-3 text-brand-100/80"><Check className="size-5 text-brand-500 shrink-0" /> SSO & Audit Logs</div>
                        </CardContent>
                        <CardFooter>
                            <Button variant="outline" className="w-full border-brand-800 text-brand-100 hover:bg-brand-950 hover:text-white hover:border-brand-500 transition-all">Contact Sales</Button>
                        </CardFooter>
                    </Card>
                </div>
            </div>
        </section>
    );
}

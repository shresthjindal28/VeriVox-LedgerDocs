"use client";

import { Button } from "@/components/ui/button";
import { Play, Pause, FileCheck } from "lucide-react";
import { useState } from "react";

export function Demo() {
    const [isPlaying, setIsPlaying] = useState(false);

    return (
        <section className="py-20 lg:py-32 bg-secondary/30 border-y border-white/5">
            <div className="container mx-auto px-4">
                <div className="flex flex-col lg:flex-row items-center gap-16">

                    <div className="flex-1 space-y-8">
                        <h2 className="text-3xl lg:text-4xl font-bold">
                            See the Truth in <span className="text-primary">Real-Time</span>
                        </h2>
                        <p className="text-muted-foreground text-lg leading-relaxed">
                            VeriVox doesn't just transcribe; it validates. Watch as our engine detects financial commitments, cross-references them with your blockchain ledger, and flags inconsistencies instantly.
                        </p>

                        <div className="space-y-4">
                            <div className="flex items-start gap-4">
                                <div className="w-8 h-8 rounded bg-primary/20 flex items-center justify-center mt-1">
                                    <span className="text-primary font-bold">1</span>
                                </div>
                                <div>
                                    <h4 className="font-bold">Live Transcription</h4>
                                    <p className="text-sm text-muted-foreground">Speaker separation and high-fidelity text generation.</p>
                                </div>
                            </div>
                            <div className="flex items-start gap-4">
                                <div className="w-8 h-8 rounded bg-primary/20 flex items-center justify-center mt-1">
                                    <span className="text-primary font-bold">2</span>
                                </div>
                                <div>
                                    <h4 className="font-bold">Fact Checking</h4>
                                    <p className="text-sm text-muted-foreground">Real-time verification against your hashed documents.</p>
                                </div>
                            </div>
                        </div>

                        <Button size="lg" className="mt-4" onClick={() => setIsPlaying(!isPlaying)}>
                            {isPlaying ? <Pause className="mr-2 size-4" /> : <Play className="mr-2 size-4" />}
                            {isPlaying ? "Pause Demo" : "Watch Demo"}
                        </Button>
                    </div>

                    <div className="flex-1 w-full relative">
                        <div className="absolute inset-0 bg-linear-to-tr from-brand-800/10 to-brand-500/10 rounded-2xl blur-xl" />

                        <div className="relative bg-background border border-white/10 rounded-2xl shadow-2xl overflow-hidden min-h-[400px]">
                            {/* Window Header */}
                            <div className="flex items-center justify-between px-4 py-3 border-b border-white/5 bg-muted/30">
                                <div className="flex items-center gap-2">
                                    <FileCheck className="size-4 text-brand-700" />
                                    <span className="text-xs font-mono">board_meeting_q3.wav</span>
                                </div>
                                <div className="text-xs text-muted-foreground">00:14 / 45:00</div>
                            </div>

                            {/* Chat/Transcript Interface */}
                            <div className="p-6 space-y-6">
                                <div className="flex gap-4">
                                    <div className="w-8 h-8 rounded-full bg-brand-500/20 text-brand-800 flex items-center justify-center text-xs font-bold">
                                        JS
                                    </div>
                                    <div className="space-y-1">
                                        <p className="text-sm font-semibold text-foreground/80">John Smith (CFO)</p>
                                        <p className="text-sm text-muted-foreground">
                                            Based on current projections, we are expecting a <span className={`bg-brand-500/10 text-brand-700 px-1 rounded transition-colors ${isPlaying ? 'bg-brand-500/20 shadow-[0_0_10px_rgba(144,169,85,0.2)]' : ''}`}>15% increase in Q3 revenue</span> compared to last year.
                                        </p>
                                    </div>
                                </div>

                                <div className="flex gap-4">
                                    <div className="w-8 h-8 rounded-full bg-brand-700/20 text-brand-900 flex items-center justify-center text-xs font-bold">
                                        AI
                                    </div>
                                    <div className="space-y-1">
                                        <p className="text-sm font-semibold text-primary">VeriVox Intelligence</p>
                                        <div className="p-3 rounded-lg bg-primary/5 border border-primary/10 text-sm">
                                            <div className="flex items-center gap-2 text-primary font-medium mb-1">
                                                <FileCheck className="size-3" />
                                                Verified against Ledger #8892
                                            </div>
                                            <p className="text-muted-foreground text-xs">
                                                This aligns with the '2024_Financial_Forecast.pdf' hashed on 01/15/2024.
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Waveform Visualization (Simple CSS Simulation) */}
                            <div className="absolute bottom-0 left-0 right-0 h-16 bg-linear-to-t from-background to-transparent flex items-end justify-center gap-1 pb-4 px-4 opacity-50">
                                {[...Array(30)].map((_, i) => (
                                    <div
                                        key={i}
                                        className={`w-1 bg-primary rounded-full transition-all duration-300 ${isPlaying ? 'animate-pulse' : ''}`}
                                        style={{ height: isPlaying ? `${Math.random() * 100}%` : '20%', animationDelay: `${i * 0.05}s` }}
                                    />
                                ))}
                            </div>

                        </div>
                    </div>

                </div>
            </div>
        </section>
    );
}

"use client";

import { Button } from "@/components/ui/button";
import { ArrowRight, Play, Shield, Mic, FileCheck } from "lucide-react";
import { motion, useScroll, useTransform } from "framer-motion";
import { useRef } from "react";

export function Hero() {
    const containerRef = useRef(null);
    const { scrollYProgress } = useScroll({
        target: containerRef,
        offset: ["start start", "end start"]
    });

    const y = useTransform(scrollYProgress, [0, 1], [0, 200]);
    const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0]);

    return (
        <section ref={containerRef} className="relative min-h-screen flex flex-col pt-32 pb-10 overflow-hidden bg-black">
            {/* Dynamic Background */}
            <div className="absolute inset-0 pointer-events-none">
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full max-w-7xl">
                    <div className="absolute top-[10%] left-[20%] w-[500px] h-[500px] rounded-full bg-brand-500/10 blur-[120px]" />
                </div>
                <div className="absolute inset-0 bg-[linear-gradient(to_bottom,transparent_0%,#000_100%)] opacity-80" />
            </div>

            <div className="container relative z-10 px-4 mx-auto flex-1 flex flex-col items-center justify-center text-center">

                {/* Badge */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-8"
                >
                    <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-950/50 border border-brand-500/30 text-brand-500 text-xs font-bold tracking-wide uppercase">
                        <span className="size-2 rounded-full bg-brand-500 animate-pulse" />
                        v2.0 Mainnet is Live
                    </span>
                </motion.div>

                {/* Headline */}
                <motion.h1
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="text-5xl lg:text-7xl font-bold tracking-tight leading-[1.1] text-white max-w-4xl mx-auto mb-6"
                >
                    Talk to Your <span className="text-brand-500 italic">PDFs</span> <br />
                    Voice-to-Voice.
                </motion.h1>

                {/* Subheadline */}
                <motion.p
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="text-lg text-brand-100/60 max-w-2xl mx-auto mb-10 font-light leading-relaxed"
                >
                    Real-time voice interaction with PDFs powered by document-bound RAG. <br className="hidden md:block" />
                    Blockchain-verified integrity, visual highlight sync, and exhaustive structured extraction.
                </motion.p>

                {/* Buttons */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="flex flex-col sm:flex-row items-center gap-4 mb-20"
                >
                    <Button size="lg" className="h-12 px-8 text-base rounded-lg bg-brand-500 hover:bg-brand-400 text-black font-bold border-none transition-all hover:scale-105">
                        Start Free Trial
                    </Button>
                    <Button size="lg" variant="outline" className="h-12 px-8 text-base rounded-lg border-brand-800 bg-white/5 hover:bg-white/10 text-white backdrop-blur-sm transition-all">
                        <Play className="mr-2 size-4 fill-white" /> Watch Demo
                    </Button>
                </motion.div>

                {/* Hero Image (Dashboard) */}
                <motion.div
                    initial={{ opacity: 0, y: 40 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    className="relative w-full max-w-5xl mx-auto aspect-video rounded-xl overflow-hidden shadow-2xl border border-white/10 bg-brand-950/50 backdrop-blur-sm group"
                >
                    {/* Pseudo-Browser Chrome */}
                    <div className="absolute top-0 left-0 right-0 h-6 bg-white/5 border-b border-white/5 flex items-center px-4 gap-2">
                        <div className="size-2 rounded-full bg-red-500/50" />
                        <div className="size-2 rounded-full bg-yellow-500/50" />
                        <div className="size-2 rounded-full bg-green-500/50" />
                        <div className="mx-auto text-[10px] text-white/30 font-mono">verivox-ledger.dashboard</div>
                    </div>

                    <div className="absolute inset-0 top-6 flex items-center justify-center bg-gradient-to-br from-brand-900/20 to-black">
                        <div className="text-brand-500/20 text-6xl font-bold">PDF VOICE INTERACTION</div>
                    </div>
                    {/* Glow behind image */}
                    <div className="absolute -inset-10 bg-brand-500/20 blur-[100px] -z-10" />
                </motion.div>

            </div>

            {/* Stats Bar */}
            <div className="w-full border-t border-white/5 bg-black/50 backdrop-blur-sm py-8 mt-auto">
                <div className="container mx-auto px-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                        {[
                            { label: "PDFs Processed", value: "10M+" },
                            { label: "Voice Sessions", value: "500K+" },
                            { label: "RAG Accuracy", value: "99.9%" },
                            { label: "Blockchain Hash", value: "SHA-256" }
                        ].map((stat, i) => (
                            <div key={i} className="text-left">
                                <div className="text-2xl font-bold text-brand-500">{stat.value}</div>
                                <div className="text-xs uppercase tracking-wider text-brand-100/50 font-medium">{stat.label}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </section>
    );
}

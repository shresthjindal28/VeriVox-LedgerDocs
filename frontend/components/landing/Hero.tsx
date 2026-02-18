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
        <section ref={containerRef} className="relative min-h-[95vh] flex items-center justify-center overflow-hidden pt-32 pb-20 lg:pt-0 lg:pb-0">
            {/* Dynamic Background */}
            <div className="absolute inset-0 pointer-events-none">
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full max-w-7xl">
                    <div className="absolute top-[20%] left-[10%] w-[30vw] h-[30vw] rounded-full bg-brand-500/10 blur-[100px] animate-pulse" style={{ animationDuration: '4s' }} />
                    <div className="absolute bottom-[20%] right-[10%] w-[40vw] h-[40vw] rounded-full bg-brand-800/10 blur-[120px] animate-pulse" style={{ animationDuration: '7s' }} />
                </div>
                <div className="absolute inset-0 bg-[linear-gradient(to_bottom,transparent_0%,var(--color-background)_100%)] opacity-80" />
            </div>

            <div className="container relative z-10 px-4 mx-auto">
                <div className="flex flex-col lg:flex-row items-center gap-16 lg:gap-24">

                    {/* Left Content */}
                    <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.8, ease: "easeOut" }}
                        className="flex-1 text-center lg:text-left space-y-8"
                    >

                        <h1 className="text-5xl lg:text-7xl font-bold tracking-tight leading-[1.1]">
                            Build <span className="text-transparent bg-clip-text bg-linear-to-r from-brand-800 via-brand-600 to-brand-500 dark:from-brand-400 dark:via-brand-200 dark:to-brand-100">Unbreakable</span> <br />
                            Financial Trust.
                        </h1>

                        <p className="text-lg lg:text-xl text-muted-foreground/90 max-w-2xl mx-auto lg:mx-0 leading-relaxed font-light">
                            VeriVox instantly transforms your voice discussions into immutable, blockchain-verified ledger entries. The transparency your investors demand, with the speed you need.
                        </p>

                        <div className="flex flex-col sm:flex-row items-center gap-4 justify-center lg:justify-start pt-4">
                            <Button size="lg" className="h-14 px-8 text-lg rounded-full shadow-xl shadow-brand-500/20 hover:shadow-brand-500/30 transition-all duration-300 bg-brand-800 hover:bg-brand-900 text-white border-none">
                                Start Free Trial <ArrowRight className="ml-2 size-5" />
                            </Button>
                            <Button size="lg" variant="outline" className="h-14 px-8 text-lg rounded-full border-brand-200 dark:border-brand-800 hover:bg-brand-50 dark:hover:bg-brand-900/50 backdrop-blur-sm">
                                <Play className="mr-2 size-4 fill-current" /> Watch Demo
                            </Button>
                        </div>

                        <div className="grid grid-cols-2 gap-6 pt-8 border-t border-brand-200/50 dark:border-brand-800/50 max-w-md mx-auto lg:mx-0">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                                    <Shield className="size-5" />
                                </div>
                                <div className="text-sm">
                                    <div className="font-semibold">SOC2 Type II</div>
                                    <div className="text-muted-foreground text-xs">Certified Security</div>
                                </div>
                            </div>
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400">
                                    <FileCheck className="size-5" />
                                </div>
                                <div className="text-sm">
                                    <div className="font-semibold">Smart Contracts</div>
                                    <div className="text-muted-foreground text-xs">Zero-Knowledge Proofs</div>
                                </div>
                            </div>
                        </div>
                    </motion.div>

                    {/* Right Visual */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, rotate: -2 }}
                        animate={{ opacity: 1, scale: 1, rotate: 0 }}
                        transition={{ duration: 1, delay: 0.3, type: "spring" }}
                        style={{ y, opacity }}
                        className="flex-1 w-full relative perspective-1000"
                    >
                        {/* Glassmorphic Card */}
                        <div className="relative z-10 rounded-3xl border border-white/20 bg-white/10 dark:bg-black/20 backdrop-blur-xl shadow-2xl p-6 lg:p-8 overflow-hidden transform transition-all hover:scale-[1.02] duration-500 group">

                            {/* Abstract UI Representation */}
                            <div className="space-y-6">
                                {/* Header */}
                                <div className="flex items-center justify-between">
                                    <div className="flex gap-2">
                                        <div className="size-3 rounded-full bg-red-400/80" />
                                        <div className="size-3 rounded-full bg-yellow-400/80" />
                                        <div className="size-3 rounded-full bg-green-400/80" />
                                    </div>
                                    <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-black/10 dark:bg-white/5 text-xs font-mono">
                                        <div className="size-2 rounded-full bg-red-500 animate-pulse" />
                                        <span>REC 00:04:23</span>
                                    </div>
                                </div>

                                {/* Flow Visualization */}
                                <div className="relative h-64 rounded-2xl bg-gradient-to-br from-brand-50 to-white dark:from-brand-950 dark:to-black border border-brand-100 dark:border-brand-900 p-6 flex flex-col justify-between overflow-hidden">
                                    {/* Waveform Animation Background */}
                                    {/* Deterministic Waveform using Math.sin/cos based on index */}
                                    <div className="absolute inset-x-0 bottom-0 h-32 opacity-20 pointer-events-none flex items-end justify-center gap-[2px]">
                                        {[...Array(40)].map((_, i) => (
                                            <motion.div
                                                key={i}
                                                className="w-1 bg-brand-500 rounded-t-full"
                                                animate={{
                                                    height: [10, 20 + Math.abs(Math.sin(i * 0.5)) * 40, 10],
                                                }}
                                                transition={{
                                                    duration: 1.5 + Math.abs(Math.cos(i)) * 1,
                                                    repeat: Infinity,
                                                    ease: "easeInOut",
                                                    delay: i * 0.05
                                                }}
                                            />
                                        ))}
                                    </div>

                                    <div className="relative z-10 flex items-center gap-4">
                                        <div className="size-12 rounded-xl bg-brand-500 text-white flex items-center justify-center shadow-lg shadow-brand-500/30">
                                            <Mic className="size-6" />
                                        </div>
                                        <div>
                                            <div className="text-sm font-semibold">Recording Active</div>
                                            <div className="text-xs text-muted-foreground">Board Meeting Q3.wav</div>
                                        </div>
                                    </div>

                                    {/* Connecting Line */}
                                    <div className="absolute left-12 top-20 bottom-20 w-px bg-gradient-to-b from-brand-500/50 to-transparent border-l border-dashed border-brand-300" />

                                    <div className="relative z-10 flex items-center justify-end">
                                        <motion.div
                                            initial={{ x: 20, opacity: 0 }}
                                            animate={{ x: 0, opacity: 1 }}
                                            transition={{ delay: 1, duration: 0.5 }}
                                            className="bg-white dark:bg-brand-900/80 backdrop-blur-md rounded-xl p-4 shadow-xl border border-brand-100 dark:border-brand-800 max-w-[280px]"
                                        >
                                            <div className="flex items-center gap-2 mb-2 text-brand-600 dark:text-brand-400">
                                                <FileCheck className="size-4" />
                                                <span className="text-xs font-bold uppercase tracking-wider">Insight Detected</span>
                                            </div>
                                            <p className="text-sm font-medium leading-snug">
                                                "Agreement reached on 15% budget increase for marketing."
                                            </p>
                                        </motion.div>
                                    </div>
                                </div>

                                {/* Bottom Status */}
                                <div className="flex items-center justify-between text-xs text-muted-foreground px-1">
                                    <div className="flex items-center gap-1.5">
                                        <div className="size-2 rounded-full bg-emerald-500" />
                                        Blockchain Sync: Active
                                    </div>
                                    <div className="font-mono">Block #882910</div>
                                </div>
                            </div>

                            {/* Reflection/Glow Overlay */}
                            <div className="absolute -inset-[100%] bg-gradient-to-r from-transparent via-white/5 to-transparent rotate-45 translate-x-[-100%] animate-[shimmer_8s_infinite]" />
                        </div>

                        {/* Floating Elements (Background Decor) */}
                        <motion.div
                            animate={{ y: [0, -20, 0] }}
                            transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
                            className="absolute -top-12 -right-8 p-4 rounded-2xl bg-white dark:bg-brand-900 shadow-xl border border-brand-100 dark:border-brand-800 z-20 hidden lg:block"
                        >
                            <div className="flex items-center gap-3">
                                <div className="size-10 rounded-full bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
                                    <Shield className="size-5" />
                                </div>
                                <div>
                                    <div className="text-sm font-bold">Smart Ledger</div>
                                    <div className="text-xs text-muted-foreground">Auto-generated</div>
                                </div>
                            </div>
                        </motion.div>
                    </motion.div>
                </div>
            </div>
        </section>
    );
}

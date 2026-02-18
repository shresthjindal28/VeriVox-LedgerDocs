import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";

export function CTA() {
    return (
        <section className="py-24 bg-brand-950 relative overflow-hidden">
             {/* Background Glow */}
             <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-brand-500/10 rounded-full blur-[120px]" />

            <div className="container mx-auto px-4 relative z-10 text-center">
                <h2 className="text-4xl lg:text-5xl font-bold mb-6 tracking-tight text-white">
                    Start Talking to Your <span className="text-brand-500">PDFs</span>
                </h2>
                <p className="text-lg text-brand-100/80 max-w-2xl mx-auto mb-10 font-light">
                    Experience real-time voice-to-voice interaction with document-bound AI and blockchain-backed integrity. No external knowledge, no hallucinations—just your documents, verified.
                </p>

                <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                     <Button size="lg" className="h-14 px-8 text-lg rounded-full shadow-xl shadow-brand-500/20 hover:shadow-brand-500/30 transition-all duration-300 bg-brand-500 hover:bg-brand-400 text-brand-950 font-bold border-none">
                        Get Started Now
                    </Button>
                    <Button size="lg" variant="outline" className="h-14 px-8 text-lg rounded-full border-brand-800 bg-black/20 hover:bg-brand-900/40 backdrop-blur-sm text-white">
                        Contact Sales
                    </Button>
                </div>
            </div>
        </section>
    );
}

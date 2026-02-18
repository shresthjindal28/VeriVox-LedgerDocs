import { ArrowDown } from "lucide-react";

export function HowItWorks() {
    const steps = [
        {
            step: "01",
            title: "Upload & Transcribe",
            description: "Upload your audio, video, or text. Our AI engine instantly transcribes and structures the data, identifying speakers and key topics.",
        },
        {
            step: "02",
            title: "Cryptographic Hashing",
            description: "A unique digital fingerprint (hash) is generated for the document. This hash is anchored to the blockchain, creating an immutable timestamp.",
        },
        {
            step: "03",
            title: "Smart Analysis",
            description: "Our RAG (Retrieval-Augmented Generation) engine indexes the content, allowing you to ask complex questions and get verified answers.",
        },
        {
            step: "04",
            title: "Secure Sharing",
            description: "Share access with stakeholders. They can verify the document's authenticity against the blockchain ledger instantly.",
        }
    ];

    return (
        <section id="how-it-works" className="py-20 lg:py-32 overflow-hidden bg-background relative">
            <div className="container mx-auto px-4">
                <div className="text-center mb-24">
                    <h2 className="text-3xl lg:text-4xl font-bold mb-4">How VeriVox Works</h2>
                    <p className="text-muted-foreground max-w-2xl mx-auto">
                        From raw audio to verified, searchable intelligence in four simple steps.
                    </p>
                </div>

                <div className="relative max-w-5xl mx-auto">
                    {/* Vertical Line */}
                    <div className="absolute left-[19px] lg:left-1/2 top-0 bottom-0 w-px bg-linear-to-b from-transparent via-brand-500/40 to-transparent -translate-x-1/2" />

                    <div className="space-y-16">
                        {steps.map((step, index) => (
                            <div key={index} className={`relative flex flex-col lg:flex-row gap-8 lg:gap-16 ${index % 2 === 0 ? 'lg:text-right' : 'lg:flex-row-reverse lg:text-left'}`}>

                                {/* Step Content Side */}
                                <div className="flex-1 lg:w-1/2 pl-12 lg:pl-0">
                                    <div className={`flex flex-col ${index % 2 === 0 ? 'lg:items-end' : 'lg:items-start'}`}>
                                        <span className="text-6xl font-black text-primary/5 select-none leading-none mb-2">
                                            {step.step}
                                        </span>
                                        <h3 className="text-2xl font-bold mb-3">{step.title}</h3>
                                        <p className="text-muted-foreground leading-relaxed max-w-md">
                                            {step.description}
                                        </p>
                                    </div>
                                </div>

                                {/* Center Point */}
                                <div className="absolute left-[19px] lg:left-1/2 -translate-x-1/2 mt-2 w-4 h-4 rounded-full bg-background border-2 border-primary shadow-[0_0_10px_rgba(var(--primary),0.5)] z-20" />

                                {/* Empty Side for layout balance */}
                                <div className="hidden lg:block flex-1 lg:w-1/2" />
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </section>
    );
}

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Shield, Brain, ScrollText, GitBranch, Users, Lock, Zap, Search } from "lucide-react";

const features = [
    {
        title: "AI-Powered Transcription",
        description: "Multi-speaker recognition with 99.9% accuracy across 30+ languages.",
        icon: <Brain className="size-6 text-primary" />,
    },
    {
        title: "Blockchain Verification",
        description: "Every document is hashed and anchored to the blockchain for immutable proof.",
        icon: <Shield className="size-6 text-primary" />,
    },
    {
        title: "Smart RAG Search",
        description: "Ask questions to your entire document repository and get instant, cited answers.",
        icon: <Search className="size-6 text-primary" />,
    },
    {
        title: "Secure Ledger",
        description: "Financial-grade encryption ensures your data is safe at rest and in transit.",
        icon: <Lock className="size-6 text-primary" />,
    },
    {
        title: "Multi-Party Signoff",
        description: "Streamline approvals with built-in consensus mechanisms for all stakeholders.",
        icon: <Users className="size-6 text-primary" />,
    },
    {
        title: "Audit Trails",
        description: "Complete history of every view, edit, and access request, forever.",
        icon: <GitBranch className="size-6 text-primary" />,
    }
];

export function Features() {
    return (
        <section id="features" className="py-20 lg:py-32 bg-secondary/50">
            <div className="container mx-auto px-4">
                <div className="text-center mb-16">
                    <h2 className="text-3xl lg:text-4xl font-bold mb-4">Intelligent Documentation for the Modern Age</h2>
                    <p className="text-muted-foreground max-w-2xl mx-auto">
                        VeriVox combines advanced AI with blockchain security to create the ultimate system of record for your business conversations.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {features.map((feature, index) => (
                        <Card key={index} className="bg-background/60 backdrop-blur-sm border-white/5 hover:border-brand-500/30 transition-all hover:shadow-lg hover:-translate-y-1">
                            <CardHeader>
                                <div className="w-12 h-12 rounded-lg bg-brand-500/10 flex items-center justify-center mb-4">
                                    {feature.icon}
                                </div>
                                <CardTitle className="text-xl">{feature.title}</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <CardDescription className="text-base">
                                    {feature.description}
                                </CardDescription>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </div>
        </section>
    );
}

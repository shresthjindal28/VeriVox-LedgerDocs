import { Button } from "@/components/ui/button";
import { Check } from "lucide-react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";

export function Pricing() {
    return (
        <section id="pricing" className="py-20 lg:py-32 bg-secondary/20">
            <div className="container mx-auto px-4 text-center">
                <div className="mb-16">
                    <h2 className="text-3xl lg:text-4xl font-bold mb-4">Simple, Transparent Pricing</h2>
                    <p className="text-muted-foreground">Start for free, scale with confidence.</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
                    {/* Starter */}
                    <Card className="border-white/10 bg-background/50 backdrop-blur flex flex-col">
                        <CardHeader>
                            <CardTitle>Starter</CardTitle>
                            <CardDescription>Perfect for individuals and small teams.</CardDescription>
                            <div className="text-4xl font-bold mt-4">$0 <span className="text-lg font-normal text-muted-foreground">/mo</span></div>
                        </CardHeader>
                        <CardContent className="space-y-4 text-sm text-left flex-1">
                            <div className="flex items-center gap-2"><Check className="size-4 text-primary" /> 5 Hours Voice Sessions</div>
                            <div className="flex items-center gap-2"><Check className="size-4 text-primary" /> Document-Bound RAG</div>
                            <div className="flex items-center gap-2"><Check className="size-4 text-primary" /> Basic Extraction</div>
                            <div className="flex items-center gap-2 text-muted-foreground"><Check className="size-4 text-muted-foreground opacity-50" /> Blockchain Verification</div>
                        </CardContent>
                        <CardFooter>
                            <Button variant="outline" className="w-full">Get Started</Button>
                        </CardFooter>
                    </Card>

                    {/* Pro */}
                    <Card className="border-brand-500 relative bg-background/80 backdrop-blur shadow-2xl shadow-brand-500/10 scale-105 z-10 flex flex-col">
                        <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-brand-800 text-brand-100 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wide">
                            Most Popular
                        </div>
                        <CardHeader>
                            <CardTitle>Pro</CardTitle>
                            <CardDescription>For growing businesses needing verification.</CardDescription>
                            <div className="text-4xl font-bold mt-4">$49 <span className="text-lg font-normal text-muted-foreground">/mo</span></div>
                        </CardHeader>
                        <CardContent className="space-y-4 text-sm text-left flex-1">
                            <div className="flex items-center gap-2"><Check className="size-4 text-primary" /> Unlimited Voice Sessions</div>
                            <div className="flex items-center gap-2"><Check className="size-4 text-primary" /> Blockchain Verification</div>
                            <div className="flex items-center gap-2"><Check className="size-4 text-primary" /> Exhaustive Structured Extraction</div>
                            <div className="flex items-center gap-2"><Check className="size-4 text-primary" /> Visual Highlight Sync</div>
                        </CardContent>
                        <CardFooter>
                            <Button className="w-full">Start Free Trial</Button>
                        </CardFooter>
                    </Card>

                    {/* Enterprise */}
                    <Card className="border-white/10 bg-background/50 backdrop-blur flex flex-col">
                        <CardHeader>
                            <CardTitle>Enterprise</CardTitle>
                            <CardDescription>Custom solutions for large organizations.</CardDescription>
                            <div className="text-4xl font-bold mt-4">Custom</div>
                        </CardHeader>
                        <CardContent className="space-y-4 text-sm text-left flex-1">
                            <div className="flex items-center gap-2"><Check className="size-4 text-primary" /> Custom RAG Models</div>
                            <div className="flex items-center gap-2"><Check className="size-4 text-primary" /> Dedicated Account Manager</div>
                            <div className="flex items-center gap-2"><Check className="size-4 text-primary" /> SSO & Session Audit Logs</div>
                            <div className="flex items-center gap-2"><Check className="size-4 text-primary" /> Private Blockchain Node</div>
                        </CardContent>
                        <CardFooter>
                            <Button variant="outline" className="w-full">Contact Sales</Button>
                        </CardFooter>
                    </Card>
                </div>
            </div>
        </section>
    );
}

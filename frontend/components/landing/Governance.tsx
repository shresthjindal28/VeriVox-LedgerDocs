import { Button } from "@/components/ui/button";
import { ArrowUpRight, Users, Vote, Wallet } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export function Governance() {
    return (
        <section id="governance" className="py-24 bg-black border-t border-brand-800/20 relative">
            <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-brand-500/5 rounded-full blur-[120px] pointer-events-none" />

            <div className="container mx-auto px-4">
                <div className="flex flex-col lg:flex-row items-start justify-between gap-16">

                    {/* Left Column: Info */}
                    <div className="lg:w-1/3">
                        <Badge variant="outline" className="mb-6 border-brand-500/50 text-brand-500 bg-brand-500/10">Decentralized Governance</Badge>
                        <h2 className="text-3xl lg:text-4xl font-bold mb-6 text-white tracking-tight">
                            Powered by the <br />
                            <span className="text-brand-500">$VOX Protocol</span>
                        </h2>
                        <p className="text-brand-100/60 text-lg mb-8 leading-relaxed">
                            VeriVox is owned and operated by its community. Token holders vote on protocol upgrades, treasury allocation, and RAG model integrity parameters.
                        </p>

                        <div className="grid grid-cols-2 gap-6 mb-10">
                            <div>
                                <div className="text-3xl font-bold text-white mb-2">$12.4M</div>
                                <div className="text-sm text-brand-100/40 uppercase tracking-wider font-medium">Treasury Value</div>
                            </div>
                            <div>
                                <div className="text-3xl font-bold text-white mb-2">85.2%</div>
                                <div className="text-sm text-brand-100/40 uppercase tracking-wider font-medium">Staked Supply</div>
                            </div>
                        </div>

                        <Button className="bg-white text-black hover:bg-brand-500 hover:text-black font-bold rounded-lg px-6 h-12 transition-colors">
                            View Governance Portal <ArrowUpRight className="ml-2 size-4" />
                        </Button>
                    </div>

                    {/* Right Column: Active Proposals */}
                    <div className="lg:w-2/3 w-full">
                        <div className="grid gap-4">
                            {[
                                { status: "Active", title: "OIP-12: Integrate Llama-3-70b for Enhanced Reasoning", votes: "1.2M VOX", icon: <Vote className="size-5" /> },
                                { status: "Active", title: "OIP-13: Increase Validator Staking Rewards by 2%", votes: "850K VOX", icon: <Wallet className="size-5" /> },
                                { status: "Passed", title: "OIP-11: Partnership with Polygon zkEVM", votes: "3.4M VOX", icon: <Users className="size-5" /> },
                            ].map((proposal, i) => (
                                <Card key={i} className="bg-brand-950/30 border-brand-800/30 hover:border-brand-500/50 transition-all cursor-pointer group">
                                    <CardContent className="p-6 flex items-center justify-between gap-4">
                                        <div className="flex items-start gap-4">
                                            <div className="p-3 rounded-full bg-brand-900/50 text-brand-500 group-hover:bg-brand-500 group-hover:text-black transition-colors">
                                                {proposal.icon}
                                            </div>
                                            <div>
                                                <div className="flex items-center gap-3 mb-2">
                                                    <Badge className={proposal.status === "Active" ? "bg-brand-500 text-black hover:bg-brand-400" : "bg-brand-900 text-brand-100 hover:bg-brand-800"}>
                                                        {proposal.status}
                                                    </Badge>
                                                    <span className="text-sm text-brand-100/40 font-mono">#{2405 + i}</span>
                                                </div>
                                                <h4 className="text-lg font-bold text-white group-hover:text-brand-500 transition-colors">{proposal.title}</h4>
                                            </div>
                                        </div>
                                        <div className="hidden sm:block text-right">
                                            <div className="text-sm text-brand-100/40 mb-1">Total Votes</div>
                                            <div className="text-brand-100 font-mono">{proposal.votes}</div>
                                        </div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    </div>

                </div>
            </div>
        </section>
    );
}

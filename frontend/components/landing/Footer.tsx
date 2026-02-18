import Image from "next/image";
import Link from "next/link";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";

export function Footer() {
    return (
        <footer className="py-16 bg-black border-t border-brand-800/20 text-sm">
            <div className="container mx-auto px-4">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-16">

                    <div className="col-span-1 md:col-span-1 space-y-4">
                        <div className="flex items-center gap-2">
                            <div className="relative size-8 rounded-lg overflow-hidden bg-brand-500 flex items-center justify-center">
                                <Image
                                    src="/logo.jpg"
                                    alt="VeriVox LedgerDocs Logo"
                                    width={32}
                                    height={32}
                                    className="object-cover opacity-90 mix-blend-multiply"
                                />
                            </div>
                            <span className="font-bold text-lg text-white">VeriVox</span>
                        </div>
                        <p className="text-brand-100/60 leading-relaxed max-w-xs">
                            Voice-to-voice PDF interaction with document-bound RAG and blockchain integrity. Your documents, your AI, verifiably yours.
                        </p>
                        <div className="flex gap-2 mt-4">
                            <Button size="icon" variant="ghost" className="rounded-full hover:bg-brand-900 hover:text-brand-500 text-brand-100/60">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z" /></svg>
                            </Button>
                            <Button size="icon" variant="ghost" className="rounded-full hover:bg-brand-900 hover:text-brand-500 text-brand-100/60">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5.5 9.6 3 5c2.2 2.6 5.6 4.1 9 4-.9-4.2 4-6.6 7-3.8 1.1 0 3-1.2 3-1.2z" /></svg>
                            </Button>
                        </div>
                    </div>

                    <div>
                        <h4 className="font-bold mb-6 text-white uppercase text-xs tracking-wider">Product</h4>
                        <ul className="space-y-4 text-brand-100/60">
                            <li><Link href="#" className="hover:text-brand-500 transition-colors">Voice Interaction</Link></li>
                            <li><Link href="#" className="hover:text-brand-500 transition-colors">Document RAG</Link></li>
                            <li><Link href="#" className="hover:text-brand-500 transition-colors">Structured Extraction</Link></li>
                            <li><Link href="#" className="hover:text-brand-500 transition-colors">API Documentation</Link></li>
                        </ul>
                    </div>

                    <div>
                        <h4 className="font-bold mb-6 text-white uppercase text-xs tracking-wider">Resources</h4>
                        <ul className="space-y-4 text-brand-100/60">
                            <li><Link href="#" className="hover:text-brand-500 transition-colors">RAG Architecture</Link></li>
                            <li><Link href="#" className="hover:text-brand-500 transition-colors">Blockchain Verification</Link></li>
                            <li><Link href="#" className="hover:text-brand-500 transition-colors">Extraction Formats</Link></li>
                            <li><Link href="#" className="hover:text-brand-500 transition-colors">Support</Link></li>
                        </ul>
                    </div>

                    <div>
                        <h4 className="font-bold mb-6 text-white uppercase text-xs tracking-wider">Newsletter</h4>
                        <p className="text-brand-100/60 mb-4 text-xs">
                            Stay updated on RAG improvements and blockchain features.
                        </p>
                        <div className="flex items-center gap-2 bg-brand-950/50 border border-brand-800/50 rounded-lg p-1 pl-3 focus-within:border-brand-500 transition-colors">
                            <Input
                                placeholder="Email address"
                                className="bg-transparent border-none text-white placeholder:text-brand-100/30 h-8 p-0 focus-visible:ring-0"
                            />
                            <Button size="sm" className="bg-brand-500 hover:bg-brand-400 text-brand-950 h-8 w-8 p-0 rounded-md">
                                <ArrowRight className="size-4" />
                            </Button>
                        </div>
                    </div>

                </div>

                <div className="pt-8 border-t border-brand-800/20 flex flex-col md:flex-row items-center justify-between text-brand-100/30 text-xs">
                    <p>© 2024 VeriVox LedgerDocs. All rights reserved.</p>
                    <div className="flex gap-6 mt-4 md:mt-0">
                        <Link href="#" className="hover:text-brand-500 transition-colors">Privacy Policy</Link>
                        <Link href="#" className="hover:text-brand-500 transition-colors">Terms of Service</Link>
                        <Link href="#" className="hover:text-brand-500 transition-colors">Cookie Settings</Link>
                    </div>
                </div>
            </div>
        </footer>
    );
}

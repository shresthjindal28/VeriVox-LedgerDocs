import Image from "next/image";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function Navbar() {
    return (
        <nav className="fixed top-0 left-0 right-0 z-50 bg-black/80 backdrop-blur-md border-b border-white/5">
            <div className="container mx-auto px-4 h-20 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="relative size-8 rounded-lg overflow-hidden bg-brand-500 flex items-center justify-center">
                        <Image
                            src="/logo.png"
                            alt="VeriVox Logo"
                            width={32}
                            height={32}
                            className="object-cover opacity-90 mix-blend-multiply"
                        />
                    </div>
                    <span className="font-bold text-xl tracking-tight text-white">VeriVox <span className="text-brand-500 font-light">LedgerDocs</span></span>
                </div>

                <div className="hidden md:flex items-center gap-8 text-sm font-medium text-brand-100/80">
                    <Link href="/#features" className="hover:text-brand-500 transition-colors">Features</Link>
                    <Link href="/#infrastructure" className="hover:text-brand-500 transition-colors">Infrastructure</Link>
                    <Link href="/#governance" className="hover:text-brand-500 transition-colors">Governance</Link>
                    <Link href="/#pricing" className="hover:text-brand-500 transition-colors">Pricing</Link>
                </div>

                <div className="flex items-center gap-6">
                    <Link href="/login" className="text-sm font-bold text-white hover:text-brand-500 transition-colors hidden sm:block">
                        Log In
                    </Link>
                    <Button variant="default" className="font-bold shadow-lg shadow-brand-500/20 bg-brand-500 text-black hover:bg-brand-400 rounded-lg px-6">
                        Get Started
                    </Button>
                </div>
            </div>
        </nav>
    );
}

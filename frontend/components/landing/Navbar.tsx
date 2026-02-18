import Image from "next/image";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function Navbar() {
    return (
        <nav className="fixed top-0 left-0 right-0 z-50 bg-background/60 backdrop-blur-md border-b border-white/10 supports-backdrop-filter:bg-background/60">
            <div className="container mx-auto px-4 h-16 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="relative size-8 rounded-lg overflow-hidden border border-brand-500/20">
                        <Image
                            src="/logo.jpg"
                            alt="VeriVox Logo"
                            fill
                            className="object-cover"
                        />
                    </div>
                    <span className="font-bold text-xl tracking-tight text-brand-950 dark:text-brand-100">VeriVox</span>
                </div>

                <div className="hidden md:flex items-center gap-8 text-sm font-medium text-muted-foreground">
                    <Link href="#features" className="hover:text-primary transition-colors">Features</Link>
                    <Link href="#security" className="hover:text-primary transition-colors">Security</Link>
                    <Link href="#how-it-works" className="hover:text-primary transition-colors">How it Works</Link>
                    <Link href="#pricing" className="hover:text-primary transition-colors">Pricing</Link>
                </div>

                <div className="flex items-center gap-4">
                    <Link href="/login" className="text-sm font-medium hover:text-primary transition-colors hidden sm:block">
                        Log in
                    </Link>
                    <Button variant="default" className="font-semibold shadow-lg shadow-primary/20">
                        Start Talking
                    </Button>
                </div>
            </div>
        </nav>
    );
}

import Image from "next/image";
import Link from "next/link";

export function Footer() {
    return (
        <footer className="py-12 bg-background border-t border-white/10 text-sm">
            <div className="container mx-auto px-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-12">

                    <div className="col-span-2 md:col-span-1">
                        <div className="flex items-center gap-2 mb-4">
                            <div className="relative w-6 h-6 rounded overflow-hidden">
                                <Image
                                    src="/logo.jpg"
                                    alt="VeriVox Logo"
                                    fill
                                    className="object-cover"
                                />
                            </div>
                            <span className="font-bold text-lg">VeriVox</span>
                        </div>
                        <p className="text-muted-foreground max-w-xs">
                            The standard for verifiable financial documentation. Secure, Intelligent, Blockchain-Verified.
                        </p>
                    </div>

                    <div>
                        <h4 className="font-bold mb-4 text-foreground">Product</h4>
                        <ul className="space-y-2 text-muted-foreground">
                            <li><Link href="#features" className="hover:text-primary transition-colors">Features</Link></li>
                            <li><Link href="#security" className="hover:text-primary transition-colors">Security</Link></li>
                            <li><Link href="#pricing" className="hover:text-primary transition-colors">Pricing</Link></li>
                            <li><Link href="#" className="hover:text-primary transition-colors">Enterprise</Link></li>
                        </ul>
                    </div>

                    <div>
                        <h4 className="font-bold mb-4 text-foreground">Company</h4>
                        <ul className="space-y-2 text-muted-foreground">
                            <li><Link href="#" className="hover:text-primary transition-colors">About Us</Link></li>
                            <li><Link href="#" className="hover:text-primary transition-colors">Careers</Link></li>
                            <li><Link href="#" className="hover:text-primary transition-colors">Blog</Link></li>
                            <li><Link href="#" className="hover:text-primary transition-colors">Contact</Link></li>
                        </ul>
                    </div>

                    <div>
                        <h4 className="font-bold mb-4 text-foreground">Legal</h4>
                        <ul className="space-y-2 text-muted-foreground">
                            <li><Link href="#" className="hover:text-primary transition-colors">Privacy Policy</Link></li>
                            <li><Link href="#" className="hover:text-primary transition-colors">Terms of Service</Link></li>
                            <li><Link href="#" className="hover:text-primary transition-colors">Cookie Policy</Link></li>
                        </ul>
                    </div>

                </div>

                <div className="pt-8 border-t border-white/5 flex flex-col md:flex-row items-center justify-between text-muted-foreground">
                    <p>© 2024 VeriVox Inc. All rights reserved.</p>
                </div>
            </div>
        </footer>
    );
}

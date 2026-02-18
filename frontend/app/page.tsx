import { Navbar } from "@/components/landing/Navbar";
import { Hero } from "@/components/landing/Hero";
import { Features } from "@/components/landing/Features";
import { Infrastructure } from "@/components/landing/Infrastructure";
import { Pricing } from "@/components/landing/Pricing";
import { Governance } from "@/components/landing/Governance";
import { CTA } from "@/components/landing/CTA";
import { Footer } from "@/components/landing/Footer";

export default function Home() {
  return (
    <main className="min-h-screen bg-background text-foreground antialiased overflow-x-hidden selection:bg-brand-500/20 selection:text-brand-500">
      <Navbar />
      <Hero />
      <Features />
      <Infrastructure />
      <div className="relative">
        <Governance />
        <Pricing />
      </div>
      <CTA />
      <Footer />
    </main>
  );
}

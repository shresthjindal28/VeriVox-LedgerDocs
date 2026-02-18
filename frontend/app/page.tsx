import { Navbar } from "@/components/landing/Navbar";
import { Hero } from "@/components/landing/Hero";
import { Features } from "@/components/landing/Features";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { Demo } from "@/components/landing/Demo";
import { Security } from "@/components/landing/Security";
import { Pricing } from "@/components/landing/Pricing";
import { Footer } from "@/components/landing/Footer";

export default function Home() {
  return (
    <main className="min-h-screen bg-background text-foreground antialiased overflow-x-hidden selection:bg-primary/20 selection:text-white">
      <Navbar />
      <Hero />
      <Features />
      <HowItWorks />
      <Demo />
      <Security />
      <Pricing />
      <Footer />
    </main>
  );
}

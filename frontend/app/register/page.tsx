'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { toast } from 'sonner';
import { useRegister } from '@/hooks';
import { useAuthStore } from '@/stores';
import { Button, Input, Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui';
import { motion } from 'framer-motion';
import { Navbar } from '@/components/landing/Navbar';

export default function RegisterPage() {
  const router = useRouter();
  const register = useRegister();
  const { isAuthenticated, error } = useAuthStore();

  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [confirmPassword, setConfirmPassword] = React.useState('');
  const [displayName, setDisplayName] = React.useState('');
  const [validationError, setValidationError] = React.useState('');

  React.useEffect(() => {
    if (isAuthenticated) {
      router.push('/documents');
    }
  }, [isAuthenticated, router]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError('');

    if (password !== confirmPassword) {
      setValidationError('Passwords do not match');
      return;
    }

    if (password.length < 8) {
      setValidationError('Password must be at least 8 characters');
      return;
    }

    register.mutate(
      { email, password, display_name: displayName || undefined },
      {
        onSuccess: (data) => {
          toast.success('Registration successful!', {
            description: 'Please check your email to verify your account before signing in.',
            duration: 6000,
          });
          router.push('/login?registered=true');
        },
      }
    );
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center p-4 bg-black overflow-hidden">
      <Navbar />
      {/* Background Effects */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-brand-500/10 rounded-full blur-[120px] pointer-events-none" />

      <div className="absolute inset-0 bg-[linear-gradient(to_right,#000_1px,transparent_1px),linear-gradient(to_bottom,#000_1px,transparent_1px)] bg-size-[4rem_4rem] mask-[radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] opacity-20 pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
        className="w-full max-w-md relative z-10"
      >
        <div className="flex items-center justify-center gap-2 mb-8">
          <div className="relative size-10 rounded-lg overflow-hidden bg-brand-500 flex items-center justify-center shadow-lg shadow-brand-500/20">
            <Image
              src="/logo.png"
              alt="VeriVox Logo"
              width={40}
              height={40}
              className="object-cover opacity-90 mix-blend-multiply"
            />
          </div>
          <span className="font-bold text-2xl tracking-tight text-white">VeriVox <span className="text-brand-500 font-light">LedgerDocs</span></span>
        </div>

        <Card className="bg-brand-950/60 backdrop-blur-md border-brand-800/50 shadow-2xl">
          <CardHeader className="text-center pb-2">
            <CardTitle className="text-2xl font-bold text-white tracking-tight">Create an account</CardTitle>
            <CardDescription className="text-brand-100/60">
              Start your journey to smarter studying
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-6 pt-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Display Name"
                type="text"
                placeholder="John Doe"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="bg-white/5 border-brand-800/50 text-white placeholder:text-brand-100/20 focus:border-brand-500 focus:ring-brand-500/20"
                labelClassName="text-brand-100/80 font-medium"
              />

              <Input
                label="Email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="bg-white/5 border-brand-800/50 text-white placeholder:text-brand-100/20 focus:border-brand-500 focus:ring-brand-500/20"
                labelClassName="text-brand-100/80 font-medium"
              />

              <Input
                label="Password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="bg-white/5 border-brand-800/50 text-white placeholder:text-brand-100/20 focus:border-brand-500 focus:ring-brand-500/20"
                labelClassName="text-brand-100/80 font-medium"
              />

              <Input
                label="Confirm Password"
                type="password"
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                className="bg-white/5 border-brand-800/50 text-white placeholder:text-brand-100/20 focus:border-brand-500 focus:ring-brand-500/20"
                labelClassName="text-brand-100/80 font-medium"
              />

              {(error || validationError) && (
                <div className="p-3 rounded-md bg-destructive/10 border border-destructive/20 text-sm text-destructive font-medium">
                  {validationError || error}
                </div>
              )}

              <Button
                type="submit"
                className="w-full bg-brand-500 hover:bg-brand-400 text-black font-bold h-11"
                isLoading={register.isPending}
              >
                Create Account
              </Button>
            </form>
          </CardContent>

          <CardFooter className="justify-center border-t border-brand-800/30 pt-4">
            <p className="text-sm text-brand-100/60">
              Already have an account?{' '}
              <Link href="/login" className="font-bold text-brand-500 hover:text-brand-400 hover:underline">
                Sign in
              </Link>
            </p>
          </CardFooter>
        </Card>
      </motion.div>
    </div>
  );
}

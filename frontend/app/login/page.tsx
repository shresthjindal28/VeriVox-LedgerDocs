'use client';

import * as React from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { toast } from 'sonner';
import { useLogin } from '@/hooks';
import { useAuthStore } from '@/stores';
import { Button, Input, Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui';
import { authApi } from '@/lib/api';
import { motion } from 'framer-motion';
import { Navbar } from '@/components/landing/Navbar';

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const login = useLogin();
  const { isAuthenticated, error } = useAuthStore();

  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');

  // Show toast when redirected from registration
  React.useEffect(() => {
    if (searchParams.get('registered') === 'true') {
      toast.success('Registration successful!', {
        description: 'Please check your email to verify your account before signing in.',
        duration: 6000,
      });
      // Remove the query param from URL without reload
      router.replace('/login', { scroll: false });
    }
  }, [searchParams, router]);

  React.useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  // Show toast for email not confirmed error
  React.useEffect(() => {
    if (error && error.toLowerCase().includes('email not confirmed')) {
      toast.error('Email not verified', {
        description: 'Please check your inbox and verify your email before signing in.',
        duration: 6000,
      });
    }
  }, [error]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    login.mutate({ email, password });
  };

  const handleGoogleLogin = async () => {
    try {
      const { url } = await authApi.getGoogleAuthUrl();
      window.location.href = url;
    } catch (err) {
      console.error('Google auth error:', err);
    }
  };

  const handleLinkedInLogin = async () => {
    try {
      const { url } = await authApi.getLinkedInAuthUrl();
      window.location.href = url;
    } catch (err) {
      console.error('LinkedIn auth error:', err);
    }
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
            <CardTitle className="text-2xl font-bold text-white tracking-tight">Welcome Back</CardTitle>
            <CardDescription className="text-brand-100/60">
              Sign in to verify your documents
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-6 pt-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
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
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 text-brand-100/80">Password</label>
                  <Link
                    href="/forgot-password"
                    className="text-xs text-brand-500 hover:text-brand-400 font-medium"
                  >
                    Forgot password?
                  </Link>
                </div>
                <Input
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="bg-white/5 border-brand-800/50 text-white placeholder:text-brand-100/20 focus:border-brand-500 focus:ring-brand-500/20"
                />
              </div>

              {error && (
                <div className="p-3 rounded-md bg-destructive/10 border border-destructive/20 text-sm text-destructive font-medium">
                  {error}
                </div>
              )}

              <Button
                type="submit"
                className="w-full bg-brand-500 hover:bg-brand-400 text-black font-bold h-11"
                isLoading={login.isPending}
              >
                Sign In
              </Button>
            </form>

            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-brand-800/50" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-brand-950 px-2 text-brand-100/40">
                  Or continue with
                </span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <Button
                type="button"
                variant="outline"
                onClick={handleGoogleLogin}
                className="bg-white/5 border-brand-800/50 hover:bg-white/10 text-white hover:text-white hover:border-brand-500/50"
              >
                <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
                  <path
                    fill="currentColor"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="currentColor"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="currentColor"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  />
                  <path
                    fill="currentColor"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  />
                </svg>
                Google
              </Button>

              <Button
                type="button"
                variant="outline"
                onClick={handleLinkedInLogin}
                className="bg-white/5 border-brand-800/50 hover:bg-white/10 text-white hover:text-white hover:border-brand-500/50"
              >
                <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                </svg>
                LinkedIn
              </Button>
            </div>
          </CardContent>

          <CardFooter className="justify-center border-t border-brand-800/30 pt-4">
            <p className="text-sm text-brand-100/60">
              Don&apos;t have an account?{' '}
              <Link href="/register" className="font-bold text-brand-500 hover:text-brand-400 hover:underline">
                Sign up
              </Link>
            </p>
          </CardFooter>
        </Card>
      </motion.div>
    </div>
  );
}

'use client';

import * as React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/stores';
import { useLogout } from '@/hooks';
import {
  FileText,
  Home,
  LogOut,
  Menu,
  Moon,
  Settings,
  Sun,
  User,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';

interface NavbarProps {
  className?: string;
}

export function Navbar({ className }: NavbarProps) {
  const pathname = usePathname();
  const { user, isAuthenticated } = useAuthStore();

  // Hide global navbar on landing page and auth pages which have their own specific navbars
  if (pathname === '/' || pathname === '/login' || pathname === '/register') {
    return null;
  }

  const logout = useLogout();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = React.useState(false);
  const [isDark, setIsDark] = React.useState(false);

  React.useEffect(() => {
    setIsDark(document.documentElement.classList.contains('dark'));
  }, []);

  const toggleTheme = () => {
    setIsDark(!isDark);
    document.documentElement.classList.toggle('dark');
  };

  const navLinks = [
    { href: '/', label: 'Home', icon: Home },
    { href: '/documents', label: 'Documents', icon: FileText },
  ];

  const handleLogout = () => {
    logout.mutate();
  };

  return (
    <nav className={cn('border-b bg-background', className)}>
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <FileText className="h-5 w-5" />
          </div>
          <span className="text-lg font-semibold">Study With Me</span>
        </Link>

        {/* Desktop Navigation */}
        <div className="hidden items-center gap-6 md:flex">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                'flex items-center gap-2 text-sm font-medium transition-colors hover:text-primary',
                pathname === link.href
                  ? 'text-primary'
                  : 'text-muted-foreground'
              )}
            >
              <link.icon className="h-4 w-4" />
              {link.label}
            </Link>
          ))}
        </div>

        {/* Actions */}
        <div className="hidden items-center gap-4 md:flex">
          <Button variant="ghost" size="icon" onClick={toggleTheme}>
            {isDark ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
          </Button>

          {isAuthenticated ? (
            <>
              <Link href="/profile">
                <Button variant="ghost" size="icon">
                  <User className="h-4 w-4" />
                </Button>
              </Link>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleLogout}
                disabled={logout.isPending}
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </>
          ) : (
            <>
              <Link href="/login">
                <Button variant="ghost">Sign In</Button>
              </Link>
              <Link href="/register">
                <Button>Sign Up</Button>
              </Link>
            </>
          )}
        </div>

        {/* Mobile menu button */}
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        >
          {isMobileMenuOpen ? (
            <X className="h-5 w-5" />
          ) : (
            <Menu className="h-5 w-5" />
          )}
        </Button>
      </div>

      {/* Mobile menu */}
      {isMobileMenuOpen && (
        <div className="border-t px-4 py-4 md:hidden">
          <div className="flex flex-col gap-4">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setIsMobileMenuOpen(false)}
                className={cn(
                  'flex items-center gap-2 text-sm font-medium',
                  pathname === link.href
                    ? 'text-primary'
                    : 'text-muted-foreground'
                )}
              >
                <link.icon className="h-4 w-4" />
                {link.label}
              </Link>
            ))}

            <hr className="my-2" />

            {isAuthenticated ? (
              <>
                <Link
                  href="/profile"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex items-center gap-2 text-sm text-muted-foreground"
                >
                  <User className="h-4 w-4" />
                  Profile
                </Link>
                <button
                  onClick={() => {
                    setIsMobileMenuOpen(false);
                    handleLogout();
                  }}
                  className="flex items-center gap-2 text-sm text-muted-foreground"
                >
                  <LogOut className="h-4 w-4" />
                  Sign Out
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="text-sm text-muted-foreground"
                >
                  Sign In
                </Link>
                <Link
                  href="/register"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="text-sm text-primary"
                >
                  Sign Up
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}

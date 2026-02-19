'use client';

import * as React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  FileText,
  Settings,
  Library,
  User,
  LogOut,
  ChevronLeft,
  ChevronRight,
  LayoutDashboard
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/stores';
import { useLogout } from '@/hooks';
import Image from 'next/image';

interface SidebarProps {
  className?: string;
  isCollapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ className, isCollapsed, onToggle }: SidebarProps) {
  const pathname = usePathname();
  const { user } = useAuthStore();
  const logout = useLogout();

  const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { href: '/documents', label: 'Documents', icon: FileText },
    { href: '/library', label: 'Library', icon: Library },
    { href: '/settings', label: 'Settings', icon: Settings },
    { href: '/profile', label: 'Profile', icon: User },
  ];

  const handleLogout = () => {
    logout.mutate();
  };

  return (
    <aside
      className={cn(
        'flex h-screen flex-col border-r border-brand-500/10 bg-black transition-all duration-300 fixed left-0 top-0 z-40',
        isCollapsed ? 'w-20' : 'w-64',
        className
      )}
    >
      {/* Logo Area */}
      <div className={cn("flex items-center h-20 px-6 border-b border-brand-500/10", isCollapsed ? "justify-center px-0" : "justify-between")}>
        {!isCollapsed && (
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
            <span className="font-bold text-lg tracking-tight text-white">VeriVox</span>
          </div>
        )}
        {isCollapsed && (
          <div className="relative size-10 rounded-lg overflow-hidden bg-brand-500 flex items-center justify-center">
            <Image
              src="/logo.png"
              alt="VeriVox Logo"
              width={32}
              height={32}
              className="object-cover opacity-90 mix-blend-multiply"
            />
          </div>
        )}

        {!isCollapsed && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggle}
            className="text-brand-100/40 hover:text-white"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Toggle button when collapsed */}
      {isCollapsed && (
        <div className="flex justify-center p-2 border-b border-brand-500/10">
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggle}
            className="text-brand-100/40 hover:text-white"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 space-y-2 p-4 mt-4 overflow-y-auto scrollbar-thin scrollbar-thumb-brand-500/10 scrollbar-track-transparent">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              'flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-200 group',
              pathname === item.href
                ? 'bg-brand-500/10 text-brand-500 shadow-lg shadow-brand-500/5'
                : 'text-brand-100/60 hover:bg-white/5 hover:text-white',
              isCollapsed && 'justify-center px-2'
            )}
            title={isCollapsed ? item.label : undefined}
          >
            <item.icon className={cn("h-5 w-5 shrink-0 transition-colors", pathname === item.href ? "text-brand-500" : "text-brand-100/40 group-hover:text-white")} />
            {!isCollapsed && <span>{item.label}</span>}

            {/* Active Indicator */}
            {!isCollapsed && pathname === item.href && (
              <div className="ml-auto w-1.5 h-1.5 rounded-full bg-brand-500 shadow-[0_0_8px_rgba(34,197,94,0.8)]" />
            )}
          </Link>
        ))}
      </nav>

      {/* User Profile */}
      <div className="p-4 border-t border-brand-500/10 bg-black/50">
        <div className={cn("flex items-center gap-3 rounded-xl p-2 transition-colors hover:bg-white/5", isCollapsed ? "justify-center" : "")}>
          <div className="h-10 w-10 shrink-0 rounded-full bg-linear-to-br from-brand-400 to-brand-600 flex items-center justify-center border border-brand-500/30 text-black font-bold shadow-lg shadow-brand-500/20">
            {user?.display_name ? user.display_name[0].toUpperCase() : 'U'}
          </div>

          {!isCollapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">
                {user?.display_name || 'User'}
              </p>
              <p className="text-xs text-brand-100/40 truncate">
                {user?.email || 'user@example.com'}
              </p>
            </div>
          )}

          {!isCollapsed && (
            <Button
              variant="ghost"
              size="icon"
              onClick={handleLogout}
              className="text-brand-100/40 hover:text-red-400 hover:bg-red-500/10"
              title="Log out"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </aside>
  );
}

'use client';

import * as React from 'react';
import { AppLayout } from '@/components/layout';
import { Card } from '@/components/ui';
import { User } from 'lucide-react';
import { useAuthStore } from '@/stores';

export default function ProfilePage() {
  const { user } = useAuthStore();

  return (
    <AppLayout>
      <div className="min-h-screen bg-black text-white p-8">
        <h1 className="text-3xl font-bold mb-6">Profile</h1>
        <Card className="p-8 border-brand-500/10 bg-brand-950/10 backdrop-blur-sm">
          <div className="flex items-center gap-6 mb-8">
            <div className="h-24 w-24 rounded-full bg-brand-500/20 flex items-center justify-center border border-brand-500/30 text-brand-500 text-3xl font-bold">
              {user?.display_name ? user.display_name[0].toUpperCase() : 'U'}
            </div>
            <div>
              <h2 className="text-2xl font-semibold text-white">{user?.display_name || 'User'}</h2>
              <p className="text-brand-100/60">{user?.email}</p>
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <div className="p-4 rounded-xl bg-white/5 border border-white/5">
              <h3 className="text-sm font-medium text-brand-500 mb-1">Account Type</h3>
              <p className="text-lg">Free Plan</p>
            </div>
            <div className="p-4 rounded-xl bg-white/5 border border-white/5">
              <h3 className="text-sm font-medium text-brand-500 mb-1">Member Since</h3>
              <p className="text-lg">Feb 2026</p>
            </div>
          </div>
        </Card>
      </div>
    </AppLayout>
  );
}

'use client';

import * as React from 'react';
import { AppLayout } from '@/components/layout';
import { Card } from '@/components/ui';
import { Settings } from 'lucide-react';

export default function SettingsPage() {
    return (
        <AppLayout>
            <div className="min-h-screen bg-black text-white p-8">
                <h1 className="text-3xl font-bold mb-6">Settings</h1>
                <Card className="p-8 border-brand-500/10 bg-brand-950/10 backdrop-blur-sm text-center">
                    <Settings className="mx-auto h-12 w-12 text-brand-500/50 mb-4" />
                    <h2 className="text-xl font-semibold mb-2">Account Settings</h2>
                    <p className="text-brand-100/60 max-w-md mx-auto">
                        Manage your account preferences, notifications, and security settings here. Coming soon.
                    </p>
                </Card>
            </div>
        </AppLayout>
    );
}

'use client';

import * as React from 'react';
import { AppLayout } from '@/components/layout';
import { Card } from '@/components/ui';
import { ShieldCheck } from 'lucide-react';

export default function ProofsPage() {
    return (
        <AppLayout>
            <div className="min-h-screen bg-black text-white p-8">
                <h1 className="text-3xl font-bold mb-6">Blockchain Proofs</h1>
                <Card className="p-8 border-brand-500/10 bg-brand-950/10 backdrop-blur-sm text-center">
                    <ShieldCheck className="mx-auto h-12 w-12 text-brand-500/50 mb-4" />
                    <h2 className="text-xl font-semibold mb-2">Immutable Verification</h2>
                    <p className="text-brand-100/60 max-w-md mx-auto">
                        View and verify the blockchain proofs for your documents and sessions. This feature provides a permanent, tamper-proof record of your interactions.
                        <br /><br />
                        Coming soon.
                    </p>
                </Card>
            </div>
        </AppLayout>
    );
}

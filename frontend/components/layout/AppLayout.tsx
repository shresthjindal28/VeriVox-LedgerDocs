'use client';

import * as React from 'react';
import { Sidebar } from './sidebar';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/stores';
import { useRouter } from 'next/navigation';
import { LoadingOverlay } from '@/components/ui';

interface AppLayoutProps {
    children: React.ReactNode;
    className?: string; // Allow passing className to wrapper for flexibility
}

export function AppLayout({ children, className }: AppLayoutProps) {
    const { isAuthenticated, isInitialized } = useAuthStore();
    const router = useRouter();
    const [isSidebarCollapsed, setSidebarCollapsed] = React.useState(false);

    React.useEffect(() => {
        if (isInitialized && !isAuthenticated) {
            router.push('/login');
        }
    }, [isAuthenticated, isInitialized, router]);

    if (!isInitialized) {
        return <LoadingOverlay message="Initializing..." />;
    }

    if (!isAuthenticated) {
        return null;
    }

    return (
        <div className="flex min-h-screen bg-black">
            <Sidebar
                isCollapsed={isSidebarCollapsed}
                onToggle={() => setSidebarCollapsed(!isSidebarCollapsed)}
            />
            <main
                className={cn(
                    "flex-1 min-h-screen transition-all duration-300 relative bg-black overflow-x-hidden",
                    isSidebarCollapsed ? "ml-20" : "ml-64",
                    className
                )}
            >
                {/* Abstract background elements could go here if global */}
                {children}
            </main>
        </div >
    );
}

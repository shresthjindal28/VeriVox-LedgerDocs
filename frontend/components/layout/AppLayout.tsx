'use client';

import * as React from 'react';
import { Sidebar } from './sidebar';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/stores';
import { useRouter } from 'next/navigation';
import { LoadingOverlay } from '@/components/ui';

interface AppLayoutProps {
    children: React.ReactNode;
    className?: string; // Applied to the main content area
    layoutMode?: 'default' | 'fullscreen';
}

export function AppLayout({ children, className, layoutMode = 'default' }: AppLayoutProps) {
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
        <div className={cn(
            "flex bg-black",
            layoutMode === 'fullscreen' ? "h-screen overflow-hidden" : "min-h-screen"
        )}>
            <Sidebar
                isCollapsed={isSidebarCollapsed}
                onToggle={() => setSidebarCollapsed(!isSidebarCollapsed)}
            />
            <main
                className={cn(
                    "flex-1 transition-all duration-300 relative bg-black",
                    isSidebarCollapsed ? "ml-20" : "ml-64",
                    layoutMode === 'fullscreen' ? "h-full overflow-hidden" : "min-h-screen overflow-x-hidden",
                    className
                )}
            >
                {/* Abstract background elements could go here if global */}
                {children}
            </main>
        </div >
    );
}

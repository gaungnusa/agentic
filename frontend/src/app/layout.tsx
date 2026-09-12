import type { Metadata } from 'next';
import './globals.css';
import { EntityProvider } from '@/context/EntityContext';
import { AuthProvider } from '@/context/AuthContext';
import { ChatProvider } from '@/context/ChatContext';
import ChatHeader from '@/components/ChatHeader';

export const metadata: Metadata = {
  title: 'Batu Networks ERP - Agentic AI Platform',
  description: 'Enterprise ERP AI Extension Layer — Chat-First Interface',
  icons: {
    icon: '/favicon.ico',
    shortcut: '/favicon.ico',
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="id" suppressHydrationWarning>
      <body suppressHydrationWarning className="bg-slate-950 text-slate-100 min-h-screen antialiased">
        <EntityProvider>
          <AuthProvider>
            <ChatProvider>
              {/* Minimal Header — always visible */}
              <ChatHeader />

              {/* Full-bleed content (chat or HITL/audit pages) */}
              <main>
                {children}
              </main>
            </ChatProvider>
          </AuthProvider>
        </EntityProvider>
      </body>
    </html>
  );
}
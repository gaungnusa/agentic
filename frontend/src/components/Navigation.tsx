'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import UserPersonaDropdown from '@/components/UserPersonaDropdown';

interface AgentNavItem {
  id: string;
  label: string;
  route: string;
  allowedRoles: string[];
}

const AGENT_NAV_ITEMS: AgentNavItem[] = [
  { id: 'agent_1', label: 'A1: Quote', route: '/agents/agent-1', allowedRoles: ['purchasing', 'admin'] },
  { id: 'agent_2', label: 'A2: Margin', route: '/agents/agent-2', allowedRoles: ['purchasing', 'admin'] },
  { id: 'agent_3', label: 'A3: Backlog', route: '/agents/agent-3', allowedRoles: ['sales', 'admin'] },
  { id: 'agent_4', label: 'A4: Renewal', route: '/agents/agent-4', allowedRoles: ['purchasing', 'admin'] },
  { id: 'agent_5', label: 'A5: Vendor', route: '/agents/agent-5', allowedRoles: ['purchasing', 'admin'] },
  { id: 'agent_6', label: 'A6: GR Split', route: '/agents/agent-6', allowedRoles: ['warehouse', 'admin'] },
  { id: 'agent_7', label: 'A7: Triangle', route: '/agents/agent-7', allowedRoles: ['warehouse', 'admin'] },
  { id: 'agent_8', label: 'A8: Bank FX', route: '/agents/agent-8', allowedRoles: ['treasury', 'admin'] },
  { id: 'agent_9', label: 'A9: Cash', route: '/agents/agent-9', allowedRoles: ['treasury', 'admin'] },
];

export default function Navigation() {
  const pathname = usePathname();
  const { user } = useAuth();
  const currentRole = user?.role || 'operator';

  return (
    <nav className="bg-white border-b border-slate-200 px-4 md:px-6 py-2.5 text-xs font-semibold text-slate-600 flex flex-wrap justify-between items-center gap-3 sticky top-0 z-40">
      <div className="flex items-center gap-4 overflow-x-auto py-1 max-w-full">
        <Link
          href="/"
          className={`font-black tracking-wider uppercase text-[11px] transition flex items-center gap-1.5 shrink-0 ${
            pathname === '/' ? 'text-blue-700 bg-blue-50/80 px-2 py-1 rounded' : 'text-slate-900 hover:text-blue-600'
          }`}
        >
          Command Center
        </Link>
        <div className="flex items-center gap-2 shrink-0">
          <Link
            href="/hitl"
            className={`transition flex items-center gap-1.5 font-bold px-2.5 py-1 rounded border ${
              pathname === '/hitl'
                ? 'text-blue-700 bg-blue-100/70 border-blue-300 shadow-xs'
                : 'text-blue-700 bg-blue-50 hover:bg-blue-100/50 border-blue-200'
            }`}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-pulse"></span>
            <span>HITL Gateway</span>
          </Link>
          <Link
            href="/audit"
            className={`transition px-2.5 py-1 rounded font-semibold ${
              pathname === '/audit'
                ? 'text-purple-700 bg-purple-100/70 border border-purple-300'
                : 'text-purple-700 hover:text-purple-900'
            }`}
          >
            Audit Trail
          </Link>
          <span className="text-slate-300">|</span>

          {/* Dynamic Role-Aware Agents */}
          {AGENT_NAV_ITEMS.map((item) => {
            const isAuthorized = currentRole === 'admin' || currentRole === 'auditor' || item.allowedRoles.includes(currentRole);
            const isActive = pathname === item.route;

            return (
              <Link
                key={item.id}
                href={item.route}
                className={`transition px-2 py-1 rounded relative flex items-center gap-1 shrink-0 ${
                  isActive
                    ? 'bg-slate-900 text-white font-bold'
                    : isAuthorized
                    ? 'text-slate-800 hover:text-blue-600 font-bold bg-slate-50 border border-slate-200 hover:border-blue-300'
                    : 'text-slate-400 hover:text-slate-600 font-medium'
                }`}
                title={
                  isAuthorized
                    ? `${item.label} (Hak Otorisasi Penuh untuk ${currentRole})`
                    : `${item.label} (Mode Eksplorasi/Simulasi - Khusus ${item.allowedRoles.join(', ')})`
                }
              >
                {isAuthorized && currentRole !== 'admin' && currentRole !== 'auditor' && (
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block"></span>
                )}
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>
      </div>

      <div className="flex items-center gap-3 shrink-0">
        <div className="text-[11px] text-slate-400 font-mono hidden md:block">
          FastAPI: <span className="text-emerald-600 font-bold">:8000</span>
        </div>
        <UserPersonaDropdown />
      </div>
    </nav>
  );
}

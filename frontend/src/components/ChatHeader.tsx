'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEntity } from '@/context/EntityContext';
import { useAuth } from '@/context/AuthContext';
import { useChat } from '@/context/ChatContext';
import UserPersonaDropdown from '@/components/UserPersonaDropdown';

export default function ChatHeader() {
  const pathname = usePathname();
  const { entity, setEntity } = useEntity();
  const { user } = useAuth();
  const { clearChat } = useChat();
  const [hasImageError, setHasImageError] = useState(false);

  return (
    <header className="h-16 bg-slate-900/95 backdrop-blur-xl border-b border-slate-800/80 px-4 md:px-6 flex items-center justify-between sticky top-0 z-50">
      {/* Left: Logo + Brand */}
      <div className="flex items-center gap-4">
        <Link href="/" className="flex items-center gap-2.5 group" onClick={() => { if (pathname === '/') clearChat(); }}>
          {!hasImageError ? (
            <img
              src="/batu.PNG"
              alt="Batu Networks"
              className="h-7 w-auto object-contain"
              onError={() => setHasImageError(true)}
            />
          ) : (
            <div className="h-7 px-2 bg-gradient-to-r from-blue-600 to-indigo-700 rounded flex items-center justify-center text-white font-extrabold text-[10px] tracking-wider">
              BATU
            </div>
          )}
          <div className="hidden sm:block">
            <div className="text-sm font-bold text-white tracking-tight group-hover:text-blue-400 transition">
              Agentic AI
            </div>
          </div>
        </Link>

        {/* Nav Links (HITL + Audit only) */}
        <div className="flex items-center gap-1 ml-2 pl-3 border-l border-slate-800">
          <Link
            href="/"
            className={`px-2.5 py-1 rounded-md text-[11px] font-bold transition ${
              pathname === '/'
                ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            💬 Chat
          </Link>
          <Link
            href="/hitl"
            className={`px-2.5 py-1 rounded-md text-[11px] font-bold transition flex items-center gap-1.5 ${
              pathname === '/hitl'
                ? 'bg-amber-600/20 text-amber-400 border border-amber-500/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
            HITL
          </Link>
          <Link
            href="/audit"
            className={`px-2.5 py-1 rounded-md text-[11px] font-bold transition ${
              pathname === '/audit'
                ? 'bg-purple-600/20 text-purple-400 border border-purple-500/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            Audit
          </Link>
        </div>
      </div>

      {/* Right: Entity + User */}
      <div className="flex items-center gap-3 text-xs">
        {/* Entity Selector */}
        <div className="flex items-center gap-1.5 bg-slate-800/60 border border-slate-700/60 px-2.5 py-1.5 rounded-lg">
          <span className="text-slate-500 font-semibold hidden sm:inline">Entity:</span>
          <select
            value={entity}
            onChange={(e) => setEntity(e.target.value as any)}
            className="bg-transparent font-bold text-slate-200 focus:outline-none cursor-pointer text-[11px]"
          >
            <option value="SG">SG — Singapore HQ</option>
            <option value="VN">VN — Vietnam SSC</option>
            <option value="KR">KR — Korea Branch</option>
            <option value="IN">IN — India Office</option>
            <option value="JP">JP — Japan Office</option>
          </select>
        </div>

        {/* User Persona */}
        <UserPersonaDropdown />
      </div>
    </header>
  );
}

'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';

export default function UserPersonaDropdown() {
  const { user, switchPersona, demoPersonas, loading } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const roleColors: Record<string, string> = {
    purchasing: 'bg-emerald-900/40 text-emerald-400 border-emerald-700/50',
    sales: 'bg-blue-900/40 text-blue-400 border-blue-700/50',
    warehouse: 'bg-amber-900/40 text-amber-400 border-amber-700/50',
    treasury: 'bg-indigo-900/40 text-indigo-400 border-indigo-700/50',
    auditor: 'bg-purple-900/40 text-purple-400 border-purple-700/50',
    admin: 'bg-rose-900/40 text-rose-400 border-rose-700/50',
  };

  const roleIcons: Record<string, string> = {
    purchasing: '🛒',
    sales: '💼',
    warehouse: '📦',
    treasury: '🏦',
    auditor: '⚖️',
    admin: '🛡️',
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-2.5 py-1.5 bg-slate-800/60 hover:bg-slate-700/80 border border-slate-700/60 hover:border-slate-600 rounded-lg text-xs font-semibold text-slate-300 transition"
      >
        <span>{roleIcons[user.role] || '👤'}</span>
        <div className="text-left hidden sm:block">
          <div className="text-[11px] font-bold text-slate-200 leading-none">{user.full_name}</div>
          <div className="text-[9px] text-slate-500 font-mono capitalize">
            {user.role} &bull; {user.entity_code}
          </div>
        </div>
        <span className="text-[10px] text-slate-500">&#9662;</span>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-72 bg-slate-800 rounded-xl shadow-2xl shadow-black/40 border border-slate-700/60 py-2 z-50">
          <div className="px-3 py-1.5 border-b border-slate-700/50 text-[11px] font-bold text-slate-400 uppercase tracking-wider flex justify-between items-center">
            <span>Beralih Persona RBAC</span>
            {loading && <span className="text-blue-400 animate-spin">&#8635;</span>}
          </div>

          <div className="py-1">
            {demoPersonas.map((p) => {
              const isSelected = p.username === user.username;
              return (
                <button
                  key={p.username}
                  onClick={() => {
                    switchPersona(p.username);
                    setIsOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2 flex items-center justify-between hover:bg-slate-700/60 transition text-xs ${
                    isSelected ? 'bg-blue-900/20 border-l-2 border-blue-500' : ''
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span>{roleIcons[p.role] || '👤'}</span>
                    <div>
                      <div className="font-bold text-slate-200 text-[11px]">{p.full_name}</div>
                      <div className="text-[10px] text-slate-500">{p.email}</div>
                    </div>
                  </div>
                  <span
                    className={`px-1.5 py-0.5 rounded text-[9px] font-bold border uppercase tracking-wider ${
                      roleColors[p.role] || 'bg-slate-700 text-slate-400 border-slate-600'
                    }`}
                  >
                    {p.role}
                  </span>
                </button>
              );
            })}
          </div>

          <div className="px-3 pt-2 border-t border-slate-700/50 text-[10px] text-slate-500">
            Peran menentukan otorisasi eksekusi approval di gateway HITL.
          </div>
        </div>
      )}
    </div>
  );
}

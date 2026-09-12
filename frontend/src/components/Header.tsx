'use client';

import React, { useState, useEffect } from 'react';
import { useEntity } from '@/context/EntityContext';
import { useAuth } from '@/context/AuthContext';

interface HeaderProps {
  title: string;
  agentTag?: string;
  subTitle: string;
  moduleCode?: string;
}

export default function Header({ title, agentTag = 'Active', subTitle, moduleCode }: HeaderProps) {
  const { entity, setEntity } = useEntity();
  const { user } = useAuth();
  const [timestamp, setTimestamp] = useState('');
  const [hasImageError, setHasImageError] = useState(false);

  useEffect(() => {
    setTimestamp(new Date().toLocaleString('id-ID', { dateStyle: 'medium', timeStyle: 'short' }) + ' WITA');
  }, []);

  const currentRole = user?.role || 'operator';

  return (
    <header className="bg-white border border-slate-200 rounded-xl p-4 mb-6 shadow-sm flex flex-col md:flex-row justify-between items-center gap-4">
      <div className="flex items-center gap-5">
        <div className="flex items-center gap-3 pr-5 border-r border-slate-200">
          {!hasImageError ? (
            <img 
              src="/batu.PNG" 
              alt="Batu Networks" 
              className="h-9 w-auto object-contain"
              onError={() => setHasImageError(true)}
            />
          ) : (
            <div className="h-9 px-2.5 bg-gradient-to-r from-blue-700 to-indigo-800 rounded-md flex items-center justify-center text-white font-extrabold text-[11px] tracking-wider shadow-sm select-none">
              BATU NETWORKS
            </div>
          )}
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-base font-bold text-slate-900 tracking-tight">{title}</h1>
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-200">
              {agentTag}
            </span>
          </div>
          <p className="text-xs text-slate-500 font-medium flex items-center gap-2 mt-0.5">
            <span className="flex items-center gap-1.5 text-emerald-600 font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              {subTitle}
            </span>
            {moduleCode && (
              <>
                <span className="text-slate-300">|</span>
                <span>{moduleCode}</span>
              </>
            )}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3 text-xs">
        {/* User Persona & Role Badge */}
        {user && (
          <div className="hidden lg:flex items-center gap-2 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg shadow-sm">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span className="text-slate-400 font-semibold">User:</span>
            <span className="font-bold text-slate-800">{user.full_name}</span>
            <span className="px-1.5 py-0.5 rounded bg-blue-100 text-blue-800 text-[10px] font-bold uppercase tracking-wider">
              {currentRole}
            </span>
          </div>
        )}

        {/* Entity Selector Switcher */}
        <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg shadow-sm">
          <span className="text-slate-400 font-semibold">Branch:</span>
          <select 
            value={entity} 
            onChange={(e) => setEntity(e.target.value as any)}
            className="bg-transparent font-bold text-slate-800 focus:outline-none cursor-pointer"
          >
            <option value="SG">Singapore HQ (SGD/USD)</option>
            <option value="VN">Vietnam SSC (VND)</option>
            <option value="KR">Korea Branch (KRW)</option>
            <option value="IN">India Back-Office (INR)</option>
            <option value="JP">Japan Office (JPY)</option>
          </select>
        </div>

        {/* Live Clock Badge */}
        <div className="bg-slate-50 border border-slate-200 px-3 py-2 rounded-lg text-slate-600 flex items-center gap-2 shadow-sm">
          <span className="text-slate-400">&#128339;</span>
          <span>Last Updated: <strong className="text-slate-800 font-semibold">{timestamp}</strong></span>
        </div>
      </div>
    </header>
  );
}
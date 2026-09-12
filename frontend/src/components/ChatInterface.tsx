'use client';

import React, { useRef, useEffect } from 'react';
import { useChat } from '@/context/ChatContext';
import { useEntity } from '@/context/EntityContext';
import { useAuth } from '@/context/AuthContext';
import ChatMessage from '@/components/ChatMessage';
import ChatInput from '@/components/ChatInput';

export default function ChatInterface() {
  const { messages, isLoading, sendMessage, clearChat } = useChat();
  const { entity } = useEntity();
  const { user } = useAuth();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [messages]);

  const handleSend = (message: string) => {
    sendMessage(message, entity);
  };

  const handleSuggestionClick = (text: string) => {
    sendMessage(text, entity);
  };

  const currentRole = user?.role || 'operator';

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950">
      {/* Chat Message Stream */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto scroll-smooth">
        {messages.length === 0 ? (
          <WelcomeScreen onSuggestionClick={handleSuggestionClick} entity={entity} role={currentRole} userName={user?.full_name} />
        ) : (
          <div className="max-w-4xl mx-auto py-6 space-y-1">
            {messages.map((msg) => (
              <ChatMessage
                key={msg.id}
                message={msg}
                onSuggestionClick={handleSuggestionClick}
              />
            ))}
          </div>
        )}
      </div>

      {/* Input Bar */}
      <ChatInput onSend={handleSend} disabled={isLoading} />
    </div>
  );
}

// ============================================================
// Welcome Screen (Shown when no messages)
// ============================================================
interface WelcomeProps {
  onSuggestionClick: (text: string) => void;
  entity: string;
  role?: string;
  userName?: string;
}

function getRoleSuggestions(role: string = 'purchasing', entity: string) {
  const r = role.toLowerCase();
  if (r === 'purchasing') {
    return [
      { label: '🏷️ Carikan Harga SFP', prompt: 'Carikan harga SFP-10G-LR' },
      { label: '📊 Validasi Margin PO', prompt: 'Cek margin PO-2026-4412' },
      { label: '⏰ Radar Validitas Harga', prompt: 'Cek radar validitas harga' },
      { label: '🏭 Evaluasi Vendor', prompt: `Evaluasi semua vendor entitas ${entity}` },
      { label: '📋 Antrean Approval', prompt: 'Tampilkan draf menunggu approval' },
      { label: '📦 Katalog Suku Cadang', prompt: 'Daftar part' },
      { label: '📄 Daftar Purchase Order', prompt: 'Daftar PO' },
      { label: '📜 Riwayat Audit', prompt: `Lihat riwayat audit trail ${entity}` },
    ];
  } else if (r === 'sales') {
    return [
      { label: '🚚 Backlog Pengiriman SO', prompt: 'Cek backlog pengiriman SO-2026-4401' },
      { label: '⏱️ Evaluasi Risiko RDD', prompt: `Evaluasi keterlambatan pengiriman ${entity}` },
      { label: '📋 Antrean Approval Sales', prompt: 'Tampilkan draf menunggu approval' },
      { label: '📦 Cek Stok Katalog', prompt: 'Daftar part' },
      { label: '🏢 Pindah Entitas ke VN', prompt: 'Pindah ke entitas VN' },
      { label: '📜 Riwayat Audit', prompt: `Lihat riwayat audit trail ${entity}` },
    ];
  } else if (r === 'warehouse') {
    return [
      { label: '📦 Penerimaan Barang (GR)', prompt: 'Cek GR PO-2026-9902' },
      { label: '🚢 Triangle Trade POD', prompt: 'Verifikasi POD triangle trade' },
      { label: '⏳ Cek Pinjaman Stok', prompt: 'Cek pinjaman stok aktif' },
      { label: '📋 Antrean Approval Gudang', prompt: 'Tampilkan draf menunggu approval' },
      { label: '📄 Cek Purchase Order', prompt: 'Daftar PO' },
      { label: '📜 Riwayat Audit', prompt: `Lihat riwayat audit trail ${entity}` },
    ];
  } else if (r === 'treasury') {
    return [
      { label: '💵 Cek Runway Kas', prompt: `Cek runway kas operasional ${entity}` },
      { label: '🏦 Rekonsiliasi FX Bank', prompt: 'Rekonsiliasi TXN-DBS-88319' },
      { label: '📉 Analisis Likuiditas', prompt: `Analisis likuiditas kas ${entity}` },
      { label: '📋 Antrean Approval Treasury', prompt: 'Tampilkan draf menunggu approval' },
      { label: '🏢 Pindah Entitas ke SG', prompt: 'Pindah ke entitas SG' },
      { label: '📜 Riwayat Audit', prompt: `Lihat riwayat audit trail ${entity}` },
    ];
  } else if (r === 'auditor') {
    return [
      { label: '📜 Lihat Audit Trail', prompt: `Lihat riwayat audit trail ${entity}` },
      { label: '🔒 Verifikasi Hash Log', prompt: 'Verifikasi integritas log HITL' },
      { label: '📋 Antrean Keputusan HITL', prompt: 'Tampilkan draf menunggu approval' },
      { label: '🔍 Audit Rekonsiliasi Bank', prompt: 'Rekonsiliasi TXN-DBS-88319' },
      { label: '🏢 Cek Audit Entitas VN', prompt: 'Pindah ke entitas VN' },
      { label: '📊 Audit Margin Pembelian', prompt: 'Cek margin PO-2026-4412' },
    ];
  } else {
    // Admin / Superuser
    return [
      { label: '💵 Cek Cash Flow', prompt: `Cek runway kas operasional ${entity}` },
      { label: '📋 Antrean HITL', prompt: 'Tampilkan draf menunggu approval' },
      { label: '🏭 Evaluasi Vendor', prompt: `Evaluasi semua vendor entitas ${entity}` },
      { label: '🚚 Backlog SO', prompt: 'Cek backlog pengiriman SO-2026-4401' },
      { label: '📊 Validasi Margin', prompt: 'Cek margin PO-2026-4412' },
      { label: '📦 Pinjaman Stok', prompt: 'Cek pinjaman stok aktif' },
      { label: '🏦 Rekonsiliasi FX', prompt: 'Rekonsiliasi TXN-DBS-88319' },
      { label: '📜 Audit Trail', prompt: `Lihat riwayat audit trail ${entity}` },
    ];
  }
}

const ROLE_DESCRIPTIONS: Record<string, string> = {
  purchasing: '🛒 Wewenang: RFQ Dynamic Costing, Validasi Margin PO, Price Radar, dan Evaluasi Vendor',
  sales: '💼 Wewenang: Sales Order Backlog, Analisa Delay RDD & Risiko Keterlambatan Pengiriman',
  warehouse: '📦 Wewenang: Goods Receipt Damaged Split, Triangle Trade POD, dan Pinjaman Stok Antar-Entitas',
  treasury: '🏦 Wewenang: Runway Kas Likuiditas, Multi-Currency Bank FX, dan Otorisasi Treasury',
  auditor: '⚖️ Wewenang: Audit Trail Kepatuhan, Verifikasi Hash Kriptografi, dan Review Keputusan HITL',
  admin: '🛡️ Wewenang: Otoritas Penuh Seluruh Modul ERP, Eksekusi Agen, dan Tata Kelola Sistem',
};

function WelcomeScreen({ onSuggestionClick, entity, role, userName }: WelcomeProps) {
  const currentRole = (role || 'purchasing').toLowerCase();
  const suggestions = getRoleSuggestions(currentRole, entity);
  const roleDesc = ROLE_DESCRIPTIONS[currentRole] || ROLE_DESCRIPTIONS.admin;

  return (
    <div className="flex flex-col items-center justify-center h-full px-6 py-12">
      <div className="text-center space-y-6 max-w-2xl">
        {/* Logo + Title */}
        <div className="space-y-3">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-700 shadow-xl shadow-blue-600/20 mb-2">
            <span className="text-3xl">🤖</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-black text-white tracking-tight">
            Batu Networks Agentic AI
          </h1>
          <p className="text-sm text-slate-400 leading-relaxed max-w-md mx-auto">
            Selamat datang, <span className="text-blue-400 font-semibold">{userName || 'Operator'}</span>.
            Konteks entitas aktif: <span className="text-emerald-400 font-bold">{entity}</span>.
          </p>
          <div className="inline-block px-3 py-1 bg-slate-800/80 border border-slate-700/60 rounded-full text-[11px] text-slate-300 font-medium">
            {roleDesc}
          </div>
        </div>

        {/* Quick Action Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-4">
          {suggestions.map((s, i) => (
            <button
              key={i}
              onClick={() => onSuggestionClick(s.prompt)}
              className="group bg-slate-800/60 hover:bg-slate-700/80 border border-slate-700/60 hover:border-blue-500/40 rounded-xl px-3 py-3 text-left transition-all shadow-sm hover:shadow-md hover:shadow-blue-900/10"
            >
              <div className="text-sm font-bold text-slate-200 group-hover:text-white transition-colors">
                {s.label}
              </div>
              <div className="text-[10px] text-slate-500 group-hover:text-slate-400 mt-1 leading-tight truncate transition-colors">
                {s.prompt}
              </div>
            </button>
          ))}
        </div>

        {/* Capabilities Badges */}
        <div className="flex flex-wrap items-center justify-center gap-2 pt-4">
          <span className="px-2.5 py-1 rounded-full bg-slate-800/60 border border-slate-700/50 text-[10px] font-semibold text-slate-400">
            🔒 RBAC: {currentRole.toUpperCase()}
          </span>
          <span className="px-2.5 py-1 rounded-full bg-slate-800/60 border border-slate-700/50 text-[10px] font-semibold text-slate-400">
            🏢 Entity: {entity}
          </span>
          <span className="px-2.5 py-1 rounded-full bg-slate-800/60 border border-slate-700/50 text-[10px] font-semibold text-slate-400">
            ✅ 100% HITL Governance
          </span>
          <span className="px-2.5 py-1 rounded-full bg-slate-800/60 border border-slate-700/50 text-[10px] font-semibold text-slate-400">
            📜 Immutable Audit Trail
          </span>
        </div>
      </div>
    </div>
  );
}

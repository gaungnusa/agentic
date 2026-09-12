'use client';

import React from 'react';
import type { ChatMessage as ChatMessageType } from '@/context/ChatContext';
import Link from 'next/link';

interface ChatMessageProps {
  message: ChatMessageType;
  onSuggestionClick?: (text: string) => void;
  onApprove?: (draftId: string) => void;
}

const AGENT_LABELS: Record<string, { name: string; color: string; icon: string }> = {
  agent_1: { name: 'Quotation Assistant', color: 'from-blue-500 to-blue-700', icon: '💰' },
  agent_2: { name: 'Margin Pre-Checker', color: 'from-amber-500 to-amber-700', icon: '📊' },
  agent_3: { name: 'Backlog Narrator', color: 'from-orange-500 to-red-600', icon: '🚚' },
  agent_5: { name: 'Vendor Advisor', color: 'from-indigo-500 to-indigo-700', icon: '🏭' },
  agent_6: { name: 'GR Handler', color: 'from-rose-500 to-rose-700', icon: '📦' },
  agent_7: { name: 'Triangle & Stock', color: 'from-purple-500 to-purple-700', icon: '🔺' },
  agent_8: { name: 'FX Reconciler', color: 'from-emerald-500 to-emerald-700', icon: '🏦' },
  agent_9: { name: 'Cash Flow Radar', color: 'from-teal-500 to-teal-700', icon: '💵' },
};

export default function ChatMessage({ message, onSuggestionClick, onApprove }: ChatMessageProps) {
  if (message.isLoading) {
    return (
      <div className="flex items-start gap-3 px-4 py-3">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center text-white text-xs font-bold shadow-lg shrink-0">
          AI
        </div>
        <div className="flex items-center gap-1.5 mt-2">
          <span className="w-2 h-2 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '0ms' }} />
          <span className="w-2 h-2 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '150ms' }} />
          <span className="w-2 h-2 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    );
  }

  if (message.role === 'user') {
    return (
      <div className="flex items-start gap-3 px-4 py-3 justify-end">
        <div className="max-w-[75%] bg-blue-600 text-white px-4 py-2.5 rounded-2xl rounded-br-md text-sm leading-relaxed shadow-md">
          {message.content}
        </div>
        <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-white text-xs font-bold shrink-0 shadow">
          U
        </div>
      </div>
    );
  }

  // Assistant message
  const agent = message.agent_used ? AGENT_LABELS[message.agent_used] : null;
  const richCard = message.rich_card;

  return (
    <div className="flex items-start gap-3 px-4 py-3">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center text-white text-xs font-bold shadow-lg shrink-0">
        AI
      </div>
      <div className="flex-1 max-w-[85%] space-y-3">
        {/* Agent Badge */}
        {agent && (
          <div className="flex items-center gap-2">
            <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full text-white bg-gradient-to-r ${agent.color} shadow-sm`}>
              {agent.icon} {agent.name}
            </span>
          </div>
        )}

        {/* Text Content */}
        <div className="bg-slate-800/80 backdrop-blur-sm border border-slate-700/60 text-slate-100 px-4 py-3 rounded-2xl rounded-bl-md text-sm leading-relaxed shadow-lg">
          <div className="whitespace-pre-wrap">{renderMarkdown(message.content)}</div>
        </div>

        {/* Rich Card: Agent Result */}
        {richCard?.type === 'agent_result' && (
          <div className="bg-slate-800/60 backdrop-blur border border-slate-700/50 rounded-xl p-4 shadow-lg space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-slate-300 uppercase tracking-wider">
                {richCard.agent_name || 'Agent Analysis'}
              </span>
              {richCard.metrics && (
                <span className="text-[10px] font-mono text-slate-500">Verified Python Engine</span>
              )}
            </div>
            {richCard.metrics && (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {Object.entries(richCard.metrics).map(([key, val]) => (
                  <div key={key} className="bg-slate-900/60 rounded-lg px-3 py-2 border border-slate-700/50">
                    <div className="text-[10px] text-slate-400 font-semibold uppercase truncate">{formatKey(key)}</div>
                    <div className="text-sm font-bold text-white mt-0.5 truncate">{formatValue(val)}</div>
                  </div>
                ))}
              </div>
            )}

            {/* HITL Approval Buttons */}
            {message.requires_hitl && message.draft_action_id && (
              <div className="flex items-center gap-2 pt-2 border-t border-slate-700/50">
                <span className="text-[10px] text-amber-400 font-bold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
                  Menunggu Otorisasi HITL
                </span>
                <div className="ml-auto flex gap-2">
                  <Link
                    href="/hitl"
                    className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-[11px] font-bold shadow transition"
                  >
                    Buka HITL Gateway →
                  </Link>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Rich Card: HITL Queue */}
        {richCard?.type === 'hitl_queue' && richCard.items && (
          <div className="bg-slate-800/60 backdrop-blur border border-slate-700/50 rounded-xl p-4 shadow-lg space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-amber-400 uppercase tracking-wider">
                📋 Antrean HITL ({richCard.entity})
              </span>
              <Link href="/hitl" className="text-[11px] font-bold text-blue-400 hover:text-blue-300 transition">
                Buka Full View →
              </Link>
            </div>
            <div className="space-y-1.5 max-h-48 overflow-y-auto">
              {richCard.items.map((item: any) => (
                <div key={item.id} className="flex items-center gap-2 bg-slate-900/50 rounded-lg px-3 py-2 border border-slate-700/40 text-xs">
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-blue-900/50 text-blue-300 uppercase">
                    {item.agent_id}
                  </span>
                  <span className="font-mono font-bold text-blue-400">{item.ref_doc}</span>
                  <span className="text-slate-500 truncate flex-1">{item.narrative}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Rich Card: Audit Trail */}
        {richCard?.type === 'audit_trail' && richCard.items && (
          <div className="bg-slate-800/60 backdrop-blur border border-slate-700/50 rounded-xl p-4 shadow-lg space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-purple-400 uppercase tracking-wider">
                📜 Audit Trail ({richCard.entity})
              </span>
              <Link href="/audit" className="text-[11px] font-bold text-blue-400 hover:text-blue-300 transition">
                Buka Full View →
              </Link>
            </div>
            <div className="space-y-1.5 max-h-48 overflow-y-auto">
              {richCard.items.map((item: any) => (
                <div key={item.id} className="flex items-center gap-2 bg-slate-900/50 rounded-lg px-3 py-2 border border-slate-700/40 text-xs">
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                    item.action === 'APPROVED' ? 'bg-emerald-900/50 text-emerald-300' :
                    item.action === 'EDITED' ? 'bg-amber-900/50 text-amber-300' :
                    'bg-rose-900/50 text-rose-300'
                  }`}>
                    {item.action}
                  </span>
                  <span className="font-mono font-bold text-blue-400">{item.ref_doc}</span>
                  <span className="text-slate-500">{item.operator}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Rich Card: Vendor List */}
        {richCard?.type === 'vendor_list' && richCard.vendors && (
          <div className="bg-slate-800/60 backdrop-blur border border-slate-700/50 rounded-xl p-4 shadow-lg space-y-2">
            <span className="text-[11px] font-bold text-indigo-400 uppercase tracking-wider">
              🏭 Vendor Performance ({richCard.entity})
            </span>
            <div className="space-y-1.5">
              {richCard.vendors.map((v: any, i: number) => (
                <div key={i} className="flex items-center gap-3 bg-slate-900/50 rounded-lg px-3 py-2.5 border border-slate-700/40 text-xs">
                  <div className="flex-1">
                    <div className="font-bold text-white">{v.vendor_name}</div>
                    <div className="text-[10px] text-slate-400 mt-0.5">
                      Score: <span className={`font-bold ${v.composite_score >= 88 ? 'text-emerald-400' : v.composite_score >= 70 ? 'text-amber-400' : 'text-rose-400'}`}>
                        {v.composite_score}
                      </span>
                      &nbsp;| Tier: <span className="text-slate-300 font-semibold">{v.vendor_tier}</span>
                      &nbsp;| Quota: <span className="text-blue-400 font-semibold">{v.suggested_allocation_pct}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Rich Card: Loan List */}
        {richCard?.type === 'loan_list' && richCard.loans && (
          <div className="bg-slate-800/60 backdrop-blur border border-slate-700/50 rounded-xl p-4 shadow-lg space-y-2">
            <span className="text-[11px] font-bold text-purple-400 uppercase tracking-wider">
              📦 Pinjaman Stok Aktif ({richCard.entity})
            </span>
            <div className="space-y-1.5">
              {richCard.loans.map((loan: any, i: number) => (
                <div key={i} className="flex items-center gap-3 bg-slate-900/50 rounded-lg px-3 py-2.5 border border-slate-700/40 text-xs">
                  <div className="flex-1">
                    <div className="font-bold text-white">{loan.loan_ref} — {loan.partner}</div>
                    <div className="text-[10px] text-slate-400 mt-0.5">
                      Part: <span className="text-slate-300">{loan.part}</span>
                      &nbsp;| Qty: <span className="text-blue-400 font-semibold">{loan.qty}</span>
                      &nbsp;| Sisa: <span className={`font-bold ${loan.days_left <= 5 ? 'text-rose-400' : 'text-emerald-400'}`}>
                        {loan.days_left} hari
                      </span>
                      {loan.is_overdue && <span className="ml-1 text-rose-400 font-bold">⚠️ OVERDUE</span>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Suggested Actions */}
        {message.suggested_actions && message.suggested_actions.length > 0 && (
          <div className="flex flex-wrap gap-2 pt-1">
            {message.suggested_actions.map((action, i) => (
              <button
                key={i}
                onClick={() => onSuggestionClick?.(action)}
                className="px-3 py-1.5 bg-slate-800/60 hover:bg-slate-700/80 border border-slate-600/50 hover:border-blue-500/50 text-slate-300 hover:text-white rounded-full text-[11px] font-semibold transition-all shadow-sm"
              >
                {action}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Helpers
function formatKey(key: string): string {
  return key.replace(/_/g, ' ').replace(/pct$/i, '%').replace(/qty$/i, ' qty');
}

function formatValue(val: any): string {
  if (val === null || val === undefined) return '—';
  if (typeof val === 'boolean') return val ? '✅ Ya' : '❌ Tidak';
  if (typeof val === 'number') {
    if (val >= 1000) return `$${val.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    return val.toFixed(2);
  }
  if (typeof val === 'object') return JSON.stringify(val);
  return String(val);
}

function renderMarkdown(text: string): React.ReactNode {
  // Simple bold markdown rendering
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} className="text-white font-bold">{part.slice(2, -2)}</strong>;
    }
    return <span key={i}>{part}</span>;
  });
}

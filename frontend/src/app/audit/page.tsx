'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Header from '@/components/Header';
import StatCard from '@/components/StatCard';
import { useEntity } from '@/context/EntityContext';

interface AuditLog {
  id: string;
  draft_action_id: string | null;
  operator_id: string;
  entity_code: string;
  event_action: string;
  original_text: string;
  final_dispatched_text: string;
  execution_result: Record<string, any>;
  agent_id: string;
  module_code: string;
  reference_doc: string;
  created_at: string;
}

export default function AuditTrailPage() {
  const { entity } = useEntity();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [filterAction, setFilterAction] = useState<string>('ALL');
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [loading, setLoading] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const fetchAuditLogs = useCallback(async () => {
    try {
      setFetchError(null);
      const res = await fetch(`http://localhost:8000/api/v1/hitl/audit/${entity}`, {
        cache: 'no-store'
      });
      if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);
      const data = await res.json();
      setLogs(data);
    } catch {
      setFetchError('Koneksi ke backend FastAPI gagal. Pastikan port 8000 aktif.');
    }
  }, [entity]);

  useEffect(() => {
    fetchAuditLogs();
    const timer = setInterval(fetchAuditLogs, 5000);
    return () => clearInterval(timer);
  }, [fetchAuditLogs]);

  const filteredLogs = logs.filter((log) => {
    if (filterAction === 'ALL') return true;
    return log.event_action === filterAction;
  });

  const countApproved = logs.filter((l) => l.event_action === 'APPROVED').length;
  const countEdited = logs.filter((l) => l.event_action === 'EDITED').length;
  const countDiscarded = logs.filter((l) => l.event_action === 'DISCARDED').length;

  const getActionBadgeColor = (action: string) => {
    switch (action) {
      case 'APPROVED': return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'EDITED': return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'DISCARDED': return 'bg-rose-50 text-rose-700 border-rose-200';
      default: return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="space-y-6">
      <Header
        title="Audit Trail & Compliance Explorer"
        agentTag="SOX Compliant"
        subTitle="Immutable Ledger of Human-in-the-Loop Decisions"
        moduleCode="Database Table: audit_trail_logs"
      />

      {fetchError && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 text-xs p-3 rounded-xl flex items-center justify-between">
          <span>&#9888; {fetchError}</span>
          <button onClick={fetchAuditLogs} className="underline font-bold">Coba Lagi</button>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Audited Events" value={`${logs.length}`} subtext={`Tercatat untuk entitas ${entity}`} valueColor="text-blue-600" />
        <StatCard title="Approved Decisions" value={`${countApproved}`} subtext="Dieksekusi ke ERP" valueColor="text-emerald-600" />
        <StatCard title="Edited & Approved" value={`${countEdited}`} subtext="Revisi manual oleh PIC" valueColor="text-amber-600" />
        <StatCard title="Discarded Actions" value={`${countDiscarded}`} subtext="Ditolak / tidak dieksekusi" valueColor="text-rose-600" />
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 bg-slate-50/50">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Riwayat Kepatuhan Otorisasi ({entity})
            </span>
            <span className="px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 text-[10px] font-bold">
              Auto-Sync 5s
            </span>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-400 font-semibold">Filter:</span>
            <select
              value={filterAction}
              onChange={(e) => setFilterAction(e.target.value)}
              className="bg-white border border-slate-200 font-bold text-slate-700 px-2.5 py-1 rounded-lg focus:outline-none cursor-pointer"
            >
              <option value="ALL">Semua Keputusan ({logs.length})</option>
              <option value="APPROVED">Disetujui Langsung ({countApproved})</option>
              <option value="EDITED">Diedit & Disetujui ({countEdited})</option>
              <option value="DISCARDED">Ditolak ({countDiscarded})</option>
            </select>
            <button
              onClick={fetchAuditLogs}
              className="text-xs font-semibold text-blue-600 hover:text-blue-800 transition pl-2"
            >
              &#8635;
            </button>
          </div>
        </div>

        <div className="overflow-x-auto text-xs">
          <table className="w-full text-left border-collapse">
            <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
              <tr>
                <th className="p-3">Log ID</th>
                <th className="p-3">Waktu Eksekusi</th>
                <th className="p-3">Operator PIC</th>
                <th className="p-3">Keputusan</th>
                <th className="p-3">Agen ID</th>
                <th className="p-3">Modul</th>
                <th className="p-3">Ref Dokumen</th>
                <th className="p-3 text-center">Inspeksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={8} className="p-8 text-center text-slate-400">
                    Belum ada riwayat audit trail untuk filter <strong>{filterAction}</strong> di entitas <strong>{entity}</strong>.
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50 transition">
                    <td className="p-3 font-mono font-bold text-slate-900 text-[11px]">
                      {log.id.substring(0, 8)}...
                    </td>
                    <td className="p-3 text-slate-400 whitespace-nowrap font-mono text-[11px]">
                      {log.created_at ? new Date(log.created_at).toLocaleString('id-ID') : '-'}
                    </td>
                    <td className="p-3 font-medium text-slate-800">{log.operator_id}</td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getActionBadgeColor(log.event_action)}`}>
                        {log.event_action}
                      </span>
                    </td>
                    <td className="p-3 font-mono uppercase text-blue-600 font-semibold">{log.agent_id}</td>
                    <td className="p-3 font-semibold text-slate-900">{log.module_code}</td>
                    <td className="p-3 font-mono text-blue-600 font-bold">{log.reference_doc}</td>
                    <td className="p-3 text-center">
                      <button
                        onClick={() => setSelectedLog(log)}
                        className="px-2.5 py-1 bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-slate-700 rounded font-semibold text-[11px] border border-slate-200 transition"
                      >
                        Detail &rarr;
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* INSPECTION SLIDE-OVER MODAL */}
      {selectedLog && (
        <div className="fixed inset-0 bg-slate-900/60 z-50 flex justify-end transition-opacity">
          <div className="w-full max-w-2xl bg-white h-full shadow-2xl p-6 flex flex-col justify-between overflow-y-auto">
            <div>
              <div className="flex justify-between items-start pb-4 border-b border-slate-200">
                <div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase ${getActionBadgeColor(selectedLog.event_action)}`}>
                      {selectedLog.event_action}
                    </span>
                    <span className="text-xs font-mono text-slate-400">ID: {selectedLog.id}</span>
                  </div>
                  <h3 className="text-base font-bold text-slate-900 mt-1">
                    Inspeksi Kepatuhan: {selectedLog.reference_doc}
                  </h3>
                  <p className="text-xs text-slate-400">
                    Agen: {selectedLog.agent_id.toUpperCase()} &bull; Modul: {selectedLog.module_code} &bull; Entitas: {selectedLog.entity_code}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedLog(null)}
                  className="text-slate-400 hover:text-slate-600 text-lg p-1"
                >
                  &#10005;
                </button>
              </div>

              <div className="mt-5 space-y-4 text-xs">
                {/* METADATA STAMP */}
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg grid grid-cols-2 gap-2 text-[11px]">
                  <div>
                    <span className="text-slate-400 block">Operator PIC Peninjau:</span>
                    <strong className="text-slate-800">{selectedLog.operator_id}</strong>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Stempel Waktu Eksekusi:</span>
                    <strong className="text-slate-800">
                      {selectedLog.created_at ? new Date(selectedLog.created_at).toLocaleString('id-ID') : '-'}
                    </strong>
                  </div>
                </div>

                {/* SIDE BY SIDE DIFF */}
                <div>
                  <label className="font-bold text-slate-700 block mb-1">
                    1. Rekomendasi Asli AI (Anthropic Claude RAG):
                  </label>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg font-mono text-[11px] text-slate-700 whitespace-pre-wrap leading-relaxed">
                    {selectedLog.original_text || '(Tidak ada narasi teks)'}
                  </div>
                </div>

                <div>
                  <label className="font-bold text-slate-700 block mb-1">
                    2. Teks Final yang Diotorisasi Operator (Dispatched Narrative):
                  </label>
                  <div className={`p-3 rounded-lg font-mono text-[11px] whitespace-pre-wrap leading-relaxed border ${
                    selectedLog.event_action === 'EDITED' 
                      ? 'bg-amber-50/50 border-amber-300 text-amber-950' 
                      : 'bg-emerald-50/40 border-emerald-200 text-emerald-950'
                  }`}>
                    {selectedLog.final_dispatched_text || '(Tidak ada narasi dikirim)'}
                  </div>
                  {selectedLog.event_action === 'EDITED' && (
                    <span className="text-[10px] text-amber-700 font-semibold mt-1 block">
                      * Teks ini telah melalui modifikasi manual oleh staf sebelum disetujui.
                    </span>
                  )}
                </div>

                {/* DISPATCH EXECUTION RESULT */}
                <div>
                  <label className="font-bold text-slate-700 block mb-1">
                    3. Bukti Eksekusi Nyata Dispatcher (Voucher / Webhook / Mutasi ERP):
                  </label>
                  <pre className="p-3 bg-slate-900 text-emerald-400 rounded-lg font-mono text-[11px] overflow-x-auto max-h-44">
                    {JSON.stringify(selectedLog.execution_result, null, 2)}
                  </pre>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-200 flex justify-end">
              <button
                onClick={() => setSelectedLog(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-bold text-xs transition"
              >
                Tutup Inspeksi
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
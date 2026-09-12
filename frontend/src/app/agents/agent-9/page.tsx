'use client';

import React, { useState } from 'react';
import Header from '@/components/Header';
import StatCard from '@/components/StatCard';
import DrawerModal from '@/components/DrawerModal';
import ReplicaSelectorModal from '@/components/ReplicaSelectorModal';
import { useEntity } from '@/context/EntityContext';

export default function Agent9Page() {
  const { entity } = useEntity();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isReplicaOpen, setIsReplicaOpen] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const [formData, setFormData] = useState({
    reference_doc: 'TREASURY-WK36-2026',
    bank_account: 'DBS Treasury Operating SGD',
    current_cash: 185000.0,
    weekly_burn_rate: 32000.0,
    loan_due_7days: 45000.0,
  });

  const handleAssessRunway = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/v1/agents/agent-9/assess-cash-runway', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          entity_code: entity,
          reference_doc: formData.reference_doc,
          current_cash: Number(formData.current_cash),
          weekly_burn_rate: Number(formData.weekly_burn_rate),
          loan_due_7days: Number(formData.loan_due_7days),
        }),
      });
      const data = await res.json();
      setResult(data);
      setIsDrawerOpen(true);
    } catch {
      alert('Gagal menghubungi backend FastAPI pada port 8000.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Header
        title="Agent 9: Cash Flow & Loan Narrative"
        agentTag="Phase 1: Active"
        subTitle="Operational Liquidity Runway Radar & OA Loan Repayment Guard"
        moduleCode="Module AC01 / AC02"
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Minimum Safe Runway" value="4.0 Minggu" subtext="Batas aman operasional entitas" valueColor="text-blue-600" />
        <StatCard title="Critical Threshold" value="< 2.0 Minggu" subtext="Pemicu otomatis eskalasi CFO" valueColor="text-rose-600" />
        <StatCard title="Priority Shield" value="OA Loans" subtext="Proteksi penalti denda bank" valueColor="text-emerald-600" />
        <StatCard title="Active Entity Scope" value={entity} subtext="Partisi akun kas entitas" valueColor="text-purple-600" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
              Simulasi Likuiditas Kas & Jatuh Tempo Pinjaman OA
            </h2>
            <button
              onClick={() => setIsReplicaOpen(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-50 border border-emerald-300 text-emerald-700 hover:bg-emerald-100 rounded text-xs font-semibold transition"
            >
              <span>📥</span>
              <span>Ambil dari Kas Replica ({entity})</span>
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Referensi Audit Kas / Periode:</label>
              <input
                type="text"
                value={formData.reference_doc}
                onChange={(e) => setFormData({ ...formData, reference_doc: e.target.value })}
                className="w-full p-2 border border-slate-300 rounded font-mono"
              />
            </div>
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Rekening Kas Utama:</label>
              <input
                type="text"
                value={formData.bank_account}
                onChange={(e) => setFormData({ ...formData, bank_account: e.target.value })}
                className="w-full p-2 border border-slate-300 rounded"
              />
            </div>
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Saldo Kas Efektif Saat Ini ($):</label>
              <input
                type="number"
                value={formData.current_cash}
                onChange={(e) => setFormData({ ...formData, current_cash: parseFloat(e.target.value) || 0 })}
                className="w-full p-2 border border-slate-300 rounded font-mono"
              />
            </div>
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Rata-Rata Burn Rate Mingguan ($):</label>
              <input
                type="number"
                value={formData.weekly_burn_rate}
                onChange={(e) => setFormData({ ...formData, weekly_burn_rate: parseFloat(e.target.value) || 0 })}
                className="w-full p-2 border border-slate-300 rounded font-mono"
              />
            </div>
            <div className="sm:col-span-2">
              <label className="text-slate-600 font-semibold block mb-1">
                Kewajiban Pinjaman OA Jatuh Tempo 7 Hari ke Depan ($):
              </label>
              <input
                type="number"
                value={formData.loan_due_7days}
                onChange={(e) => setFormData({ ...formData, loan_due_7days: parseFloat(e.target.value) || 0 })}
                className="w-full p-2 border border-slate-300 rounded font-mono"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">
                Dikurangkan secara deterministik dari kas efektif sebelum menghitung sisa ketahanan runway.
              </span>
            </div>
          </div>

          <div className="pt-2 flex justify-end">
            <button
              disabled={loading}
              onClick={handleAssessRunway}
              className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold text-xs shadow-sm transition disabled:opacity-50"
            >
              {loading ? 'Menganalisis Kas...' : 'Hitung Runway & Proteksi Likuiditas'}
            </button>
          </div>
        </div>

        <div className="bg-slate-50 rounded-xl border border-slate-200 p-5 space-y-4 text-xs">
          <h3 className="font-bold text-slate-800 uppercase tracking-wide border-b border-slate-200 pb-2">
            Protokol Treasury & Likuiditas
          </h3>
          <div className="space-y-3 text-slate-600">
            <div className="p-3 bg-white border border-slate-200 rounded-lg">
              <span className="font-bold text-emerald-700 block">Status Healthy (&gt;= 4.0 Minggu)</span>
              <p className="mt-1 text-[11px] text-slate-500">
                Operasional berjalan normal tanpa restriksi pengeluaran PO atau disbursement baru.
              </p>
            </div>
            <div className="p-3 bg-white border border-slate-200 rounded-lg">
              <span className="font-bold text-amber-700 block">Status Tight (2.0 - 3.9 Minggu)</span>
              <p className="mt-1 text-[11px] text-slate-500">
                Peringatan dini ke Treasury Lead untuk mempercepat penagihan AR (piutang usaha).
              </p>
            </div>
            <div className="p-3 bg-white border border-slate-200 rounded-lg">
              <span className="font-bold text-rose-700 block">Status Critical Deficit (&lt; 2.0 Minggu)</span>
              <p className="mt-1 text-[11px] text-slate-500">
                Draf peringatan darurat ke CFO untuk penangguhan belanja modal non-esensial dan renegosiasi pinjaman bank.
              </p>
            </div>
          </div>
        </div>
      </div>

      <DrawerModal
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        title={`Review Proyeksi Kas: ${formData.reference_doc}`}
        subTitle={`Rekening: ${formData.bank_account} • Entitas: ${entity}`}
        payload={result?.metrics || {}}
        narrative={result?.draft_preview || ''}
        onApprove={() => {
          alert('Laporan mitigasi likuiditas disetujui untuk diteruskan ke CFO!');
          setIsDrawerOpen(false);
        }}
        onEdit={(text) => {
          alert(`Laporan likuiditas disunting: ${text}`);
          setIsDrawerOpen(false);
        }}
        onDiscard={() => setIsDrawerOpen(false)}
      />

      <ReplicaSelectorModal
        isOpen={isReplicaOpen}
        onClose={() => setIsReplicaOpen(false)}
        title={`ERP Replica: Saldo Kas & Runway (${entity})`}
        endpoint={`/api/v1/replica/cash-position/${entity}`}
        columns={[
          { key: 'bank_account', label: 'Rekening Bank' },
          { key: 'current_cash', label: 'Kas Efektif ($)', format: (v) => `$${Number(v).toLocaleString()}` },
          { key: 'weekly_burn_rate', label: 'Weekly Burn ($)', format: (v) => `$${Number(v).toLocaleString()}` },
          { key: 'loan_due_7days', label: 'OA Due 7d ($)', format: (v) => `$${Number(v).toLocaleString()}` },
        ]}
        onSelect={(item) => {
          setFormData((prev) => ({
            ...prev,
            bank_account: item.bank_account || prev.bank_account,
            current_cash: Number(item.current_cash) || 0,
            weekly_burn_rate: Number(item.weekly_burn_rate) || 0,
            loan_due_7days: Number(item.loan_due_7days) || 0,
          }));
        }}
      />
    </div>
  );
}

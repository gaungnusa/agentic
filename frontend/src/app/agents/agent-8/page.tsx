'use client';

import React, { useState } from 'react';
import Header from '@/components/Header';
import StatCard from '@/components/StatCard';
import DrawerModal from '@/components/DrawerModal';
import { useEntity } from '@/context/EntityContext';
import { getBaseUrl } from '@/lib/api';

export default function Agent8Page() {
  const { entity } = useEntity();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const [formData, setFormData] = useState({
    bank_account: 'DBS Bank Singapore USD',
    reference_doc: 'TXN-DBS-88319',
    remittance_amount: 74500.0,
    invoice_book_rate: 1.350,
    bank_settlement_rate: 1.342,
    invoices: 'INV-2026-0412, INV-2026-0413',
  });

  const handleReconcile = async () => {
    setLoading(true);
    try {
      const baseUrl = await getBaseUrl();
      const res = await fetch(`${baseUrl}/agents/agent-8/reconcile-bank`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          entity_code: entity,
          reference_doc: formData.reference_doc,
          bank_account_ref: formData.bank_account,
          remittance_amount: formData.remittance_amount,
          remittance_currency: 'USD',
          target_invoices: formData.invoices.split(',').map((s) => s.trim()),
          invoice_book_rate: formData.invoice_book_rate,
          bank_settlement_rate: formData.bank_settlement_rate,
        }),
      });
      const data = await res.json();
      setResult(data);
      setIsDrawerOpen(true);
    } catch {
      alert('Gagal menghubungi backend FastAPI.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Header
        title="Agent 8: AR/AP Multi-Currency Reconciler"
        agentTag="Phase 3: Active"
        subTitle="Bank Matching, Realized FX Gain/Loss & Clearing Journal"
        moduleCode="Module AC02"
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Auto-Match Rate" value="94.8%" subtext="Payer & nomor invoice terpetakan" valueColor="text-emerald-600" />
        <StatCard title="Tolerance Rule" value="± $1.00" subtext="Ambang batas pembulatan transaksi" />
        <StatCard title="Month-End Closing" value="-3.5 Hari" subtext="Penyelesaian rekonsiliasi buku besar" valueColor="text-blue-600" />
        <StatCard title="Active Entity" value={entity} subtext="Entitas pembukuan valas" valueColor="text-purple-600" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wide border-b border-slate-100 pb-2">
            Bank Statement Ingestion & Settlement Feed
          </h2>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Akun Bank:</label>
              <input
                type="text"
                value={formData.bank_account}
                onChange={(e) => setFormData({ ...formData, bank_account: e.target.value })}
                className="w-full p-2 border border-slate-300 rounded"
              />
            </div>
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Ref Transaksi Bank:</label>
              <input
                type="text"
                value={formData.reference_doc}
                onChange={(e) => setFormData({ ...formData, reference_doc: e.target.value })}
                className="w-full p-2 border border-slate-300 rounded font-mono"
              />
            </div>
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Nominal Remittance ($):</label>
              <input
                type="number"
                value={formData.remittance_amount}
                onChange={(e) => setFormData({ ...formData, remittance_amount: parseFloat(e.target.value) })}
                className="w-full p-2 border border-slate-300 rounded font-mono"
              />
            </div>
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Invoice Cocok:</label>
              <input
                type="text"
                value={formData.invoices}
                onChange={(e) => setFormData({ ...formData, invoices: e.target.value })}
                className="w-full p-2 border border-slate-300 rounded font-mono"
              />
            </div>
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Kurs Buku Faktur (1 USD ke SGD):</label>
              <input
                type="number"
                step="0.001"
                value={formData.invoice_book_rate}
                onChange={(e) => setFormData({ ...formData, invoice_book_rate: parseFloat(e.target.value) })}
                className="w-full p-2 border border-slate-300 rounded font-mono"
              />
            </div>
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Kurs Penyelesaian Bank (1 USD ke SGD):</label>
              <input
                type="number"
                step="0.001"
                value={formData.bank_settlement_rate}
                onChange={(e) => setFormData({ ...formData, bank_settlement_rate: parseFloat(e.target.value) })}
                className="w-full p-2 border border-slate-300 rounded font-mono"
              />
            </div>
          </div>

          <div className="pt-3 border-t border-slate-100 flex justify-end">
            <button
              onClick={handleReconcile}
              disabled={loading}
              className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-bold text-xs shadow-sm transition"
            >
              {loading ? 'Menghitung Selisih Kurs...' : 'Proses Rekonsiliasi & Siapkan Jurnal'}
            </button>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3 text-xs">
          <h3 className="font-bold text-slate-900">Aturan Alokasi Valas AC02</h3>
          <p className="text-slate-600 leading-relaxed">
            Sistem menghitung selisih antara kurs saat faktur terbit dengan kurs riil saat dana masuk di mutasi bank:
          </p>
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1 font-mono text-[11px]">
            <div>Variance = Settlement - Book</div>
            <div>Loss (&lt; 0): Akun 7210 (Realized FX Loss)</div>
            <div>Gain (&ge; 0): Akun 7110 (Realized FX Gain)</div>
          </div>
        </div>
      </div>

      <DrawerModal
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        title={`Review Kliring Jurnal: ${formData.reference_doc}`}
        subTitle={`Akun: ${formData.bank_account} • Modul AC02`}
        payload={result?.metrics || {}}
        narrative={result?.draft_preview || ''}
        onApprove={() => {
          alert('Voucher jurnal kliring berhasil diposting ke GL!');
          setIsDrawerOpen(false);
        }}
        onEdit={() => setIsDrawerOpen(false)}
        onDiscard={() => setIsDrawerOpen(false)}
      />
    </div>
  );
}
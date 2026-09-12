'use client';

import React, { useState } from 'react';
import Header from '@/components/Header';
import StatCard from '@/components/StatCard';
import DrawerModal from '@/components/DrawerModal';
import ReplicaSelectorModal from '@/components/ReplicaSelectorModal';
import { useEntity } from '@/context/EntityContext';

export default function Agent2Page() {
  const { entity } = useEntity();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isReplicaOpen, setIsReplicaOpen] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // Form input uji langsung
  const [formData, setFormData] = useState({
    po_number: 'PO-2026-4412',
    so_number: 'SO-2026-1182',
    supplier_name: 'Broadcom APAC',
    so_selling_price: 120.0,
    po_cost_price: 108.5,
    ordered_qty: 350,
    supplier_moq: 500,
    tier2_cost_price: 94.0,
  });

  const handleRunValidation = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/v1/agents/agent-2/validate-po', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          entity_code: entity,
          reference_doc: formData.po_number,
          ...formData,
        }),
      });
      const data = await res.json();
      setTestResult(data);
      setIsDrawerOpen(true);
    } catch (err) {
      alert('Gagal menghubungi backend FastAPI.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Header
        title="Agent 2: SO/PO Mismatch Pre-Checker"
        agentTag="Phase 2: Active"
        subTitle="Contract Margin Guardrail & MOQ Enforcement"
        moduleCode="Module PS02"
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Min Margin Threshold" value="15.0%" subtext="Aturan baku BRD v10.0" valueColor="text-blue-600" />
        <StatCard title="MOQ Enforcement" value="Strict" subtext="Otomatis tawarkan tier harga" valueColor="text-emerald-600" />
        <StatCard title="Rework Cycle" value="-70%" subtext="Penurunan revisi PO manual" />
        <StatCard title="Active Entity" value={entity} subtext="Partisi tenant aktif" valueColor="text-purple-600" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
              Simulator Uji Validasi PO (Tembak Langsung ke FastAPI)
            </h2>
            <button
              onClick={() => setIsReplicaOpen(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-50 border border-emerald-300 text-emerald-700 hover:bg-emerald-100 rounded text-xs font-semibold transition"
            >
              <span>📥</span>
              <span>Ambil dari PO Replica ({entity})</span>
            </button>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Nomor PO:</label>
              <input
                type="text"
                value={formData.po_number}
                onChange={(e) => setFormData({ ...formData, po_number: e.target.value })}
                className="w-full p-2 border border-slate-300 rounded font-mono"
              />
            </div>
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Nomor SO Referensi:</label>
              <input
                type="text"
                value={formData.so_number}
                onChange={(e) => setFormData({ ...formData, so_number: e.target.value })}
                className="w-full p-2 border border-slate-300 rounded font-mono"
              />
            </div>
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Harga Jual SO ($):</label>
              <input
                type="number"
                value={formData.so_selling_price}
                onChange={(e) => setFormData({ ...formData, so_selling_price: parseFloat(e.target.value) })}
                className="w-full p-2 border border-slate-300 rounded font-mono"
              />
            </div>
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Harga Beli PO ($):</label>
              <input
                type="number"
                value={formData.po_cost_price}
                onChange={(e) => setFormData({ ...formData, po_cost_price: parseFloat(e.target.value) })}
                className="w-full p-2 border border-slate-300 rounded font-mono"
              />
            </div>
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Kuantitas Order:</label>
              <input
                type="number"
                value={formData.ordered_qty}
                onChange={(e) => setFormData({ ...formData, ordered_qty: parseInt(e.target.value) })}
                className="w-full p-2 border border-slate-300 rounded font-mono"
              />
            </div>
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Batas Minimum MOQ Vendor:</label>
              <input
                type="number"
                value={formData.supplier_moq}
                onChange={(e) => setFormData({ ...formData, supplier_moq: parseInt(e.target.value) })}
                className="w-full p-2 border border-slate-300 rounded font-mono"
              />
            </div>
          </div>

          <div className="pt-3 border-t border-slate-100 flex justify-end">
            <button
              onClick={handleRunValidation}
              disabled={loading}
              className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold text-xs shadow-sm transition"
            >
              {loading ? 'Menghitung...' : 'Jalankan Pra-Validasi PO'}
            </button>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3 text-xs">
          <h3 className="font-bold text-slate-900">Aturan Deterministik PS02</h3>
          <p className="text-slate-600 leading-relaxed">
            Jika gross margin berada di bawah 15% atau kuantitas order melanggar MOQ, PO langsung dikunci dari approval manajer dan draf rekomendasi perbaikan dikirim ke antrean HITL.
          </p>
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1 font-mono text-[11px]">
            <div>Margin = (SO - PO) / SO</div>
            <div>Strict Gate: Margin &ge; 15.0%</div>
            <div>MOQ Check: Qty &ge; MOQ</div>
          </div>
        </div>
      </div>

      <DrawerModal
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        title={`Review Validasi: ${formData.po_number}`}
        subTitle={`Entitas: ${entity} • Modul PS02`}
        payload={testResult?.metrics || {}}
        narrative={testResult?.draft_preview || ''}
        onApprove={() => {
          alert('PO disetujui dan diteruskan ke Dispatcher!');
          setIsDrawerOpen(false);
        }}
        onEdit={(text) => {
          alert(`PO diedit dan disetujui dengan catatan: ${text}`);
          setIsDrawerOpen(false);
        }}
        onDiscard={() => {
          alert('PO Ditolak / Dibatalkan.');
          setIsDrawerOpen(false);
        }}
      />

      <ReplicaSelectorModal
        isOpen={isReplicaOpen}
        onClose={() => setIsReplicaOpen(false)}
        title={`ERP Replica: Purchase Orders (${entity})`}
        endpoint={`/api/v1/replica/purchase-orders/${entity}`}
        columns={[
          { key: 'po_number', label: 'Nomor PO' },
          { key: 'so_number', label: 'Ref SO' },
          { key: 'supplier_name', label: 'Pemasok' },
          { key: 'ordered_qty', label: 'Qty' },
          { key: 'po_cost_price', label: 'Cost Price ($)', format: (v) => `$${Number(v).toFixed(2)}` },
          { key: 'supplier_moq', label: 'MOQ' },
          { key: 'tier2_cost_price', label: 'Tier 2 Cost ($)', format: (v) => `$${Number(v).toFixed(2)}` },
        ]}
        onSelect={(item) => {
          setFormData((prev) => ({
            ...prev,
            po_number: item.po_number,
            so_number: item.so_number || prev.so_number,
            supplier_name: item.supplier_name || prev.supplier_name,
            ordered_qty: Number(item.ordered_qty) || prev.ordered_qty,
            po_cost_price: Number(item.po_cost_price) || prev.po_cost_price,
            supplier_moq: Number(item.supplier_moq) || prev.supplier_moq,
            tier2_cost_price: Number(item.tier2_cost_price) || prev.tier2_cost_price,
          }));
        }}
      />
    </div>
  );
}
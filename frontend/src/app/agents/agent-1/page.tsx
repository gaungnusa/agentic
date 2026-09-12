'use client';

import React, { useState } from 'react';
import Header from '@/components/Header';
import StatCard from '@/components/StatCard';
import DrawerModal from '@/components/DrawerModal';
import ReplicaSelectorModal from '@/components/ReplicaSelectorModal';
import { useEntity } from '@/context/EntityContext';

export default function Agent1Page() {
  const { entity } = useEntity();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isReplicaOpen, setIsReplicaOpen] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const [formData, setFormData] = useState({
    rfq_number: 'RFQ-2026-0891',
    client_name: 'Singtel Optus SG',
    part_description: 'SFP+ 10G-LR Transceiver Module',
    unit_cost: '38.50',
    target_margin_pct: 18.0,
  });

  const handleProcessRFQ = async (isCatalogItem: boolean) => {
    setLoading(true);
    try {
      const costValue = isCatalogItem ? parseFloat(formData.unit_cost) : null;
      const res = await fetch('http://localhost:8000/api/v1/agents/agent-1/process-rfq', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          entity_code: entity,
          reference_doc: formData.rfq_number,
          unit_cost: costValue,
          target_margin_pct: formData.target_margin_pct,
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
        title="Agent 1: Quotation Response Assistant"
        agentTag="Phase 2: Active"
        subTitle="Inbound RFQ Auto-Pricer & Parallel Sourcing Dispatcher"
        moduleCode="Module PS01"
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Turnaround Time" value="4.2 Mins" subtext="Dari rata-rata manual 3.5 jam" valueColor="text-blue-600" />
        <StatCard title="Catalog Match Rate" value="83.3%" subtext="Ditemukan di Master Price PS03" valueColor="text-emerald-600" />
        <StatCard title="Target Gross Margin" value={`${formData.target_margin_pct}%`} subtext="Ambang batas standar penawaran" />
        <StatCard title="Active Entity" value={entity} subtext="Partisi tenant aktif" valueColor="text-purple-600" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
              Inbound Customer RFQ Simulator
            </h2>
            <button
              onClick={() => setIsReplicaOpen(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-50 border border-emerald-300 text-emerald-700 hover:bg-emerald-100 rounded text-xs font-semibold transition"
            >
              <span>📥</span>
              <span>Ambil dari Master Price ({entity})</span>
            </button>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Nomor RFQ:</label>
              <input
                type="text"
                value={formData.rfq_number}
                onChange={(e) => setFormData({ ...formData, rfq_number: e.target.value })}
                className="w-full p-2 border border-slate-300 rounded font-mono"
              />
            </div>
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Nama Pelanggan:</label>
              <input
                type="text"
                value={formData.client_name}
                onChange={(e) => setFormData({ ...formData, client_name: e.target.value })}
                className="w-full p-2 border border-slate-300 rounded"
              />
            </div>
            <div className="col-span-2">
              <label className="text-slate-600 font-semibold block mb-1">Deskripsi Part / SKU:</label>
              <input
                type="text"
                value={formData.part_description}
                onChange={(e) => setFormData({ ...formData, part_description: e.target.value })}
                className="w-full p-2 border border-slate-300 rounded"
              />
            </div>
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Estimasi Biaya Dasar ($):</label>
              <input
                type="number"
                value={formData.unit_cost}
                onChange={(e) => setFormData({ ...formData, unit_cost: e.target.value })}
                className="w-full p-2 border border-slate-300 rounded font-mono"
              />
            </div>
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Target Margin (%):</label>
              <input
                type="number"
                value={formData.target_margin_pct}
                onChange={(e) => setFormData({ ...formData, target_margin_pct: parseFloat(e.target.value) })}
                className="w-full p-2 border border-slate-300 rounded font-mono"
              />
            </div>
          </div>

          <div className="pt-3 border-t border-slate-100 flex justify-end gap-2">
            <button
              onClick={() => handleProcessRFQ(false)}
              disabled={loading}
              className="px-4 py-2 border border-amber-300 bg-amber-50 hover:bg-amber-100 text-amber-900 rounded-lg font-bold text-xs transition"
            >
              Simulasikan Part Baru (Parallel Sourcing)
            </button>
            <button
              onClick={() => handleProcessRFQ(true)}
              disabled={loading}
              className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold text-xs shadow-sm transition"
            >
              {loading ? 'Memproses...' : 'Proses RFQ (Catalog Matched)'}
            </button>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3 text-xs">
          <h3 className="font-bold text-slate-900">Alur Kerja Deterministik PS01</h3>
          <p className="text-slate-600 leading-relaxed">
            Jika part terdaftar di Master Price, agen langsung menghitung harga penawaran resmi. Jika part belum terdaftar, agen memicu RFQ paralel ke 3 vendor rekanan (Amphenol, Molex, CommScope).
          </p>
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1 font-mono text-[11px]">
            <div>Price = Cost / (1 - Margin%)</div>
            <div>Quorum Vendor: 3 Pemasok Terdaftar</div>
          </div>
        </div>
      </div>

      <DrawerModal
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        title={`Review RFQ: ${formData.rfq_number}`}
        subTitle={`Pelanggan: ${formData.client_name} • Modul PS01`}
        payload={result?.metrics || {}}
        narrative={result?.draft_preview || ''}
        onApprove={() => {
          alert('Penawaran disetujui dan masuk ke antrean pengiriman!');
          setIsDrawerOpen(false);
        }}
        onEdit={(text) => {
          alert(`Draf penawaran disunting: ${text}`);
          setIsDrawerOpen(false);
        }}
        onDiscard={() => setIsDrawerOpen(false)}
      />

      <ReplicaSelectorModal
        isOpen={isReplicaOpen}
        onClose={() => setIsReplicaOpen(false)}
        title={`ERP Replica: Master Price (${entity})`}
        endpoint={`/api/v1/replica/master-price/${entity}`}
        columns={[
          { key: 'part_number', label: 'Part Number' },
          { key: 'description', label: 'Deskripsi' },
          { key: 'unit_cost', label: 'Unit Cost ($)', format: (v) => `$${Number(v).toFixed(2)}` },
          { key: 'currency', label: 'Valas' },
        ]}
        onSelect={(item) => {
          setFormData((prev) => ({
            ...prev,
            part_description: `${item.part_number} - ${item.description}`,
            unit_cost: String(item.unit_cost),
          }));
        }}
      />
    </div>
  );
}
'use client';

import React, { useState } from 'react';
import Header from '@/components/Header';
import StatCard from '@/components/StatCard';
import DrawerModal from '@/components/DrawerModal';
import ReplicaSelectorModal from '@/components/ReplicaSelectorModal';
import { useEntity } from '@/context/EntityContext';
import { getBaseUrl } from '@/lib/api';

export default function Agent5Page() {
  const { entity } = useEntity();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isReplicaOpen, setIsReplicaOpen] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const [formData, setFormData] = useState({
    reference_doc: 'Amphenol Singapore Pte Ltd',
    supplier_code: 'VEND-SG-0492',
    on_time_rate: 94.0,
    quality_rate: 96.5,
    price_variance_pct: 1.8,
  });

  const handleEvaluateVendor = async () => {
    setLoading(true);
    try {
      const baseUrl = await getBaseUrl();
      const res = await fetch(`${baseUrl}/agents/agent-5/evaluate-vendor`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          entity_code: entity,
          reference_doc: formData.reference_doc,
          on_time_rate: Number(formData.on_time_rate),
          quality_rate: Number(formData.quality_rate),
          price_variance_pct: Number(formData.price_variance_pct),
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
        title="Agent 5: Vendor Performance Advisor"
        agentTag="Phase 1: Active"
        subTitle="Vendor Composite Scoring & Sourcing Allocation Engine"
        moduleCode="Module PS07"
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="On-Time Weight (OTD)" value="40%" subtext="Kepatuhan jadwal kedatangan" valueColor="text-blue-600" />
        <StatCard title="Quality QA Weight" value="40%" subtext="Rasio lolos inspeksi gudang" valueColor="text-emerald-600" />
        <StatCard title="Price Variance Weight" value="20%" subtext="Deviasi vs benchmark pasar" valueColor="text-purple-600" />
        <StatCard title="Tier 1 Threshold" value=">= 88.0" subtext="Rekomendasi alokasi 70% kuota" valueColor="text-amber-600" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
              Evaluasi Performa & Skor Komposit Supplier
            </h2>
            <button
              onClick={() => setIsReplicaOpen(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-50 border border-emerald-300 text-emerald-700 hover:bg-emerald-100 rounded text-xs font-semibold transition"
            >
              <span>📥</span>
              <span>Ambil dari Vendor Replica ({entity})</span>
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Nama Vendor / Mitra:</label>
              <input
                type="text"
                value={formData.reference_doc}
                onChange={(e) => setFormData({ ...formData, reference_doc: e.target.value })}
                className="w-full p-2 border border-slate-300 rounded"
              />
            </div>
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Kode Vendor ERP:</label>
              <input
                type="text"
                value={formData.supplier_code}
                onChange={(e) => setFormData({ ...formData, supplier_code: e.target.value })}
                className="w-full p-2 border border-slate-300 rounded font-mono"
              />
            </div>
            <div>
              <label className="text-slate-600 font-semibold block mb-1">On-Time Delivery Rate (%):</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="100"
                value={formData.on_time_rate}
                onChange={(e) => setFormData({ ...formData, on_time_rate: parseFloat(e.target.value) || 0 })}
                className="w-full p-2 border border-slate-300 rounded font-mono"
              />
            </div>
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Quality QA Passing Rate (%):</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="100"
                value={formData.quality_rate}
                onChange={(e) => setFormData({ ...formData, quality_rate: parseFloat(e.target.value) || 0 })}
                className="w-full p-2 border border-slate-300 rounded font-mono"
              />
            </div>
            <div className="sm:col-span-2">
              <label className="text-slate-600 font-semibold block mb-1">Variansi Harga terhadap Indeks Pasar (%):</label>
              <input
                type="number"
                step="0.1"
                value={formData.price_variance_pct}
                onChange={(e) => setFormData({ ...formData, price_variance_pct: parseFloat(e.target.value) || 0 })}
                className="w-full p-2 border border-slate-300 rounded font-mono"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">
                Nilai positif menunjukkan harga lebih tinggi dari patokan standar katalog ERP.
              </span>
            </div>
          </div>

          <div className="pt-2 flex justify-end">
            <button
              disabled={loading}
              onClick={handleEvaluateVendor}
              className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold text-xs shadow-sm transition disabled:opacity-50"
            >
              {loading ? 'Menghitung Skor...' : 'Kalkulasi Skor Komposit & Kuota PO'}
            </button>
          </div>
        </div>

        <div className="bg-slate-50 rounded-xl border border-slate-200 p-5 space-y-4 text-xs">
          <h3 className="font-bold text-slate-800 uppercase tracking-wide border-b border-slate-200 pb-2">
            Tiering & Alokasi Kuota Pengadaan
          </h3>
          <div className="space-y-3 text-slate-600">
            <div className="p-3 bg-white border border-slate-200 rounded-lg">
              <div className="flex justify-between items-center">
                <span className="font-bold text-emerald-700">Tier 1: Preferred</span>
                <span className="font-mono font-bold text-slate-800">&gt;= 88.0</span>
              </div>
              <p className="mt-1 text-[11px] text-slate-500">
                Alokasi kuota PO utama: <strong>70%</strong> dari total volume kebutuhan batch.
              </p>
            </div>
            <div className="p-3 bg-white border border-slate-200 rounded-lg">
              <div className="flex justify-between items-center">
                <span className="font-bold text-blue-700">Tier 2: Standard</span>
                <span className="font-mono font-bold text-slate-800">70.0 - 87.9</span>
              </div>
              <p className="mt-1 text-[11px] text-slate-500">
                Alokasi cadangan: <strong>30%</strong> dari total volume kebutuhan batch.
              </p>
            </div>
            <div className="p-3 bg-white border border-slate-200 rounded-lg">
              <div className="flex justify-between items-center">
                <span className="font-bold text-rose-700">Tier 3: Restricted</span>
                <span className="font-mono font-bold text-slate-800">&lt; 70.0</span>
              </div>
              <p className="mt-1 text-[11px] text-slate-500">
                Alokasi <strong>0%</strong>. Vendor diblokir dari penerbitan PO otomatis hingga proses audit selesai.
              </p>
            </div>
          </div>
        </div>
      </div>

      <DrawerModal
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        title={`Review Skor Vendor: ${formData.reference_doc}`}
        subTitle={`Kode: ${formData.supplier_code} • Entitas: ${entity}`}
        payload={result?.metrics || {}}
        narrative={result?.draft_preview || ''}
        onApprove={() => {
          alert('Alokasi kuota sourcing vendor disetujui!');
          setIsDrawerOpen(false);
        }}
        onEdit={(text) => {
          alert(`Rekomendasi sourcing disunting: ${text}`);
          setIsDrawerOpen(false);
        }}
        onDiscard={() => setIsDrawerOpen(false)}
      />

      <ReplicaSelectorModal
        isOpen={isReplicaOpen}
        onClose={() => setIsReplicaOpen(false)}
        title={`ERP Replica: Vendor Registry (${entity})`}
        endpoint={`/api/v1/replica/vendors/${entity}`}
        columns={[
          { key: 'vendor_code', label: 'Kode Vendor' },
          { key: 'vendor_name', label: 'Nama Vendor' },
          { key: 'on_time_rate', label: 'OTD Rate (%)', format: (v) => `${Number(v).toFixed(1)}%` },
          { key: 'quality_rate', label: 'Quality QA (%)', format: (v) => `${Number(v).toFixed(1)}%` },
          { key: 'price_variance_pct', label: 'Price Var (%)', format: (v) => `${Number(v).toFixed(1)}%` },
        ]}
        onSelect={(item) => {
          setFormData((prev) => ({
            ...prev,
            reference_doc: item.vendor_name,
            supplier_code: item.vendor_code,
            on_time_rate: Number(item.on_time_rate) || 0,
            quality_rate: Number(item.quality_rate) || 0,
            price_variance_pct: Number(item.price_variance_pct) || 0,
          }));
        }}
      />
    </div>
  );
}

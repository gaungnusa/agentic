'use client';

import React, { useState } from 'react';
import Header from '@/components/Header';
import StatCard from '@/components/StatCard';
import DrawerModal from '@/components/DrawerModal';
import ReplicaSelectorModal from '@/components/ReplicaSelectorModal';
import { useEntity } from '@/context/EntityContext';
import { getBaseUrl } from '@/lib/api';

export default function Agent3Page() {
  const { entity } = useEntity();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isReplicaOpen, setIsReplicaOpen] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const [formData, setFormData] = useState({
    reference_doc: 'SO-2026-9021',
    customer_name: 'VNPT Telecom Vietnam',
    rdd_target_str: '2026-09-10',
    eta_str: '2026-09-22',
    order_value: 45000.0,
  });

  const handleEvaluateRDD = async () => {
    setLoading(true);
    try {
      const baseUrl = await getBaseUrl();
      const res = await fetch(`${baseUrl}/agents/agent-3/evaluate-rdd`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          entity_code: entity,
          reference_doc: formData.reference_doc,
          rdd_target_str: formData.rdd_target_str,
          eta_str: formData.eta_str,
          order_value: Number(formData.order_value),
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
        title="Agent 3: Backlog & Exception Narrator"
        agentTag="Phase 1: Active"
        subTitle="RDD Delivery Deviation & Backlog Escalation Radar"
        moduleCode="Module PS06 / PS07"
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Target Delivery SLA" value="100% RDD" subtext="Batas kepatuhan kontrak klien" valueColor="text-blue-600" />
        <StatCard title="Warning Threshold" value="> 3 Hari" subtext="Eskalasi logistik level 1" valueColor="text-amber-600" />
        <StatCard title="Critical Severity" value="> 14 Hari" subtext="Eskalasi darurat Project Lead" valueColor="text-rose-600" />
        <StatCard title="Active Entity Scope" value={entity} subtext="Partisi tenant database" valueColor="text-purple-600" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
              RDD vs ETA Deviation Simulator
            </h2>
            <button
              onClick={() => setIsReplicaOpen(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-50 border border-emerald-300 text-emerald-700 hover:bg-emerald-100 rounded text-xs font-semibold transition"
            >
              <span>📥</span>
              <span>Ambil dari SO Replica ({entity})</span>
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Nomor Dokumen / SO:</label>
              <input
                type="text"
                value={formData.reference_doc}
                onChange={(e) => setFormData({ ...formData, reference_doc: e.target.value })}
                className="w-full p-2 border border-slate-300 rounded font-mono"
              />
            </div>
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Nama Customer / Proyek:</label>
              <input
                type="text"
                value={formData.customer_name}
                onChange={(e) => setFormData({ ...formData, customer_name: e.target.value })}
                className="w-full p-2 border border-slate-300 rounded"
              />
            </div>
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Target Request Delivery Date (RDD):</label>
              <input
                type="date"
                value={formData.rdd_target_str}
                onChange={(e) => setFormData({ ...formData, rdd_target_str: e.target.value })}
                className="w-full p-2 border border-slate-300 rounded font-mono"
              />
            </div>
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Estimated Time of Arrival (ETA):</label>
              <input
                type="date"
                value={formData.eta_str}
                onChange={(e) => setFormData({ ...formData, eta_str: e.target.value })}
                className="w-full p-2 border border-slate-300 rounded font-mono"
              />
            </div>
            <div className="sm:col-span-2">
              <label className="text-slate-600 font-semibold block mb-1">Total Nilai Pesanan ($ USD / Valas):</label>
              <input
                type="number"
                value={formData.order_value}
                onChange={(e) => setFormData({ ...formData, order_value: parseFloat(e.target.value) || 0 })}
                className="w-full p-2 border border-slate-300 rounded font-mono"
              />
            </div>
          </div>

          <div className="pt-2 flex justify-end">
            <button
              disabled={loading}
              onClick={handleEvaluateRDD}
              className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold text-xs shadow-sm transition disabled:opacity-50"
            >
              {loading ? 'Menganalisis RDD...' : 'Jalankan Evaluasi Backlog RDD'}
            </button>
          </div>
        </div>

        <div className="bg-slate-50 rounded-xl border border-slate-200 p-5 space-y-4 text-xs">
          <h3 className="font-bold text-slate-800 uppercase tracking-wide border-b border-slate-200 pb-2">
            Matriks Aturan Deterministik
          </h3>
          <div className="space-y-3 text-slate-600">
            <div className="p-3 bg-white border border-slate-200 rounded-lg">
              <span className="font-bold text-slate-800 block">SOP Deviasi Pengiriman:</span>
              <p className="mt-1 text-[11px] leading-relaxed">
                Delta hari dihitung pasti via Python: <code>ETA - RDD</code>. Jika selisih hari &gt; 14 hari, keparahan bertipe <strong>CRITICAL</strong> dan draf surat peringatan keterlambatan otomatis diterbitkan ke antrean HITL.
              </p>
            </div>
            <div className="p-3 bg-white border border-slate-200 rounded-lg">
              <span className="font-bold text-slate-800 block">Governance HITL Gateway:</span>
              <p className="mt-1 text-[11px] leading-relaxed">
                Narasi formal yang disusun Claude API tidak akan langsung terkirim ke email klien/forwarder hingga PIC Logistik menyetujui di antrean <code>draft_agent_actions</code>.
              </p>
            </div>
          </div>
        </div>
      </div>

      <DrawerModal
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        title={`Review Evaluasi SLA RDD: ${formData.reference_doc}`}
        subTitle={`Entitas: ${entity} • Pelanggan: ${formData.customer_name}`}
        payload={result?.metrics || {}}
        narrative={result?.draft_preview || ''}
        onApprove={() => {
          alert('Notifikasi keterlambatan disetujui untuk dikirim!');
          setIsDrawerOpen(false);
        }}
        onEdit={(text) => {
          alert(`Notifikasi diedit dan disetujui: ${text}`);
          setIsDrawerOpen(false);
        }}
        onDiscard={() => {
          setIsDrawerOpen(false);
        }}
      />

      <ReplicaSelectorModal
        isOpen={isReplicaOpen}
        onClose={() => setIsReplicaOpen(false)}
        title={`ERP Replica: Sales Orders (${entity})`}
        endpoint={`/api/v1/replica/sales-orders/${entity}`}
        columns={[
          { key: 'so_number', label: 'Nomor SO' },
          { key: 'customer_name', label: 'Customer' },
          { key: 'rdd_target', label: 'Target RDD', format: (v) => v ? String(v).split('T')[0] : '-' },
          { key: 'eta_delivery', label: 'ETA Delivery', format: (v) => v ? String(v).split('T')[0] : '-' },
          { key: 'order_value', label: 'Nilai Order ($)', format: (v) => `$${Number(v).toLocaleString()}` },
        ]}
        onSelect={(item) => {
          setFormData((prev) => ({
            ...prev,
            reference_doc: item.so_number,
            customer_name: item.customer_name || prev.customer_name,
            rdd_target_str: item.rdd_target ? String(item.rdd_target).split('T')[0] : prev.rdd_target_str,
            eta_str: item.eta_delivery ? String(item.eta_delivery).split('T')[0] : prev.eta_str,
            order_value: Number(item.order_value) || prev.order_value,
          }));
        }}
      />
    </div>
  );
}

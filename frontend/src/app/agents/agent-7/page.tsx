'use client';

import React, { useState } from 'react';
import Header from '@/components/Header';
import StatCard from '@/components/StatCard';
import DrawerModal from '@/components/DrawerModal';
import { useEntity } from '@/context/EntityContext';
import { getBaseUrl } from '@/lib/api';

export default function Agent7Page() {
  const { entity } = useEntity();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleVerifyTriangle = async () => {
    setLoading(true);
    try {
      const baseUrl = await getBaseUrl();
      const res = await fetch(`${baseUrl}/agents/agent-7/verify-triangle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          entity_code: entity,
          po_ref: 'PO-8812',
          so_ref: 'SO-3310',
          is_pod_received: true,
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
        title="Agent 7: Direct Delivery & Borrowed Stock Monitor"
        agentTag="Phase 3: Active"
        subTitle="Triangle Trade Logical GR/GI Pairing & Loan Maturity Radar"
        moduleCode="BRD Section 6.3"
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Active Triangle Routes" value="12 Orders" subtext="Bypass gudang fisik Singapura" valueColor="text-blue-600" />
        <StatCard title="Verified PODs" value="9 Matched" subtext="Siap posting serentak Logical GR/GI" valueColor="text-emerald-600" />
        <StatCard title="Borrowed Stock Assets" value="5 Units" subtext="1 unit mendekati jatuh tempo H-5" valueColor="text-purple-600" />
        <StatCard title="Penalty Incurred" value="$0.00" subtext="Nol denda keterlambatan stok mitra" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Triangle Trade Block */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div className="flex justify-between items-center border-b border-slate-100 pb-2">
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
              1. Triangle Trade Direct Delivery Queue
            </h2>
            <span className="text-[10px] bg-blue-100 text-blue-800 font-bold px-2 py-0.5 rounded">Rute 6.3</span>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            Pengiriman langsung dari <strong>Furukawa Tokyo (PO-8812)</strong> ke <strong>FPT Telecom Danang (SO-3310)</strong> tanpa transit fisik di hub Singapura.
          </p>
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
            <div>Forwarder POD: <strong className="text-emerald-600 font-mono">Diterima & Tervalidasi</strong></div>
            <div>Mutasi Gudang Fisik SG: <strong className="text-slate-700">Nol (Bypass Sesuai Aturan)</strong></div>
          </div>
          <button
            onClick={handleVerifyTriangle}
            disabled={loading}
            className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold text-xs shadow-sm transition"
          >
            {loading ? 'Memvalidasi...' : 'Verifikasi POD & Siapkan Logical GR/GI'}
          </button>
        </div>

        {/* Borrowed Stock Block */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div className="flex justify-between items-center border-b border-slate-100 pb-2">
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
              2. Borrowed Stock Maturity Tracker
            </h2>
            <span className="text-[10px] bg-amber-100 text-amber-800 font-bold px-2 py-0.5 rounded">Alert H-5</span>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            Mitra: <strong>NTT Singapore</strong> &bull; Item: <strong>Cisco Line Card 100G (2 unit)</strong>. Stok pengganti (PO-9014) sudah tiba di dermaga.
          </p>
          <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs space-y-1 text-amber-950">
            <div>Batas Waktu Pinjaman: <strong className="font-mono">5 Hari Lagi (H-5)</strong></div>
            <div>Nomor Seri Pengganti: <strong className="font-mono">SN-882190, SN-882191</strong></div>
          </div>
          <button
            onClick={() => {
              setResult({
                metrics: { days_left: 5, action_required: 'DISPATCH_RETURN_ADVICE' },
                draft_preview: 'Agent 7 menyusun nota pengembalian resmi untuk NTT Singapore dengan verifikasi nomor seri pengganti.',
              });
              setIsDrawerOpen(true);
            }}
            className="w-full py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg font-bold text-xs shadow-sm transition"
          >
            Review Nota Pengembalian Barang Pinjaman
          </button>
        </div>
      </div>

      <DrawerModal
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        title="Review Otorisasi Logistik Triangle Trade"
        subTitle={`Entitas: ${entity} • Section 6.3 Compliance`}
        payload={result?.metrics || {}}
        narrative={result?.draft_preview || ''}
        onApprove={() => {
          alert('Logical GR dan Logical GI serentak diposting!');
          setIsDrawerOpen(false);
        }}
        onEdit={() => setIsDrawerOpen(false)}
        onDiscard={() => setIsDrawerOpen(false)}
      />
    </div>
  );
}
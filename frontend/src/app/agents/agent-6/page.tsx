'use client';

import React, { useState } from 'react';
import Header from '@/components/Header';
import StatCard from '@/components/StatCard';
import DrawerModal from '@/components/DrawerModal';
import { useEntity } from '@/context/EntityContext';
import { getBaseUrl } from '@/lib/api';

export default function Agent6Page() {
  const { entity } = useEntity();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleScanSimulation = async () => {
    try {
      const baseUrl = await getBaseUrl();
      const res = await fetch(`${baseUrl}/agents/agent-6/handle-gr`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          entity_code: entity,
          reference_doc: 'PO-2026-9902',
          po_expected_qty: 1000,
          scanned_qty: 1000,
          damaged_qty: 80,
          unit_cost: 39.0,
        }),
      });
      const data = await res.json();
      setResult(data);
      setIsDrawerOpen(true);
    } catch {
      alert('Gagal menghubungi backend.');
    }
  };

  return (
    <div className="space-y-6">
      <Header
        title="Agent 6: GR Discrepancy Handler"
        agentTag="Phase 2: Active"
        subTitle="Warehouse Receiving & RMA Auto-Split"
        moduleCode="Module IN01 / IN05"
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Dock Clearance" value="14 Mins" subtext="Down from manual 3 hours" valueColor="text-blue-600" />
        <StatCard title="Auto-Split Mode" value="Enabled" subtext="Valid units directly to inventory" valueColor="text-emerald-600" />
        <StatCard title="RMA Generation" value="Instant" subtext="Debit note klaim terotomasi" />
        <StatCard title="Active Entity" value={entity} subtext="Warehouse dock scope" valueColor="text-purple-600" />
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
        <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wide border-b border-slate-100 pb-2">
          Simulasi Penerimaan Kargo Masuk (Inbound Receiving)
        </h2>
        <p className="text-xs text-slate-600">
          Uji skenario: 1.000 pcs pesanan tiba, 920 pcs utuh, 80 pcs rusak fisik akibat benturan kontainer.
        </p>
        <button
          onClick={handleScanSimulation}
          className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg font-bold text-xs shadow-sm transition"
        >
          Simulasikan Deteksi Kerusakan Barcode
        </button>
      </div>

      <DrawerModal
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        title="Review Pemisahan Partial GR & RMA Klaim"
        subTitle="PO-2026-9902 • Tuas Warehouse SG"
        payload={result?.metrics || {}}
        narrative={result?.draft_preview || ''}
        onApprove={() => {
          alert('Partial GR 920 pcs diposting & RMA 80 pcs diterbitkan!');
          setIsDrawerOpen(false);
        }}
        onEdit={() => setIsDrawerOpen(false)}
        onDiscard={() => setIsDrawerOpen(false)}
      />
    </div>
  );
}
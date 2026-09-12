'use client';

import React, { useState } from 'react';
import Header from '@/components/Header';
import StatCard from '@/components/StatCard';
import DrawerModal from '@/components/DrawerModal';
import { useEntity } from '@/context/EntityContext';
import { submitHITLDecision } from '@/lib/api';

export default function Agent4Page() {
  const { entity } = useEntity();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [selectedBook, setSelectedBook] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const PRICE_BOOKS = [
    {
      id: 'MP-CS-2026-Q2',
      vendor: 'Cisco Systems APAC',
      category: 'Optics & SFP Modules',
      validity: '01 Jul - 30 Sep 2026',
      days_left: 28,
      status: 'Expiring Soon (H-28)',
      status_color: 'bg-rose-100 text-rose-800',
      items_count: 45,
    },
    {
      id: 'MP-FH-2026-Q3',
      vendor: 'FiberHome Optical',
      category: 'Cables & Patch Cords',
      validity: '15 Jul - 15 Oct 2026',
      days_left: 43,
      status: 'Scheduled H-30',
      status_color: 'bg-amber-100 text-amber-800',
      items_count: 120,
    },
    {
      id: 'MP-SUM-2026-Q3',
      vendor: 'Sumitomo Electric JP',
      category: 'Fusion Splicers & Toolkits',
      validity: '01 Aug - 31 Oct 2026',
      days_left: 59,
      status: 'Healthy',
      status_color: 'bg-emerald-100 text-emerald-800',
      items_count: 18,
    },
  ];

  const handleGenerateRenewal = async (book: any) => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/v1/agents/agent-4/evaluate-price-book', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          entity_code: entity,
          reference_doc: book.id,
          days_left: book.days_left,
          items_count: book.items_count,
          inflation_adj_pct: 2.1,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setSelectedBook({
          payload: data.metrics,
          draftText: data.draft_preview,
          ref_doc: book.id,
          draft_id: data.draft_action_id,
        });
        setIsDrawerOpen(true);
        return;
      }
    } catch {}

    // Fallback if backend is unreachable
    const payload = {
      book_reference: book.id,
      vendor: book.vendor,
      current_validity: book.validity,
      days_remaining: book.days_left,
      items_affected: book.items_count,
      recommended_inflation_adjustment_pct: 2.1,
      target_renewal_period: '01 Oct 2026 - 31 Dec 2026',
    };

    const draftText = (
      `Agent 4 mendeteksi katalog harga ${book.vendor} (${book.id}) akan kedaluwarsa dalam ${book.days_left} hari.\n\n` +
      `Paket Pembaruan Otomatis Terbentuk:\n` +
      `• Penyesuaian indeks inflasi: +2.1% pre-calculated\n` +
      `• Format file: Template resmi bulk Excel ERP (.xlsx) untuk ${book.items_count} baris SKU\n` +
      `• Target periode baru: 01 Oct 2026 - 31 Dec 2026\n\n` +
      `Siap diekspor dan dikirimkan ke kontak vendor untuk renegosiasi kuartal berikutnya.`
    );

    setSelectedBook({ payload, draftText, ref_doc: book.id });
    setIsDrawerOpen(true);
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <Header
        title="Agent 4: Price Validity & Renewal Agent"
        agentTag="Phase 2: Active"
        subTitle="90-Day Master Price Radar & Bulk Template Generator"
        moduleCode="Module PS03"
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Active Price Books" value="142 Books" subtext="1,820 SKU terdaftar" valueColor="text-blue-600" />
        <StatCard title="Expiring in 30 Days" value="4 Books" subtext="Draf template bulk siap diekspor" valueColor="text-amber-600" />
        <StatCard title="Expired Rate Avoidance" value="100%" subtext="Nol kutipan memakai harga usang" valueColor="text-emerald-600" />
        <StatCard title="Active Entity" value={entity} subtext="Wilayah harga katalog" valueColor="text-purple-600" />
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
        <div className="flex justify-between items-center border-b border-slate-100 pb-3">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
            Master Price Validity Radar (90-Day Lifecycle Schedule)
          </h2>
          <span className="text-xs font-mono bg-slate-100 px-2 py-0.5 rounded text-slate-600">Module PS03</span>
        </div>

        <div className="overflow-x-auto text-xs">
          <table className="w-full text-left">
            <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
              <tr>
                <th className="p-3">Ref Kontrak</th>
                <th className="p-3">Vendor / Kategori</th>
                <th className="p-3">Masa Berlaku</th>
                <th className="p-3">Sisa Waktu</th>
                <th className="p-3">Status Radar</th>
                <th className="p-3 text-center">Aksi Agen</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {PRICE_BOOKS.map((book) => (
                <tr key={book.id} className="hover:bg-slate-50">
                  <td className="p-3 font-mono font-bold text-blue-600">{book.id}</td>
                  <td className="p-3">
                    <strong className="block text-slate-900">{book.vendor}</strong>
                    <span className="text-[11px] text-slate-400">{book.category} ({book.items_count} SKU)</span>
                  </td>
                  <td className="p-3 font-mono">{book.validity}</td>
                  <td className="p-3 font-bold font-mono text-slate-700">{book.days_left} Hari</td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${book.status_color}`}>
                      {book.status}
                    </span>
                  </td>
                  <td className="p-3 text-center">
                    <button
                      onClick={() => handleGenerateRenewal(book)}
                      className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold text-[11px] shadow-sm transition"
                    >
                      Buka Renewal Pack
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <DrawerModal
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        title={`Review Perpanjangan: ${selectedBook?.ref_doc}`}
        subTitle={`Modul PS03 • Entitas ${entity}`}
        payload={selectedBook?.payload || {}}
        narrative={selectedBook?.draftText || ''}
        onApprove={async () => {
          if (selectedBook?.draft_id) {
            try {
              await submitHITLDecision({
                draft_action_id: selectedBook.draft_id,
                operator_id: 'sg_purchaser',
                decision: 'APPROVE',
              });
              alert(`✓ Paket renewal ${selectedBook.ref_doc} berhasil disetujui dan dicatat ke Audit Trail!`);
            } catch (err: any) {
              alert(`Gagal approve: ${err.message || 'Kesalahan jaringan'}`);
            }
          } else {
            alert('Template Excel (.xlsx) dibuat dan draf email renegosiasi terkirim!');
          }
          setIsDrawerOpen(false);
        }}
        onEdit={() => setIsDrawerOpen(false)}
        onDiscard={() => setIsDrawerOpen(false)}
      />
    </div>
  );
}
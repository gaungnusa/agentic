'use client';

import React, { useState, useEffect } from 'react';

interface DraftAction {
  id: string;
  agent_id: string;
  module: string;
  ref_doc: string;
  payload: any;
  narrative: string;
  created_at: string;
}

export default function HITLWorkspace() {
  const [entity, setEntity] = useState('SG');
  const [queue, setQueue] = useState<DraftAction[]>([]);
  const [selectedDraft, setSelectedDraft] = useState<DraftAction | null>(null);
  const [editText, setEditText] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchQueue = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/hitl/queue/${entity}`);
      if (res.ok) {
        const data = await res.json();
        setQueue(data);
      }
    } catch (err) {
      console.error("Gagal narik antrean HITL:", err);
    }
  };

  useEffect(() => {
    fetchQueue();
    const interval = setInterval(fetchQueue, 5000); // Polling tiap 5 detik
    return () => clearInterval(interval);
  }, [entity]);

  const handleDecision = async (decision: 'APPROVE' | 'EDIT' | 'DISCARD') => {
    if (!selectedDraft) return;
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/v1/hitl/decision', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          draft_action_id: selectedDraft.id,
          operator_id: 'eko.suryahadi@batunetworks.com',
          decision: decision,
          modified_narrative: decision === 'EDIT' ? editText : undefined,
        }),
      });
      if (res.ok) {
        setSelectedDraft(null);
        fetchQueue();
      }
    } catch (err) {
      console.error("Gagal commit keputusan:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto font-sans text-slate-800">
      {/* Entity Selector Header */}
      <div className="flex justify-between items-center bg-white p-4 rounded-xl border border-slate-200 shadow-sm mb-6">
        <div>
          <h2 className="text-base font-bold text-slate-900">Batu Networks ERP &bull; Human-in-the-Loop Gateway</h2>
          <p className="text-xs text-slate-400">Verifikasi draf rekomendasi AI sebelum mutasi transaksi dieksekusi</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500 font-semibold">Wilayah Entitas:</span>
          <select 
            value={entity} 
            onChange={(e) => setEntity(e.target.value)}
            className="border border-slate-300 rounded-lg px-3 py-1.5 text-xs font-bold bg-slate-50"
          >
            <option value="SG">SG - Singapore HQ</option>
            <option value="VN">VN - Vietnam SSC</option>
            <option value="KR">KR - Korea Branch</option>
            <option value="IN">IN - India Back-Office</option>
            <option value="JP">JP - Japan Office</option>
          </select>
        </div>
      </div>

      {/* Table of Pending Drafts */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden mb-6">
        <div className="p-4 border-b border-slate-100 flex justify-between items-center">
          <span className="text-xs font-bold uppercase text-slate-500">Antrean Draf Menunggu Otorisasi ({queue.length})</span>
          <button onClick={fetchQueue} className="text-xs text-blue-600 hover:underline">Refresh Manual</button>
        </div>
        <div className="overflow-x-auto text-xs">
          <table className="w-full text-left">
            <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
              <tr>
                <th className="p-3">Agen ID</th>
                <th className="p-3">Modul</th>
                <th className="p-3">Ref Dokumen</th>
                <th className="p-3">Cuplikan Narasi Draf</th>
                <th className="p-3">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {queue.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-4 text-center text-slate-400">Tidak ada draf pending untuk entitas {entity}.</td>
                </tr>
              ) : (
                queue.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50">
                    <td className="p-3 font-mono font-bold text-blue-600 uppercase">{item.agent_id}</td>
                    <td className="p-3 font-semibold">{item.module}</td>
                    <td className="p-3 font-mono">{item.ref_doc}</td>
                    <td className="p-3 text-slate-600 truncate max-w-xs">{item.narrative}</td>
                    <td className="p-3">
                      <button 
                        onClick={() => { setSelectedDraft(item); setEditText(item.narrative); }}
                        className="bg-blue-600 hover:bg-blue-700 text-white font-bold px-3 py-1 rounded text-[11px]"
                      >
                        Buka Review
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Review Drawer Modal */}
      {selectedDraft && (
        <div className="fixed inset-0 bg-slate-900/60 z-50 flex justify-end">
          <div className="w-full max-w-lg bg-white h-full shadow-2xl p-6 flex flex-col justify-between overflow-y-auto">
            <div>
              <div className="flex justify-between items-start pb-4 border-b border-slate-200">
                <div>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">
                    HITL Gate &bull; {selectedDraft.agent_id.toUpperCase()}
                  </span>
                  <h3 className="text-base font-bold text-slate-900 mt-1">Review Transaksi {selectedDraft.ref_doc}</h3>
                </div>
                <button onClick={() => setSelectedDraft(null)} className="text-slate-400 hover:text-slate-600 text-lg">✕</button>
              </div>

              <div className="mt-4 space-y-4 text-xs">
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Payload Deterministik (Python Verified):</label>
                  <pre className="p-3 bg-slate-50 border border-slate-200 rounded font-mono text-[11px] overflow-x-auto text-slate-700">
                    {JSON.stringify(selectedDraft.payload, null, 2)}
                  </pre>
                </div>
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Draf Narasi (Bisa Disunting):</label>
                  <textarea 
                    rows={6} 
                    value={editText} 
                    onChange={(e) => setEditText(e.target.value)}
                    className="w-full p-3 font-mono text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-200 flex justify-end gap-2 text-xs">
              <button 
                disabled={loading}
                onClick={() => handleDecision('DISCARD')} 
                className="px-4 py-2 border border-slate-300 text-slate-600 rounded-lg font-semibold hover:bg-slate-50"
              >
                Discard
              </button>
              <button 
                disabled={loading}
                onClick={() => handleDecision('EDIT')} 
                className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg font-bold"
              >
                Simpan Edit & Otorisasi
              </button>
              <button 
                disabled={loading}
                onClick={() => handleDecision('APPROVE')} 
                className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold"
              >
                Approve & Eksekusi
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
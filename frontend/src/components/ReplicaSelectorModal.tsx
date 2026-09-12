'use client';

import React, { useState, useEffect } from 'react';
import { getApiRoot } from '@/lib/api';

interface Column {
  key: string;
  label: string;
  format?: (val: any) => React.ReactNode;
}

interface ReplicaSelectorModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  endpoint: string;
  columns: Column[];
  onSelect: (item: any) => void;
}

export default function ReplicaSelectorModal({
  isOpen,
  onClose,
  title,
  endpoint,
  columns,
  onSelect,
}: ReplicaSelectorModalProps) {
  const [data, setData] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSemanticMode, setIsSemanticMode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isMasterPrice = endpoint.includes('master-price');

  const fetchData = async (semanticQuery?: string) => {
    setLoading(true);
    setError(null);
    try {
      const apiRoot = await getApiRoot();
      let url = `${apiRoot}${endpoint}`;
      if (isSemanticMode && semanticQuery && semanticQuery.trim().length > 1) {
        // Extract entity from endpoint, e.g. /api/v1/replica/master-price/SG -> SG
        const parts = endpoint.split('/');
        const entity = parts[parts.length - 1] || 'ALL';
        url = `${apiRoot}/api/v1/replica/catalog/semantic-search?q=${encodeURIComponent(
          semanticQuery
        )}&entity_code=${entity}`;
      }

      const res = await fetch(url, { cache: 'no-store' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      if (Array.isArray(json)) {
        setData(json);
      } else if (json && typeof json === 'object') {
        setData([json]);
      } else {
        setData([]);
      }
    } catch {
      setError(`Gagal memuat data dari ${endpoint}. Pastikan backend FastAPI aktif.`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isOpen) return;
    setSearchQuery('');
    fetchData();
  }, [isOpen, endpoint, isSemanticMode]);

  const handleSemanticSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isSemanticMode) {
      fetchData(searchQuery);
    }
  };

  // Filter lokal jika mode standar (non-semantik)
  const filteredData = isSemanticMode
    ? data
    : data.filter((item) => {
        if (!searchQuery.trim()) return true;
        const q = searchQuery.toLowerCase();
        return Object.values(item).some((val) =>
          String(val).toLowerCase().includes(q)
        );
      });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-slate-900/60 z-50 flex items-center justify-center p-4 backdrop-blur-sm transition-opacity">
      <div className="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-3xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="p-4 border-b border-slate-200 flex justify-between items-center bg-slate-50/70">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded">
                ERP Read-Replica
              </span>
              {isMasterPrice && isSemanticMode && (
                <span className="text-[10px] font-bold uppercase tracking-wider text-purple-700 bg-purple-50 border border-purple-200 px-2 py-0.5 rounded flex items-center gap-1">
                  <span>🧠</span> pgvector 384-d Cosine Active
                </span>
              )}
            </div>
            <h3 className="text-sm font-bold text-slate-900 mt-1">{title}</h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition"
          >
            &#10005;
          </button>
        </div>

        {/* Search Bar & AI Semantic Controls */}
        <div className="p-3 border-b border-slate-100 bg-white">
          <form onSubmit={handleSemanticSubmit} className="flex flex-col sm:flex-row gap-2 items-center justify-between">
            <div className="relative w-full">
              <span className="absolute inset-y-0 left-0 pl-2.5 flex items-center pointer-events-none text-slate-400 text-xs">
                🔍
              </span>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={
                  isSemanticMode
                    ? "Cari semantik AI (cth: 'transceiver 10km optik', 'switch poe')... Tekan Enter"
                    : "Ketik untuk menyaring data seketika..."
                }
                className="w-full pl-8 pr-3 py-1.5 border border-slate-300 rounded text-xs focus:ring-1 focus:ring-blue-500 outline-none"
              />
            </div>

            {isMasterPrice && (
              <div className="flex items-center gap-2 whitespace-nowrap self-end sm:self-auto">
                <button
                  type="button"
                  onClick={() => setIsSemanticMode(!isSemanticMode)}
                  className={`px-2.5 py-1.5 rounded text-[11px] font-bold border transition flex items-center gap-1.5 ${
                    isSemanticMode
                      ? 'bg-purple-600 text-white border-purple-600 shadow-sm'
                      : 'bg-slate-100 text-slate-600 border-slate-200 hover:bg-slate-200'
                  }`}
                >
                  <span>🧠</span>
                  <span>{isSemanticMode ? 'Mode: pgvector Semantic' : 'Mode: Keyword'}</span>
                </button>
                {isSemanticMode && (
                  <button
                    type="submit"
                    className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-[11px] font-bold shadow-sm transition"
                  >
                    Cari Vektor
                  </button>
                )}
              </div>
            )}
          </form>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto text-xs space-y-3 flex-1">
          {loading && (
            <div className="p-8 text-center text-slate-500 font-semibold">
              <span className="inline-block animate-spin mr-2">&#8635;</span> Memuat data replika ERP...
            </div>
          )}

          {error && (
            <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg">
              &#9888; {error}
            </div>
          )}

          {!loading && !error && filteredData.length === 0 && (
            <div className="p-8 text-center text-slate-400">
              Tidak ada data yang cocok dengan kriteria pencarian.
            </div>
          )}

          {!loading && !error && filteredData.length > 0 && (
            <div className="border border-slate-200 rounded-lg overflow-hidden">
              <table className="w-full text-left border-collapse">
                <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                  <tr>
                    {columns.map((col) => (
                      <th key={col.key} className="p-3 whitespace-nowrap">
                        {col.label}
                      </th>
                    ))}
                    {filteredData[0]?.similarity_score !== undefined && (
                      <th className="p-3 text-center whitespace-nowrap">AI Similarity</th>
                    )}
                    <th className="p-3 text-center whitespace-nowrap">Tindakan</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {filteredData.map((item, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/80 transition">
                      {columns.map((col) => (
                        <td key={col.key} className="p-3 font-mono text-[11px]">
                          {col.format ? col.format(item[col.key]) : (
                            typeof item[col.key] === 'object' && item[col.key] !== null
                              ? JSON.stringify(item[col.key])
                              : String(item[col.key] ?? '-')
                          )}
                        </td>
                      ))}
                      {item.similarity_score !== undefined && (
                        <td className="p-3 text-center whitespace-nowrap">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            Number(item.similarity_score) >= 0.75
                              ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                              : Number(item.similarity_score) >= 0.4
                              ? 'bg-blue-100 text-blue-800 border border-blue-300'
                              : 'bg-slate-100 text-slate-700 border border-slate-300'
                          }`}>
                            {(Number(item.similarity_score) * 100).toFixed(1)}% match
                          </span>
                        </td>
                      )}
                      <td className="p-3 text-center whitespace-nowrap">
                        <button
                          onClick={() => {
                            onSelect(item);
                            onClose();
                          }}
                          className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded font-bold text-[11px] shadow-sm transition"
                        >
                          Pilih Data
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-slate-200 bg-slate-50 flex justify-between items-center text-[11px] text-slate-500">
          <span>Data terisolasi dari database transaksi utama ERP.</span>
          <button
            onClick={onClose}
            className="px-3 py-1.5 border border-slate-300 text-slate-600 hover:bg-slate-100 rounded font-semibold transition"
          >
            Tutup
          </button>
        </div>
      </div>
    </div>
  );
}

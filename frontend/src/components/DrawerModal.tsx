'use client';

import React, { useState, useEffect } from 'react';

interface DrawerModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subTitle?: string;
  payload: Record<string, any>;
  narrative: string;
  onApprove: () => void;
  onEdit: (modifiedText: string) => void;
  onDiscard: () => void;
  loading?: boolean;
}

export default function DrawerModal({
  isOpen,
  onClose,
  title,
  subTitle,
  payload,
  narrative,
  onApprove,
  onEdit,
  onDiscard,
  loading = false,
}: DrawerModalProps) {
  const [editText, setEditText] = useState(narrative);

  useEffect(() => {
    setEditText(narrative);
  }, [narrative]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-slate-900/60 z-50 flex justify-end">
      <div className="w-full max-w-xl bg-white h-full shadow-2xl p-6 flex flex-col justify-between overflow-y-auto">
        <div>
          <div className="flex justify-between items-start pb-4 border-b border-slate-200">
            <div>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200 uppercase tracking-wider">
                Human-in-the-Loop Gateway
              </span>
              <h3 className="text-base font-bold text-slate-900 mt-1">{title}</h3>
              {subTitle && <p className="text-xs text-slate-400 mt-0.5">{subTitle}</p>}
            </div>
            <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-lg p-1">&#10005;</button>
          </div>

          <div className="mt-5 space-y-4 text-xs">
            <div>
              <label className="font-bold text-slate-700 block mb-1">Payload Deterministik (Terverifikasi Python):</label>
              <pre className="p-3 bg-slate-50 border border-slate-200 rounded-lg font-mono text-[11px] text-slate-700 overflow-x-auto max-h-48">
                {JSON.stringify(payload, null, 2)}
              </pre>
            </div>

            <div>
              <label className="font-bold text-slate-700 block mb-1">Draf Narasi (Bisa Disunting):</label>
              <textarea
                rows={6}
                value={editText}
                onChange={(e) => setEditText(e.target.value)}
                className="w-full p-3 font-mono text-xs text-slate-800 bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 leading-relaxed"
              />
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-200 flex gap-2 justify-end text-xs">
          <button
            disabled={loading}
            onClick={onDiscard}
            className="px-4 py-2 border border-slate-300 text-slate-600 hover:bg-slate-50 rounded-lg font-semibold transition"
          >
            Tolak (Discard)
          </button>
          <button
            disabled={loading}
            onClick={() => onEdit(editText)}
            className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg font-bold shadow transition"
          >
            Simpan Edit & Otorisasi
          </button>
          <button
            disabled={loading}
            onClick={onApprove}
            className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold shadow transition"
          >
            {loading ? 'Memproses...' : 'Setujui & Eksekusi'}
          </button>
        </div>
      </div>
    </div>
  );
}
'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/context/AuthContext';
import UserPersonaDropdown from '@/components/UserPersonaDropdown';

interface DraftAction {
  id: string;
  agent_id: string;
  module: string;
  ref_doc: string;
  payload: Record<string, any>;
  narrative: string;
  created_at: string;
}

const AGENT_ALLOWED_ROLES: Record<string, string[]> = {
  agent_1: ['purchasing', 'admin'],
  agent_2: ['purchasing', 'admin'],
  agent_3: ['sales', 'admin'],
  agent_4: ['purchasing', 'admin'],
  agent_5: ['purchasing', 'admin'],
  agent_6: ['warehouse', 'admin'],
  agent_7: ['warehouse', 'admin'],
  agent_8: ['treasury', 'admin'],
  agent_9: ['treasury', 'admin'],
};

export default function HITLPage() {
  const { user, token, switchPersona } = useAuth();
  const [filterMode, setFilterMode] = useState<'my_queue' | 'all'>('my_queue');
  const [entity, setEntity] = useState(user?.entity_code === 'ALL' ? 'SG' : user?.entity_code || 'SG');
  const [operatorId, setOperatorId] = useState(user?.email || 'weiming.tan@batu-networks.sg');
  const [queue, setQueue] = useState<DraftAction[]>([]);
  const [selectedDraft, setSelectedDraft] = useState<DraftAction | null>(null);
  const [editText, setEditText] = useState('');
  const [loading, setLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [toastMsg, setToastMsg] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState('');
  const [hasImageError, setHasImageError] = useState(false);

  // Sinkronisasi saat persona auth berubah
  useEffect(() => {
    if (user) {
      setOperatorId(user.email);
      if (user.entity_code !== 'ALL') {
        setEntity(user.entity_code);
      }
    }
  }, [user]);

  // Update jam saat pertama kali render di client
  useEffect(() => {
    setLastUpdated(new Date().toLocaleString('id-ID', { dateStyle: 'medium', timeStyle: 'short' }) + ' WITA');
  }, []);

  const showToast = (msg: string) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 4000);
  };

  const fetchQueue = useCallback(async () => {
    try {
      setFetchError(null);
      const res = await fetch(`http://localhost:8000/api/v1/hitl/queue/${entity}`, {
        cache: 'no-store'
      });
      if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);
      const data = await res.json();
      setQueue(data);
    } catch (err: any) {
      setFetchError('Koneksi ke backend FastAPI gagal. Pastikan port 8000 aktif.');
    }
  }, [entity]);

  useEffect(() => {
    fetchQueue();
    const timer = setInterval(fetchQueue, 5000);
    return () => clearInterval(timer);
  }, [fetchQueue]);

  const handleDecision = async (decision: 'APPROVE' | 'EDIT' | 'DISCARD') => {
    if (!selectedDraft) return;
    setLoading(true);
    setActionError(null);
    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const res = await fetch('http://localhost:8000/api/v1/hitl/decision', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          draft_action_id: selectedDraft.id,
          operator_id: operatorId || (user && user.email) || 'operator@batunetworks.com',
          decision: decision,
          modified_narrative: decision === 'EDIT' ? editText : undefined,
        }),
      });

      if (!res.ok) {
        const errorJson = await res.json().catch(() => ({}));
        const detailMsg = errorJson.detail || `Gagal memproses keputusan (HTTP ${res.status}).`;
        setActionError(detailMsg);
        return;
      }

      const result = await res.json();
      showToast(`Aksi ${decision} untuk ${selectedDraft.ref_doc} sukses tercatat di Audit Trail oleh ${result.reviewed_by}!`);
      setSelectedDraft(null);
      setActionError(null);
      fetchQueue();
    } catch (err: any) {
      setActionError(err.message || 'Terjadi kesalahan sistem atau jaringan.');
    } finally {
      setLoading(false);
    }
  };

  const getAgentBadgeColor = (agentId: string) => {
    switch (agentId.toLowerCase()) {
      case 'agent_1': return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'agent_2': return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'agent_3': return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'agent_4': return 'bg-cyan-50 text-cyan-700 border-cyan-200';
      case 'agent_5': return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      case 'agent_6': return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'agent_7': return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'agent_8': return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'agent_9': return 'bg-teal-50 text-teal-700 border-teal-200';
      default: return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const currentRole = user?.role || 'operator';
  const isAdminOrAuditor = currentRole === 'admin' || currentRole === 'auditor';

  const isAuthorizedForDraft = (draft: DraftAction) => {
    const agentKey = draft.agent_id.toLowerCase().replace('-', '_');
    const allowed = AGENT_ALLOWED_ROLES[agentKey] || ['admin'];
    return isAdminOrAuditor || allowed.includes(currentRole);
  };

  const myQueue = queue.filter(isAuthorizedForDraft);
  const displayedQueue = filterMode === 'my_queue' && !isAdminOrAuditor ? myQueue : queue;

  return (
    <div className="min-h-screen bg-slate-100 text-slate-800 p-4 md:p-8 font-sans">
      <div className="max-w-7xl mx-auto space-y-6">

        {/* STANDARDIZED HEADER MATCHING DESIGN SYSTEM */}
        <header className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-5">
            <div className="flex items-center gap-3 pr-5 border-r border-slate-200">
              {!hasImageError ? (
                <img
                  src="/batu.PNG"
                  alt="Batu Networks Pte. Ltd."
                  className="h-9 w-auto object-contain"
                  onError={() => setHasImageError(true)}
                />
              ) : (
                <div className="h-9 px-2.5 bg-gradient-to-r from-blue-700 to-indigo-800 rounded-md flex items-center justify-center text-white font-extrabold text-[11px] tracking-wider shadow-sm select-none">
                  BATU NETWORKS
                </div>
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold text-slate-900 tracking-tight">Human-in-the-Loop Gateway</h1>
                <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                  Live Dispatcher
                </span>
              </div>
              <p className="text-xs text-slate-500 font-medium flex items-center gap-2 mt-0.5">
                <span className="flex items-center gap-1.5 text-emerald-600 font-semibold">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                  Multi-Agent Staging Table
                </span>
                <span className="text-slate-300">|</span>
                <span>Pre-Approval Verification Gate</span>
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-xs">
            {/* User Persona Switcher */}
            <UserPersonaDropdown />

            {/* Entity Selector */}
            <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg shadow-sm">
              <span className="text-slate-400 font-semibold">Entity:</span>
              <select
                value={entity}
                onChange={(e) => setEntity(e.target.value)}
                className="bg-transparent font-bold text-slate-800 focus:outline-none cursor-pointer"
              >
                <option value="SG">Singapore HQ (SGD/USD)</option>
                <option value="VN">Vietnam SSC (VND)</option>
                <option value="KR">Korea Branch (KRW)</option>
                <option value="IN">India Back-Office (INR)</option>
                <option value="JP">Japan Office (JPY)</option>
              </select>
            </div>

            {/* Last Updated Widget */}
            <div className="bg-slate-50 border border-slate-200 px-3 py-2 rounded-lg text-slate-600 flex items-center gap-2 shadow-sm">
              <span className="text-slate-400">&#128339;</span>
              <span>Last Updated: <strong className="text-slate-800 font-semibold">{lastUpdated}</strong></span>
            </div>
          </div>
        </header>

        {/* ERROR BANNER IF FASTAPI DOWN */}
        {fetchError && (
          <div className="bg-rose-50 border border-rose-200 text-rose-800 text-xs p-3 rounded-xl flex items-center justify-between">
            <span>&#9888; {fetchError}</span>
            <button onClick={fetchQueue} className="underline font-bold">Coba Lagi</button>
          </div>
        )}

        {/* METRICS STATS */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <div className="text-xs text-slate-400 font-semibold uppercase">
              {isAdminOrAuditor ? `Pending Drafts (${entity})` : `Menunggu Otorisasi Anda (${entity})`}
            </div>
            <div className="text-2xl font-black text-blue-600 mt-1">
              {isAdminOrAuditor ? `${queue.length} Aksi` : `${myQueue.length} Aksi`}
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              {isAdminOrAuditor ? 'Supervisi 100% antrean entitas' : `Role: ${currentRole.toUpperCase()} (Total antrean: ${queue.length})`}
            </div>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <div className="text-xs text-slate-400 font-semibold uppercase">Active Multi-Tenant</div>
            <div className="text-2xl font-black text-slate-900 mt-1">{entity} Entity</div>
            <div className="text-[11px] text-slate-500 mt-1">Isolated boundary partition</div>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <div className="text-xs text-slate-400 font-semibold uppercase">Governance Gate</div>
            <div className="text-2xl font-black text-emerald-600 mt-1">100% HITL</div>
            <div className="text-[11px] text-slate-500 mt-1">Zero-touch unapproved bypass</div>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <div className="text-xs text-slate-400 font-semibold uppercase">Audit Logging</div>
            <div className="text-2xl font-black text-purple-600 mt-1">Immutable</div>
            <div className="text-[11px] text-slate-500 mt-1">Tersimpan ke audit_trail_logs</div>
          </div>
        </div>

        {/* MAIN TABLE WITH ROLE QUEUE TABS */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden space-y-0">
          <div className="p-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50/50">
            <div className="flex items-center gap-2">
              <span className="font-bold text-xs uppercase tracking-wider text-slate-700">
                Antrean Draf Tindakan Agen ({entity})
              </span>
              <span className="px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 text-[10px] font-bold">
                Auto-Refresh 5s
              </span>
            </div>

            <div className="flex items-center gap-3">
              {/* Queue Role Filter Tabs */}
              <div className="flex items-center bg-slate-200/80 p-1 rounded-lg text-xs font-semibold">
                <button
                  onClick={() => setFilterMode('my_queue')}
                  className={`px-3 py-1.5 rounded-md transition ${
                    filterMode === 'my_queue'
                      ? 'bg-white text-slate-900 shadow-xs font-bold'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {isAdminOrAuditor ? `Semua Otorisasi (${queue.length})` : `Menunggu Otorisasi Saya (${myQueue.length})`}
                </button>
                <button
                  onClick={() => setFilterMode('all')}
                  className={`px-3 py-1.5 rounded-md transition ${
                    filterMode === 'all'
                      ? 'bg-white text-slate-900 shadow-xs font-bold'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Seluruh Antrean Entitas ({queue.length})
                </button>
              </div>

              <button
                onClick={fetchQueue}
                className="text-xs font-semibold text-blue-600 hover:text-blue-800 transition"
              >
                &#8635; Refresh
              </button>
            </div>
          </div>

          {filterMode === 'all' && !isAdminOrAuditor && (
            <div className="bg-amber-50/60 border-b border-amber-100 px-4 py-2 text-xs text-amber-900 flex items-center gap-2">
              <span>ℹ️</span>
              <span>
                Menampilkan seluruh antrean entitas. Draf dengan label <strong className="text-amber-800">Review PIC Lain</strong> dapat Anda amati (Supervisi/Eksplorasi), namun otorisasi resmi memerlukan akun dengan role departemen terkait.
              </span>
            </div>
          )}

          <div className="overflow-x-auto text-xs">
            <table className="w-full text-left border-collapse">
              <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                <tr>
                  <th className="p-3">Agen ID</th>
                  <th className="p-3">Modul ERP</th>
                  <th className="p-3">Ref Dokumen</th>
                  <th className="p-3">Draf Narasi Rekomendasi</th>
                  <th className="p-3">Wewenang Role</th>
                  <th className="p-3">Waktu Masuk</th>
                  <th className="p-3 text-center">Tindakan</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {displayedQueue.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-slate-500">
                      {filterMode === 'my_queue' && !isAdminOrAuditor ? (
                        <div className="space-y-1">
                          <p className="font-semibold text-slate-700">
                            Tidak ada draf tindakan yang menunggu otorisasi untuk role <span className="text-blue-700 uppercase">{currentRole}</span> pada entitas {entity}.
                          </p>
                          <p className="text-[11px] text-slate-400">
                            Pilih tab <button onClick={() => setFilterMode('all')} className="text-blue-600 underline font-bold">Seluruh Antrean Entitas</button> untuk memantau aktivitas draf divisi lain.
                          </p>
                        </div>
                      ) : (
                        <p>Tidak ada draf transaksi yang tertahan untuk entitas <strong>{entity}</strong>.</p>
                      )}
                    </td>
                  </tr>
                ) : (
                  displayedQueue.map((item) => {
                    const hasAuth = isAuthorizedForDraft(item);
                    const agentKey = item.agent_id.toLowerCase().replace('-', '_');
                    const allowedRoles = AGENT_ALLOWED_ROLES[agentKey] || ['admin'];

                    return (
                      <tr key={item.id} className="hover:bg-slate-50/80 transition">
                        <td className="p-3">
                          <span className={`px-2 py-1 rounded text-[10px] font-bold border ${getAgentBadgeColor(item.agent_id)}`}>
                            {item.agent_id.toUpperCase()}
                          </span>
                        </td>
                        <td className="p-3 font-semibold text-slate-900">{item.module}</td>
                        <td className="p-3 font-mono font-bold text-blue-600">{item.ref_doc}</td>
                        <td className="p-3 max-w-md truncate text-slate-600" title={item.narrative}>
                          {item.narrative}
                        </td>
                        <td className="p-3 whitespace-nowrap">
                          {hasAuth ? (
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 inline-flex items-center gap-1">
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> Siap Otorisasi
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-600 border border-slate-200">
                              PIC: {allowedRoles.join('/')}
                            </span>
                          )}
                        </td>
                        <td className="p-3 text-slate-400 whitespace-nowrap font-mono text-[11px]">
                          {new Date(item.created_at).toLocaleTimeString('id-ID')}
                        </td>
                        <td className="p-3 text-center">
                          <button
                            onClick={() => {
                              setSelectedDraft(item);
                              setEditText(item.narrative);
                              setActionError(null);
                            }}
                            className={`px-3 py-1.5 rounded-lg font-bold text-[11px] shadow-sm transition ${
                              hasAuth
                                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                                : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-300'
                            }`}
                          >
                            {hasAuth ? 'Review & Otorisasi' : 'Lihat Detail'}
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>

      {/* SLIDE-OVER HITL DRAWER */}
      {selectedDraft && (() => {
        const agentKey = selectedDraft.agent_id.toLowerCase().replace('-', '_');
        const allowedRoles = AGENT_ALLOWED_ROLES[agentKey] || ['admin'];
        const userRole = user?.role || 'operator';
        const hasPermission = userRole === 'admin' || allowedRoles.includes(userRole);

        return (
          <div className="fixed inset-0 bg-slate-900/60 z-50 flex justify-end transition-opacity">
            <div className="w-full max-w-xl bg-white h-full shadow-2xl p-6 flex flex-col justify-between overflow-y-auto">
              <div className="space-y-4">
                <div className="flex justify-between items-start pb-4 border-b border-slate-200">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200 uppercase tracking-wider">
                        Human-in-the-Loop Gateway
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getAgentBadgeColor(selectedDraft.agent_id)}`}>
                        {selectedDraft.agent_id.toUpperCase()}
                      </span>
                    </div>
                    <h3 className="text-base font-bold text-slate-900 mt-1">
                      Review Transaksi: {selectedDraft.ref_doc}
                    </h3>
                    <p className="text-xs text-slate-400">
                      Modul ERP: <strong className="text-slate-700">{selectedDraft.module}</strong> &bull; Entitas Hukum: <strong className="text-slate-700">{entity}</strong>
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setSelectedDraft(null);
                      setActionError(null);
                    }}
                    className="text-slate-400 hover:text-slate-600 text-lg p-1 rounded-md hover:bg-slate-100 transition"
                  >
                    &#10005;
                  </button>
                </div>

                {/* RBAC ROLE PERMISSION NOTICE IF UNAUTHORIZED */}
                {!hasPermission && (
                  <div className="p-3 bg-amber-50 border border-amber-300 rounded-xl text-amber-900 text-xs space-y-2">
                    <div className="flex items-center gap-2 font-bold text-amber-800">
                      <span className="text-base leading-none">&#9888;</span>
                      <span>Pemisahan Tugas Korporat (Segregation of Duties - RBAC):</span>
                    </div>
                    <p className="text-slate-700 leading-relaxed text-[11px]">
                      Persona aktif Anda adalah <strong>{user?.full_name} ({userRole.toUpperCase()})</strong>.
                      Otorisasi modul <strong>{selectedDraft.agent_id.toUpperCase()}</strong> ini memerlukan hak peran <strong>{allowedRoles.map(r => r.toUpperCase()).join(' atau ')}</strong>.
                    </p>
                    <div className="pt-1 flex flex-wrap gap-2">
                      {allowedRoles.includes('purchasing') && (
                        <button
                          type="button"
                          onClick={async () => {
                            await switchPersona('sg_purchaser');
                            setActionError(null);
                          }}
                          className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded font-bold text-[11px] shadow-sm transition flex items-center gap-1"
                        >
                          ⚡ Beralih ke Purchasing (Tan Wei Ming)
                        </button>
                      )}
                      {allowedRoles.includes('sales') && (
                        <button
                          type="button"
                          onClick={async () => {
                            await switchPersona('sg_sales');
                            setActionError(null);
                          }}
                          className="px-2.5 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded font-bold text-[11px] shadow-sm transition flex items-center gap-1"
                        >
                          ⚡ Beralih ke Sales (Clara Lim)
                        </button>
                      )}
                      {allowedRoles.includes('warehouse') && (
                        <button
                          type="button"
                          onClick={async () => {
                            await switchPersona('vn_logistics');
                            setActionError(null);
                          }}
                          className="px-2.5 py-1 bg-amber-600 hover:bg-amber-700 text-white rounded font-bold text-[11px] shadow-sm transition flex items-center gap-1"
                        >
                          ⚡ Beralih ke Warehouse (Nguyen Van Thao)
                        </button>
                      )}
                      {allowedRoles.includes('treasury') && (
                        <button
                          type="button"
                          onClick={async () => {
                            await switchPersona('sg_treasurer');
                            setActionError(null);
                          }}
                          className="px-2.5 py-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded font-bold text-[11px] shadow-sm transition flex items-center gap-1"
                        >
                          ⚡ Beralih ke Treasury (Marcus Goh)
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={async () => {
                          await switchPersona('admin');
                          setActionError(null);
                        }}
                        className="px-2.5 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded font-bold text-[11px] shadow-sm transition flex items-center gap-1"
                      >
                        🛡️ Beralih ke Admin
                      </button>
                    </div>
                  </div>
                )}

                {/* ERROR BANNER IF DECISION ACTION FAILED */}
                {actionError && (
                  <div className="p-3 bg-rose-50 border border-rose-300 text-rose-800 text-xs rounded-xl flex items-start gap-2.5 animate-in fade-in">
                    <span className="text-rose-600 font-bold text-base leading-none mt-0.5">&#9888;</span>
                    <div className="flex-1">
                      <strong className="block font-semibold">Otorisasi Gagal:</strong>
                      <span className="mt-0.5 block leading-relaxed">{actionError}</span>
                    </div>
                  </div>
                )}

                <div className="space-y-4 text-xs">
                  {/* DETERMINISTIC PAYLOAD VIEWER */}
                  <div>
                    <label className="font-bold text-slate-700 block mb-1">
                      Payload Deterministik (Terverifikasi Python):
                    </label>
                    <pre className="p-3 bg-slate-50 border border-slate-200 rounded-lg font-mono text-[11px] text-slate-700 overflow-x-auto max-h-48">
                      {JSON.stringify(selectedDraft.payload, null, 2)}
                    </pre>
                  </div>

                  {/* EDITABLE NARRATIVE */}
                  <div>
                    <label className="font-bold text-slate-700 block mb-1">
                      Draf Narasi (Dapat Diedit Sebelum Otorisasi):
                    </label>
                    <textarea
                      rows={6}
                      value={editText}
                      onChange={(e) => setEditText(e.target.value)}
                      className="w-full p-3 font-mono text-xs text-slate-800 bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 leading-relaxed"
                    />
                    <span className="text-[11px] text-slate-400 mt-1 block">
                      Jika diedit, teks hasil revisi dan teks asli AI akan dicatat berdampingan di log audit.
                    </span>
                  </div>

                  {/* AUDIT INFO */}
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-blue-900 text-[11px] space-y-1.5">
                    <div className="font-bold">Governance Stamp:</div>
                    <div className="flex flex-col sm:flex-row sm:items-center gap-1.5">
                      <span className="font-semibold text-slate-700">PIC Operator:</span>
                      <input
                        type="email"
                        value={operatorId}
                        onChange={(e) => setOperatorId(e.target.value)}
                        className="bg-white border border-blue-300 rounded px-2 py-1 text-xs font-mono font-medium text-slate-900 focus:outline-none focus:ring-1 focus:ring-blue-500 w-full sm:w-auto"
                        placeholder="operator@batunetworks.com"
                      />
                    </div>
                    <div>Session Partition: <strong>{entity} Database Read-Replica</strong></div>
                    <div>Persona Role: <strong className="uppercase">{userRole}</strong> {hasPermission ? '✅ (Berwenang)' : '❌ (Tidak Berwenang)'}</div>
                  </div>
                </div>
              </div>

              {/* ACTION BUTTONS (STICKY FOOTER) */}
              <div className="pt-4 border-t border-slate-200 flex flex-wrap gap-2 justify-end text-xs sticky bottom-0 bg-white z-10">
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => handleDecision('DISCARD')}
                  className="px-4 py-2 border border-slate-300 text-slate-600 hover:bg-slate-50 rounded-lg font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Tolak (Discard)
                </button>
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => handleDecision('EDIT')}
                  className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg font-bold shadow transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Simpan Edit & Otorisasi
                </button>
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => handleDecision('APPROVE')}
                  className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold shadow transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Memproses...' : 'Setujui & Eksekusi'}
                </button>
              </div>
            </div>
          </div>
        );
      })()}

      {/* FLOATING TOAST NOTIFICATION */}
      {toastMsg && (
        <div className="fixed bottom-5 right-5 bg-slate-900 text-white px-4 py-3 rounded-lg shadow-xl text-xs flex items-center gap-3 z-50 border border-slate-700">
          <span className="text-emerald-400 font-bold">&#10003;</span>
          <span>{toastMsg}</span>
        </div>
      )}
    </div>
  );
}
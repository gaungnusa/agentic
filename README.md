# Batu Networks ERP - Agentic AI Orchestration Engine

Sistem Agentic AI enterprise berbasis kepatuhan **Enterprise BRD v10.0**. Mengintegrasikan 9 agen cerdas lintas fungsi pengadaan, penjualan, inventaris gudang, logistik *Triangle Trade*, dan keuangan multi-valas dengan isolasi data entitas hukum (SG, VN, KR, IN, JP).

## Prinsip Arsitektur Inti
1. **Deterministic Separation of Concerns:** Seluruh kalkulasi matematis (margin kotor, penalti MOQ, selisih kurs, dan rekonsiliasi kuantitas scan) dieksekusi 100% oleh Python tanpa halusinasi LLM.
2. **Cognitive Narrative (RAG):** Anthropic Claude 3.5 bertindak murni menyusun teks komunikasi resmi berdasarkan payload JSON deterministik.
3. **Human-in-the-Loop (HITL) Gateway:** Tidak ada mutasi transaksi atau pengiriman pesan keluar yang dieksekusi tanpa persetujuan manual staf berwenang via tabel `draft_agent_actions`.
4. **Read-Only Database Replica:** Beban komputasi analitik terpisah penuh dari database transaksi utama ERP.

## Cara Menjalankan di Lingkungan Antigravity

### 1. Inisialisasi Basis Data & Cache
```bash
cd docker
podman-compose up -d
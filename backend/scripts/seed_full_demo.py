import asyncio
import asyncpg
import json
from datetime import datetime, date, timedelta

import os

DB_URL = os.getenv("DATABASE_URL", "postgresql://orchestrator_admin:AdminBatuPassword2026!@localhost:54320/batu_networks_erp_ai")

# =============================================================================
# DATA MASTER PRICE (PS03) UNTUK SIMULASI ERP READ-REPLICA
# =============================================================================
MOCK_MASTER_PRICES = [
    ("SFP-10G-LR", "SFP+ 10G-LR Transceiver Module", 38.50, "USD", 100, date(2026, 12, 31), "SG"),
    ("OP-CABLE-48C", "High-Density Armored Patch Cord 48C", 108.50, "USD", 500, date(2026, 9, 28), "KR"),
    ("SW-CAT-9300", "Cisco Catalyst 9300 48-Port PoE+", 2850.00, "USD", 10, date(2026, 9, 25), "SG"),
    ("FUSION-FS-70", "Sumitomo Core Alignment Fusion Splicer", 5400.00, "USD", 5, date(2026, 10, 2), "JP"),
    ("PLC-SPLITTER-16", "PLC Splitter 1x16 SC/APC Micro Module", 12.80, "USD", 1000, date(2026, 11, 30), "VN"),
    ("OTDR-PRO-MAX", "Anritsu Handheld OTDR Optical Tester", 3900.00, "USD", 2, date(2026, 12, 15), "IN"),
]

# =============================================================================
# 12 DATA DRAFT TRANSAKSI PENDING (COVERING 9 AGENTS & 5 ENTITIES)
# =============================================================================
PENDING_DRAFTS = [
    # 1. Agent 1 (PS01) - Singapore (Catalog Matched)
    {
        "agent_id": "agent_1",
        "entity_code": "SG",
        "module_code": "PS01",
        "reference_doc": "RFQ-2026-0891",
        "payload": {
            "catalog_matched": True,
            "sku": "SFP-10G-LR",
            "unit_cost": 38.50,
            "target_margin_pct": 18.0,
            "recommended_quote_price": 46.95,
            "action_required": "GENERATE_CUSTOMER_QUOTE"
        },
        "narrative": (
            "Agent 1 mendeteksi part SFP-10G-LR cocok dengan Master Price PS03 ($38.50). "
            "Draf penawaran resmi untuk Singtel Optus telah disusun dengan target margin 18% "
            "(Harga jual: $46.95/unit untuk volume 500 pcs)."
        )
    },
    # 2. Agent 1 (PS01) - Vietnam (Non-Catalog / Sourcing Parallel)
    {
        "agent_id": "agent_1",
        "entity_code": "VN",
        "module_code": "PS01",
        "reference_doc": "RFQ-2026-0894",
        "payload": {
            "catalog_matched": False,
            "sku": "CUSTOM-ARMORED-FIBER-96C",
            "unit_cost": None,
            "target_margin_pct": 20.0,
            "action_required": "DISPATCH_PARALLEL_SOURCING_RFQ"
        },
        "narrative": (
            "Agent 1 mengidentifikasi permintaan SKU non-katalog dari Viettel. "
            "Draf paket inquiry sourcing paralel otomatis disiapkan untuk 3 vendor rekanan: "
            "Amphenol SG, Molex APAC, dan CommScope Japan."
        )
    },
    # 3. Agent 2 (PS02) - Korea (Margin Breach & MOQ Breach)
    {
        "agent_id": "agent_2",
        "entity_code": "KR",
        "module_code": "PS02",
        "reference_doc": "PO-2026-4412",
        "payload": {
            "so_number": "SO-2026-1182",
            "supplier_name": "Broadcom APAC",
            "so_selling_price": 120.00,
            "po_cost_price": 108.50,
            "gross_margin_pct": 9.58,
            "is_margin_breached": True,
            "ordered_qty": 350,
            "supplier_moq": 500,
            "is_moq_breached": True,
            "remedy": {
                "suggested_qty": 500,
                "tier_price": 94.00,
                "projected_margin": 21.67,
                "buffer_stock_qty": 150
            }
        },
        "narrative": (
            "PERINGATAN MARGIN & MOQ: PO-2026-4412 memiliki gross margin hanya 9.58% (di bawah batas min 15%) "
            "dan kuantitas pesanan 350 pcs melanggar MOQ Broadcom (500 pcs). PO dikunci sementara. "
            "Direkomendasikan menaikkan order ke 500 pcs (Tier 2 @ $94.00) untuk memulihkan margin ke 21.67%."
        )
    },
    # 4. Agent 2 (PS02) - Singapore (Margin Tipis)
    {
        "agent_id": "agent_2",
        "entity_code": "SG",
        "module_code": "PS02",
        "reference_doc": "PO-2026-4418",
        "payload": {
            "so_number": "SO-2026-1199",
            "supplier_name": "Cisco Systems SG",
            "so_selling_price": 8500.00,
            "po_cost_price": 7800.00,
            "gross_margin_pct": 8.24,
            "is_margin_breached": True,
            "ordered_qty": 5,
            "supplier_moq": 5,
            "is_moq_breached": False,
            "remedy": None
        },
        "narrative": (
            "PO-2026-4418 terdeteksi erosi margin (8.24% vs target 15.00%). "
            "Kuantitas memenuhi MOQ, namun harga beli vendor mengalami kenaikan sepihak. "
            "Membutuhkan persetujuan manajerial khusus untuk bypass margin kotor."
        )
    },
    # 5. Agent 3 (PS06/07) - India (Backlog Delivery Delay)
    {
        "agent_id": "agent_3",
        "entity_code": "IN",
        "module_code": "PS06",
        "reference_doc": "SO-2026-7719",
        "payload": {
            "client_name": "Tata Communications",
            "target_rdd": "2026-08-20",
            "eta_forwarder": "2026-09-12",
            "delta_days": 23,
            "severity": "CRITICAL",
            "order_value_usd": 42000.00,
            "needs_escalation": True
        },
        "narrative": (
            "ESKALASI KRITIS: SO-2026-7719 mengalami keterlambatan penyerahan barang selama 23 hari "
            "terhadap target RDD kontrak. Nilai komitmen $42,000 USD berisiko terkena denda penalti SLA 1.5%/pekan. "
            "Draf memo eskalasi ke VP Logistics India siap disetujui."
        )
    },
    # 6. Agent 4 (PS03) - Singapore (Price Book Expiring H-25)
    {
        "agent_id": "agent_4",
        "entity_code": "SG",
        "module_code": "PS03",
        "reference_doc": "MP-CS-2026-Q2",
        "payload": {
            "vendor_name": "Cisco Systems APAC",
            "valid_until": "2026-09-30",
            "days_remaining": 25,
            "items_count": 45,
            "recommended_inflation_adjustment_pct": 2.1,
            "export_format": "ERP_EXCEL_TEMPLATE"
        },
        "narrative": (
            "Agent 4 mendeteksi katalog harga Cisco APAC (45 SKU) kedaluwarsa dalam 25 hari (H-25). "
            "Paket pembaruan harga kuartal Q4 2026 telah disiapkan dengan indeks inflasi +2.1%. "
            "Template mass-upload Excel resmi siap diekspor untuk negosiasi vendor."
        )
    },
    # 7. Agent 4 (PS03) - Japan (Price Book Expiring H-27)
    {
        "agent_id": "agent_4",
        "entity_code": "JP",
        "module_code": "PS03",
        "reference_doc": "MP-SUM-2026-Q3",
        "payload": {
            "vendor_name": "Sumitomo Electric JP",
            "valid_until": "2026-10-02",
            "days_remaining": 27,
            "items_count": 18,
            "recommended_inflation_adjustment_pct": 1.8
        },
        "narrative": (
            "Katalog harga alat sambung optik Sumitomo JP memasuki siklus kedaluwarsa H-27. "
            "Draf pengajuan perpanjangan masa berlaku 90 hari format JPY telah disusun."
        )
    },
    # 8. Agent 5 (PS07) - Vietnam (Vendor Evaluation Score)
    {
        "agent_id": "agent_5",
        "entity_code": "VN",
        "module_code": "PS07",
        "reference_doc": "VEND-VN-042",
        "payload": {
            "vendor_name": "Hanoi Fiber Cabling JSC",
            "on_time_rate": 65.0,
            "quality_rate": 72.0,
            "composite_score": 67.8,
            "vendor_tier": "TIER_3_RESTRICTED",
            "suggested_allocation_pct": 0,
            "is_eligible_for_po": False
        },
        "narrative": (
            "Evaluasi performa triwulan vendor Hanoi Fiber Cabling menghasilkan skor komposit 67.8 (Tier 3). "
            "Agent 5 merekomendasikan pembekuan kuota alokasi pengadaan (0%) untuk tender berikutnya "
            "akibat tingginya rasio cacat fisik barang di dermaga penerimaan."
        )
    },
    # 9. Agent 6 (IN01) - Singapore (Damaged Inbound Dock Scan)
    {
        "agent_id": "agent_6",
        "entity_code": "SG",
        "module_code": "IN01",
        "reference_doc": "PO-2026-9902",
        "payload": {
            "po_expected_qty": 1000,
            "scanned_total": 1000,
            "valid_gr_qty": 920,
            "damaged_qty": 80,
            "unit_cost": 39.00,
            "rma_required": True,
            "debit_claim_amount": 3120.00
        },
        "narrative": (
            "DISKREPANSI FISIK GUDANG: Dari 1,000 pcs modul transreceiver yang tiba di dermaga Tuas, "
            "80 pcs ditemukan cacat fisik akibat kelembaban peti kemas. "
            "Agent 6 memisahkan alur otomatis: 920 pcs diposting Partial GR ke stok aktif, "
            "dan berkas klaim RMA serta Debit Note sebesar $3,120.00 USD diterbitkan ke vendor."
        )
    },
    # 10. Agent 7 (BRD 6.3) - Singapore (Triangle Trade Direct Delivery)
    {
        "agent_id": "agent_7",
        "entity_code": "SG",
        "module_code": "6.3_TT",
        "reference_doc": "PO-8812",
        "payload": {
            "so_reference": "SO-3310",
            "route": "Furukawa Tokyo -> FPT Telecom Danang",
            "pod_verified": True,
            "posting_eligible": True,
            "warehouse_mutation_required": False
        },
        "narrative": (
            "Pengiriman langsung Triangle Trade (Furukawa ke FPT Danang) telah diverifikasi "
            "melalui resi forwarder DHL Express. Dokumen POD valid. "
            "Agent 7 siap mengeksekusi sinkronisasi posting Logical GR dan Logical GI serentak "
            "dengan saldo inventaris transit nol, membypass mutasi fisik gudang Singapura."
        )
    },
    # 11. Agent 8 (AC02) - Singapore (AR/AP Clearing & FX Loss)
    {
        "agent_id": "agent_8",
        "entity_code": "SG",
        "module_code": "AC02",
        "reference_doc": "TXN-DBS-88319",
        "payload": {
            "bank_account": "DBS USD Operating",
            "remittance_amount_usd": 74500.00,
            "matched_invoices": ["INV-2026-0412", "INV-2026-0413"],
            "invoice_book_rate": 1.350,
            "bank_settlement_rate": 1.342,
            "book_value_sgd": 100575.00,
            "settle_value_sgd": 99979.00,
            "fx_variance_sgd": -596.00,
            "fx_type": "LOSS",
            "allocated_account": "7210"
        },
        "narrative": (
            "Penerimaan dana pelanggan $74,500.00 USD telah dicocokkan 100% dengan invoice INV-0412 & 0413. "
            "Perbedaan kurs buku (1.350) vs kurs realisasi DBS (1.342) menimbulkan Realized FX Loss sebesar SGD -596.00. "
            "Voucher jurnal kliring berimbang ganda dialokasikan ke Akun 7210 siap diposting ke General Ledger."
        )
    },
    # 12. Agent 9 (AC01/02) - Vietnam (Cash Runway Deficit)
    {
        "agent_id": "agent_9",
        "entity_code": "VN",
        "module_code": "AC01",
        "reference_doc": "CASH-RUNWAY-VN",
        "payload": {
            "current_cash_vnd": 1200000000.0,
            "weekly_burn_rate_vnd": 450000000.0,
            "loan_due_7days_vnd": 500000000.0,
            "net_usable_cash_vnd": 700000000.0,
            "weeks_runway": 1.5,
            "liquidity_status": "CRITICAL_DEFICIT",
            "alert_treasury_lead": True
        },
        "narrative": (
            "PERINGATAN LIKUIDITAS: Ketahanan kas operasional cabang Vietnam berada di level kritis (1.5 minggu runway) "
            "akibat jadwal pelunasan fasilitas pinjaman bank Open Account sebesar VND 500 Juta dalam 7 hari ke depan. "
            "Agent 9 menyarankan penarikan fasilitas subordinasi kas inter-company dari Singapore HQ."
        )
    }
]

# =============================================================================
# DATA AUDIT TRAIL HISTORIS (CONTOH AKSI SEBELUMNYA)
# =============================================================================
HISTORICAL_LOGS = [
    {
        "operator_id": "eko.suryahadi@batunetworks.com",
        "entity_code": "SG",
        "event_action": "APPROVED",
        "original_text": "Agent 1: Quotation response draft for Singtel RFQ-2026-0810.",
        "final_text": "Agent 1: Quotation response draft for Singtel RFQ-2026-0810.",
        "execution_result": {"status": "DISPATCHED", "type": "EMAIL_SENT", "timestamp": "2026-09-04T14:20:00Z"}
    },
    {
        "operator_id": "eko.suryahadi@batunetworks.com",
        "entity_code": "KR",
        "event_action": "EDITED_AND_APPROVED",
        "original_text": "Agent 2: PO-2026-4401 MOQ breach notice.",
        "final_text": "Agent 2: PO-2026-4401 MOQ breach notice (Manually verified with Procurement Director).",
        "execution_result": {"status": "DISPATCHED", "type": "ERP_PO_MUTATION", "timestamp": "2026-09-04T16:45:00Z"}
    },
    {
        "operator_id": "finance.officer@batunetworks.com",
        "entity_code": "SG",
        "event_action": "DISCARDED",
        "original_text": "Agent 8: Bank matching TXN-DBS-88100.",
        "final_text": "Discarded due to duplicate transaction feed.",
        "execution_result": {"status": "DISCARDED_NO_ACTION", "timestamp": "2026-09-05T09:10:00Z"}
    }
]

async def run_seed():
    print("=== Menghubungkan ke PostgreSQL Antigravity ===")
    try:
        conn = await asyncpg.connect(DB_URL)
    except Exception as e:
        print(f"✗ Gagal koneksi database: {e}")
        print("Pastikan kontainer Postgres aktif via: cd docker && podman-compose up -d")
        return

    print("=== 1. Mengisi Tabel Katalog mock_master_price (PS03) ===")
    for item in MOCK_MASTER_PRICES:
        await conn.execute(
            """
            INSERT INTO mock_master_price 
            (part_number, description, unit_cost, currency, moq_threshold, valid_until, entity_code)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (part_number) DO UPDATE 
            SET unit_cost = EXCLUDED.unit_cost, valid_until = EXCLUDED.valid_until;
            """,
            item[0], item[1], item[2], item[3], item[4], item[5], item[6]
        )
    print(f"✓ Berhasil memuat {len(MOCK_MASTER_PRICES)} katalog harga master.")

    print("\n=== 2. Membersihkan & Mengisi Antrean Staging draft_agent_actions ===")
    await conn.execute("DELETE FROM draft_agent_actions WHERE status = 'PENDING';")
    
    for draft in PENDING_DRAFTS:
        row_id = await conn.fetchval(
            """
            INSERT INTO draft_agent_actions 
            (agent_id, entity_code, module_code, reference_doc, deterministic_payload, llm_draft_narrative, status)
            VALUES ($1, $2, $3, $4, $5, $6, 'PENDING')
            RETURNING id;
            """,
            draft["agent_id"],
            draft["entity_code"],
            draft["module_code"],
            draft["reference_doc"],
            json.dumps(draft["payload"]),
            draft["narrative"]
        )
        print(f"✓ [{draft['entity_code']}] {draft['agent_id'].upper()} ({draft['reference_doc']}) -> Staged ID: {row_id}")

    print("\n=== 3. Mengisi Tabel Riwayat Kepatuhan audit_trail_logs ===")
    for log in HISTORICAL_LOGS:
        await conn.execute(
            """
            INSERT INTO audit_trail_logs 
            (operator_id, entity_code, event_action, original_text, final_dispatched_text, execution_result)
            VALUES ($1, $2, $3, $4, $5, $6);
            """,
            log["operator_id"],
            log["entity_code"],
            log["event_action"],
            log["original_text"],
            log["final_text"],
            json.dumps(log["execution_result"])
        )
    print(f"✓ Berhasil memuat {len(HISTORICAL_LOGS)} log audit historis.")

    await conn.close()
    print("\n=======================================================")
    print("SEEDING SUKSES! Buka http://localhost:3000/hitl")
    print("Coba ganti dropdown cabang: SG, VN, KR, IN, JP.")
    print("=======================================================")

if __name__ == "__main__":
    asyncio.run(run_seed())
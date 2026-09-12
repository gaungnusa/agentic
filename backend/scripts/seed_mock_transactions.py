import asyncio
import httpx

API_BASE = "http://localhost:8000/api/v1/agents"

SAMPLE_TRANSACTIONS = [
    # 1. Agent 1 (Quotation Katalog Ada) - SG
    {
        "endpoint": "/agent-1/process-rfq",
        "payload": {
            "entity_code": "SG",
            "reference_doc": "RFQ-2026-0891",
            "unit_cost": 38.50,
            "target_margin_pct": 18.0
        }
    },
    # 2. Agent 1 (Quotation Part Baru / Kosong) - VN
    {
        "endpoint": "/agent-1/process-rfq",
        "payload": {
            "entity_code": "VN",
            "reference_doc": "RFQ-2026-0894",
            "unit_cost": None,
            "target_margin_pct": 20.0
        }
    },
    # 3. Agent 2 (Margin Erosi & Pelanggaran MOQ) - KR
    {
        "endpoint": "/agent-2/validate-po",
        "payload": {
            "entity_code": "KR",
            "reference_doc": "PO-2026-4412",
            "so_number": "SO-2026-1182",
            "supplier_name": "Broadcom APAC",
            "so_selling_price": 120.00,
            "po_cost_price": 108.50,
            "ordered_qty": 350,
            "supplier_moq": 500,
            "tier2_cost_price": 94.00
        }
    },
    # 4. Agent 6 (Penerimaan Gudang Sebagian Rusak) - SG
    {
        "endpoint": "/agent-6/handle-gr",
        "payload": {
            "entity_code": "SG",
            "reference_doc": "PO-2026-9902",
            "po_expected_qty": 1000,
            "scanned_qty": 1000,
            "damaged_qty": 80,
            "unit_cost": 39.00
        }
    },
    # 5. Agent 7 (Triangle Trade POD Masuk) - SG
    {
        "endpoint": "/agent-7/verify-triangle",
        "payload": {
            "entity_code": "SG",
            "po_ref": "PO-8812",
            "so_ref": "SO-3310",
            "is_pod_received": True
        }
    },
    # 6. Agent 8 (Kliring Bank & FX Loss Valas) - SG
    {
        "endpoint": "/agent-8/reconcile-bank",
        "payload": {
            "entity_code": "SG",
            "reference_doc": "TXN-DBS-88319",
            "bank_account_ref": "DBS USD Main",
            "remittance_amount": 74500.00,
            "remittance_currency": "USD",
            "target_invoices": ["INV-2026-0412", "INV-2026-0413"],
            "invoice_book_rate": 1.350,
            "bank_settlement_rate": 1.342
        }
    }
]

async def seed_data():
    async with httpx.AsyncClient(timeout=15.0) as client:
        print("--- Memulai Seeding Data Antrean Transaksi ---")
        for tx in SAMPLE_TRANSACTIONS:
            try:
                res = await client.post(f"{API_BASE}{tx['endpoint']}", json=tx["payload"])
                if res.status_code == 200:
                    data = res.json()
                    print(f"✓ Berhasil: {tx['payload']['reference_doc']} ({tx['payload']['entity_code']}) -> Draft ID: {data['draft_action_id']}")
                else:
                    print(f"✗ Gagal {tx['payload']['reference_doc']}: HTTP {res.status_code} - {res.text}")
            except Exception as e:
                print(f"✗ Error koneksi pada {tx['payload']['reference_doc']}: {e}")
        print("--- Seeding Selesai! Silakan cek antrean di UI Next.js / Swagger Docs ---")

if __name__ == "__main__":
    asyncio.run(seed_data())
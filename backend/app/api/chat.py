"""
Batu Networks ERP - Chat Orchestrator API
Module: backend/app/api/chat.py

Single conversational endpoint that classifies user intent, extracts parameters,
routes to the correct deterministic agent engine, and returns structured responses
with rich cards for the chat-first frontend.
"""

import json
import logging
import uuid
import httpx
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends

from app.core.config import settings
from app.core.database import get_pool
from app.core.auth import get_current_user, AGENT_ROLE_PERMISSIONS
from app.schemas.agent_payloads import ChatRequest, ChatResponse
from app.engine.deterministic import (
    compute_agent1_rfq_pricing,
    compute_agent2_po_margin,
    compute_agent3_rdd_delay,
    compute_agent4_price_validity,
    compute_agent5_vendor_score,
    compute_agent6_gr_split,
    compute_agent7_triangle_pod,
    compute_agent7_loan_maturity,
    compute_agent8_fx_split,
    compute_agent9_cash_runway
)
from app.engine.llm_synthesizer import generate_grounded_draft
from app.engine.semantic_search import search_catalog_semantic

logger = logging.getLogger("chat_orchestrator")
logger.setLevel(logging.INFO)

router = APIRouter(prefix="/api/v1/chat", tags=["Chat Orchestrator"])

# ============================================================================
# INTENT CLASSIFICATION PROMPT
# ============================================================================
INTENT_SYSTEM_PROMPT = """Anda adalah AI Intent Classifier untuk Batu Networks ERP System.
Tugas Anda: menganalisis pesan pengguna dan mengekstrak intent + parameter.

Anda HARUS merespons dalam format JSON saja, tanpa markdown atau teks lain.

Intent yang tersedia:
- "agent_1": RFQ pricing / quotation / penawaran harga / cari part di katalog
- "agent_2": Validasi margin PO/SO / cek mismatch harga / MOQ check
- "agent_3": Cek backlog / delay pengiriman / RDD vs ETA / keterlambatan
- "agent_4": Price validity radar / renewal katalog / kontrak harga kedaluwarsa / master price book
- "agent_5": Evaluasi vendor / skor performa supplier / vendor scoring
- "agent_6": Goods receipt / penerimaan gudang / barang rusak / RMA
- "agent_7_triangle": Triangle trade / POD forwarder / logical GR/GI
- "agent_7_loan": Pinjaman stok / borrowed stock / loan maturity
- "agent_8": Rekonsiliasi bank / selisih kurs / FX variance / valas
- "agent_9": Cash flow / runway kas / likuiditas / cash runway
- "hitl_queue": Lihat antrean HITL / pending approval / draf menunggu
- "audit_trail": Lihat audit trail / riwayat keputusan / log audit
- "switch_entity": Beralih atau ganti entitas bisnis aktif (SG, VN, KR, IN, JP)
- "general": Pertanyaan umum / sapaan / bantuan / tidak jelas

Parameter yang harus diekstrak (jika ada dalam pesan):
- reference_doc: nomor dokumen (PO-xxx, SO-xxx, RFQ-xxx, TXN-xxx, LOAN-xxx, MP-xxx)
- entity_code: kode entitas (SG, VN, KR, IN, JP)
- target_entity: kode entitas tujuan jika berniat ganti entitas (SG, VN, KR, IN, JP)
- angka/nilai yang disebutkan

- angka/nilai yang disebutkan

Contoh output:
{"intent": "agent_3", "params": {"reference_doc": "SO-2026-4401", "rdd_target": "2026-09-01", "eta": "2026-09-21", "order_value": 46000}, "confidence": 0.9}
{"intent": "agent_9", "params": {}, "confidence": 0.85}
{"intent": "general", "params": {}, "confidence": 1.0}
{"intent": "hitl_queue", "params": {}, "confidence": 0.95}

Respons HANYA JSON. Tidak ada teks tambahan."""

# ============================================================================
# IN-MEMORY FALLBACK DATASETS (used when Docker/Postgres container is offline)
# ============================================================================
IN_MEMORY_CONVERSATIONS: List[Dict[str, Any]] = []
IN_MEMORY_MESSAGES: Dict[str, List[Dict[str, Any]]] = {}
IN_MEMORY_DRAFTS: List[Dict[str, Any]] = [
    {
        "id": "11111111-2222-3333-4444-555555555551",
        "agent_id": "agent_2",
        "entity_code": "SG",
        "module_code": "PS02",
        "reference_doc": "PO-2026-4412",
        "deterministic_payload": {
            "gross_margin_pct": 8.7,
            "margin_status": "BELOW_TARGET",
            "moq_penalty": 2100.0,
            "approval_required": True
        },
        "llm_draft_narrative": "PO-2026-4412 terindikasi memiliki margin 8.7% di bawah threshold 15%. Rekomendasi negosiasi MOQ tier 2.",
        "status": "PENDING",
        "created_at": datetime.now().isoformat()
    },
    {
        "id": "11111111-2222-3333-4444-555555555552",
        "agent_id": "agent_3",
        "entity_code": "SG",
        "module_code": "PS06",
        "reference_doc": "SO-2026-4401",
        "deterministic_payload": {
            "rdd_delay_days": 20,
            "delay_severity": "HIGH",
            "needs_escalation": True,
            "order_value": 46000.0
        },
        "llm_draft_narrative": "Pesanan SO-2026-4401 diperkirakan terlambat 20 hari dari RDD target (01 Sep -> 21 Sep 2026). Segera berikan notifikasi ke Singtel Enterprise.",
        "status": "PENDING",
        "created_at": datetime.now().isoformat()
    }
]
IN_MEMORY_AUDIT: List[Dict[str, Any]] = [
    {
        "id": "22222222-3333-4444-5555-666666666661",
        "operator": "sg_purchaser",
        "action": "APPROVED",
        "agent": "agent_1",
        "module": "PS01",
        "ref_doc": "RFQ-2026-8801",
        "entity_code": "SG",
        "time": datetime.now().isoformat()
    }
]

IN_MEMORY_MASTER_PRICE = [
    {"part_number": "SFP-10G-LR", "description": "SFP+ 10G-LR Transceiver Module 10km", "unit_cost": 38.50, "currency": "USD", "moq_threshold": 100, "entity_code": "SG"},
    {"part_number": "OP-CABLE-48C", "description": "High-Density Patch Cord 48C Custom", "unit_cost": 108.50, "currency": "USD", "moq_threshold": 500, "entity_code": "KR"},
    {"part_number": "QSFP-100G-SR4", "description": "QSFP28 100G-SR4 Multi-Mode Optical Transceiver", "unit_cost": 185.00, "currency": "USD", "moq_threshold": 50, "entity_code": "SG"},
    {"part_number": "FIBER-OM4-12C", "description": "Indoor OM4 Fiber Optic Trunk Cable 12C", "unit_cost": 450000.00, "currency": "VND", "moq_threshold": 200, "entity_code": "VN"},
    {"part_number": "SWITCH-ACC-48P", "description": "Enterprise Gigabit Access Switch 48-Port PoE+", "unit_cost": 85000.00, "currency": "INR", "moq_threshold": 20, "entity_code": "IN"},
    {"part_number": "DWDM-MUX-16CH", "description": "16-Channel Dense Wavelength Division Mux", "unit_cost": 320000.00, "currency": "JPY", "moq_threshold": 10, "entity_code": "JP"}
]

IN_MEMORY_POS = [
    {"po_number": "PO-2026-4412", "so_number": "SO-2026-4401", "supplier_name": "Innolight Technology Corp", "part_number": "SFP-10G-LR", "ordered_qty": 450, "supplier_moq": 500, "po_cost_price": 42.00, "tier2_cost_price": 38.50, "status": "DOCK_SCAN", "entity_code": "SG"},
    {"po_number": "PO-2026-9902", "so_number": "SO-2026-9021", "supplier_name": "Foxconn Interconnect", "part_number": "QSFP-100G-SR4", "ordered_qty": 200, "supplier_moq": 100, "po_cost_price": 190.00, "tier2_cost_price": 185.00, "status": "CONFIRMED", "entity_code": "SG"}
]

IN_MEMORY_SOS = [
    {"so_number": "SO-2026-4401", "customer_name": "Singtel Enterprise Ltd", "part_number": "SFP-10G-LR", "ordered_qty": 1000, "selling_price": 46.00, "order_value": 46000.00, "rdd_target": "2026-09-01", "eta_delivery": "2026-09-21", "entity_code": "SG"},
    {"so_number": "SO-2026-1182", "customer_name": "Korea Telecom Infra", "part_number": "OP-CABLE-48C", "ordered_qty": 500, "selling_price": 145.00, "order_value": 72500.00, "rdd_target": "2026-09-15", "eta_delivery": "2026-09-14", "entity_code": "KR"},
    {"so_number": "SO-2026-9021", "customer_name": "StarHub Data Networks", "part_number": "QSFP-100G-SR4", "ordered_qty": 150, "selling_price": 240.00, "order_value": 36000.00, "rdd_target": "2026-08-20", "eta_delivery": "2026-09-25", "entity_code": "SG"}
]

IN_MEMORY_LOANS = [
    {"loan_ref": "LOAN-2026-SG-01", "partner_name": "Singtel Network Services", "part_number": "SFP-10G-LR", "qty": 150, "borrowed_date": "2026-08-10", "max_loan_days": 30, "status": "ACTIVE", "entity_code": "SG"},
    {"loan_ref": "LOAN-2026-KR-02", "partner_name": "SK Telecom Infra Tech", "part_number": "OP-CABLE-48C", "qty": 80, "borrowed_date": "2026-08-25", "max_loan_days": 30, "status": "ACTIVE", "entity_code": "KR"},
    {"loan_ref": "LOAN-2026-VN-03", "partner_name": "Viettel Network Logistics", "part_number": "FIBER-OM4-12C", "qty": 300, "borrowed_date": "2026-08-01", "max_loan_days": 30, "status": "ACTIVE", "entity_code": "VN"}
]

IN_MEMORY_VENDORS = [
    {"vendor_code": "V-CISCO-01", "vendor_name": "Cisco Systems Asia", "on_time_rate": 96.5, "quality_rate": 99.1, "price_variance_pct": -2.3, "entity_code": "SG"},
    {"vendor_code": "V-COMMSCOPE-02", "vendor_name": "CommScope Korea", "on_time_rate": 84.0, "quality_rate": 92.0, "price_variance_pct": 8.5, "entity_code": "KR"},
    {"vendor_code": "V-HUAWEI-03", "vendor_name": "Huawei Enterprise VN", "on_time_rate": 91.2, "quality_rate": 97.4, "price_variance_pct": 1.2, "entity_code": "VN"}
]

IN_MEMORY_CASH_FLOW = {
    "SG": {"current_cash": 1850000.00, "weekly_burn_rate": 80000.00, "loan_due_7days": 50000.00, "currency": "USD", "entity_code": "SG", "period_ref": "CASH-SG-2026-Q3"},
    "VN": {"current_cash": 14200000000.00, "weekly_burn_rate": 700000000.00, "loan_due_7days": 200000000.00, "currency": "VND", "entity_code": "VN", "period_ref": "CASH-VN-2026-Q3"},
    "KR": {"current_cash": 2400000000.00, "weekly_burn_rate": 112500000.00, "loan_due_7days": 0.0, "currency": "KRW", "entity_code": "KR", "period_ref": "CASH-KR-2026-Q3"},
    "IN": {"current_cash": 95000000.00, "weekly_burn_rate": 4500000.00, "loan_due_7days": 1000000.0, "currency": "INR", "entity_code": "IN", "period_ref": "CASH-IN-2026-Q3"},
    "JP": {"current_cash": 210000000.00, "weekly_burn_rate": 9500000.00, "loan_due_7days": 0.0, "currency": "JPY", "entity_code": "JP", "period_ref": "CASH-JP-2026-Q3"}
}

IN_MEMORY_BANK_TXNS = [
    {"txn_ref": "TXN-2026-SG-991", "remittance_amount": 50000.00, "book_rate": 1.35, "settle_rate": 1.436, "settled_amount": 71800.00, "settled_currency": "SGD", "booked_amount": 50000.00, "booked_currency": "USD", "entity_code": "SG", "target_invoices": [{"inv": "INV-2026-001", "amount": 50000}]},
    {"txn_ref": "TXN-2026-SG-992", "remittance_amount": 25000.00, "book_rate": 1.36, "settle_rate": 1.38, "settled_amount": 34500.00, "settled_currency": "SGD", "booked_amount": 25000.00, "booked_currency": "USD", "entity_code": "SG", "target_invoices": [{"inv": "INV-2026-002", "amount": 25000}]}
]

IN_MEMORY_PRICE_BOOKS = [
    {
        "book_reference": "MP-CS-2026-Q2",
        "vendor": "Cisco Systems APAC",
        "category": "Optics & SFP Modules",
        "validity": "01 Jul - 30 Sep 2026",
        "days_left": 28,
        "items_count": 45,
        "entity_code": "SG"
    },
    {
        "book_reference": "MP-FH-2026-Q3",
        "vendor": "FiberHome Optical",
        "category": "Cables & Patch Cords",
        "validity": "15 Jul - 15 Oct 2026",
        "days_left": 43,
        "items_count": 120,
        "entity_code": "SG"
    },
    {
        "book_reference": "MP-SUM-2026-Q3",
        "vendor": "Sumitomo Electric JP",
        "category": "Fusion Splicers & Toolkits",
        "validity": "01 Aug - 31 Oct 2026",
        "days_left": 59,
        "items_count": 18,
        "entity_code": "SG"
    },
    {
        "book_reference": "MP-VN-2026-Q3",
        "vendor": "Viettel Post Optical Tech",
        "category": "FTTH Passive Accessories",
        "validity": "01 Aug - 20 Oct 2026",
        "days_left": 22,
        "items_count": 64,
        "entity_code": "VN"
    }
]

# ============================================================================
# HELPER: DATA LOOKUP (DB OR IN-MEMORY FALLBACK)
# ============================================================================
async def lookup_db_data(pool, intent: str, params: dict, entity_code: str) -> Dict[str, Any]:
    """Fetch relevant data from mock ERP tables (or in-memory mock store if pool is None)."""
    ref = params.get("reference_doc", "")
    
    # -------------------------------------------------------------
    # Fallback to in-memory store if DB pool is not available
    # -------------------------------------------------------------
    if pool is None:
        if intent == "agent_2":
            po = next((p for p in IN_MEMORY_POS if p["po_number"] == ref), None)
            if not po:
                po = IN_MEMORY_POS[0] if IN_MEMORY_POS else None
            if po:
                so = next((s for s in IN_MEMORY_SOS if s["so_number"] == po.get("so_number")), None)
                return {"found": True, "source": "in_memory_po", "po": po, "so": so}
                
        elif intent == "agent_3":
            so = next((s for s in IN_MEMORY_SOS if s["so_number"] == ref or s["entity_code"] == entity_code), None)
            if not so and IN_MEMORY_SOS:
                so = IN_MEMORY_SOS[0]
            if so:
                return {"found": True, "source": "in_memory_so", "data": so}
                
        elif intent == "agent_4":
            if ref:
                book = next((b for b in IN_MEMORY_PRICE_BOOKS if b["book_reference"].upper() == ref.upper()), None)
                if book:
                    return {"found": True, "source": "in_memory_price_book", "data": book}
            books = [b for b in IN_MEMORY_PRICE_BOOKS if b["entity_code"] == entity_code or entity_code == "ALL"]
            return {"found": True, "source": "in_memory_price_books", "data": books or IN_MEMORY_PRICE_BOOKS}
                
        elif intent == "agent_5":
            v_match = next((v for v in IN_MEMORY_VENDORS if v["entity_code"] == entity_code), None)
            if not v_match:
                v_match = IN_MEMORY_VENDORS[0]
            return {"found": True, "source": "in_memory_vendors", "data": [v for v in IN_MEMORY_VENDORS if v["entity_code"] == entity_code or entity_code == "ALL"] or IN_MEMORY_VENDORS}
            
        elif intent == "agent_6":
            po = next((p for p in IN_MEMORY_POS if p["po_number"] == ref or p.get("status") == "DOCK_SCAN"), None)
            if po:
                return {"found": True, "source": "in_memory_gr", "data": po}
                
        elif intent == "agent_7_loan":
            loans = [l for l in IN_MEMORY_LOANS if l["entity_code"] == entity_code or entity_code == "ALL"]
            return {"found": True, "source": "in_memory_loans", "data": loans or IN_MEMORY_LOANS}
            
        elif intent == "agent_8":
            txn = next((t for t in IN_MEMORY_BANK_TXNS if t["txn_ref"] == ref or t["entity_code"] == entity_code), None)
            if not txn and IN_MEMORY_BANK_TXNS:
                txn = IN_MEMORY_BANK_TXNS[0]
            if txn:
                return {"found": True, "source": "in_memory_bank", "data": txn}
            
        elif intent == "agent_9":
            cash = IN_MEMORY_CASH_FLOW.get(entity_code, IN_MEMORY_CASH_FLOW.get("SG"))
            return {"found": True, "source": "in_memory_cash", "data": cash}
            
        elif intent == "agent_1":
            query = params.get("part_description", params.get("reference_doc", "")).lower()
            matches = [p for p in IN_MEMORY_MASTER_PRICE if query in p["part_number"].lower() or query in p["description"].lower()]
            if not matches:
                matches = [p for p in IN_MEMORY_MASTER_PRICE if p["entity_code"] == entity_code or entity_code == "ALL"]
            if not matches:
                matches = IN_MEMORY_MASTER_PRICE[:2]
            return {"found": True, "source": "semantic_search", "data": matches}
            
        elif intent == "hitl_queue":
            pending = [d for d in IN_MEMORY_DRAFTS if d.get("status") == "PENDING" and (d.get("entity_code") == entity_code or entity_code == "ALL")]
            return {"found": bool(pending), "source": "in_memory_hitl", "data": pending}
            
        elif intent == "audit_trail":
            audits = [a for a in IN_MEMORY_AUDIT if a.get("entity_code", entity_code) == entity_code or entity_code == "ALL"]
            return {"found": bool(audits), "source": "in_memory_audit", "data": audits or IN_MEMORY_AUDIT}

        elif intent == "list_po":
            pos = [p for p in IN_MEMORY_POS if p.get("entity_code") == entity_code or entity_code == "ALL"]
            return {"found": True, "source": "in_memory_pos", "data": pos or IN_MEMORY_POS}

        elif intent == "list_parts":
            parts = [p for p in IN_MEMORY_MASTER_PRICE if p.get("entity_code") == entity_code or entity_code == "ALL"]
            return {"found": True, "source": "in_memory_parts", "data": parts or IN_MEMORY_MASTER_PRICE}

        return {"found": False}

    # -------------------------------------------------------------
    # Active DB Pool lookup (when Postgres is online)
    # -------------------------------------------------------------
    async with pool.acquire() as conn:
        if intent == "agent_2" and ref:
            row = await conn.fetchrow(
                "SELECT * FROM mock_purchase_orders WHERE po_number = $1 AND entity_code = $2",
                ref, entity_code
            )
            if not row:
                row = await conn.fetchrow(
                    "SELECT * FROM mock_purchase_orders WHERE po_number = $1", ref
                )
            if row:
                so_row = await conn.fetchrow(
                    "SELECT * FROM mock_sales_orders WHERE so_number = $1", row["so_number"]
                ) if row.get("so_number") else None
                return {
                    "found": True, "source": "mock_purchase_orders",
                    "po": dict(row),
                    "so": dict(so_row) if so_row else None
                }
                
        elif intent == "agent_3" and ref:
            row = await conn.fetchrow(
                "SELECT * FROM mock_sales_orders WHERE so_number = $1", ref
            )
            if row:
                return {"found": True, "source": "mock_sales_orders", "data": dict(row)}
                
        elif intent == "agent_5":
            vendor_name = params.get("vendor_name", ref)
            if vendor_name:
                row = await conn.fetchrow(
                    "SELECT * FROM mock_vendors WHERE vendor_name ILIKE $1 OR vendor_code = $2",
                    f"%{vendor_name}%", vendor_name
                )
                if row:
                    return {"found": True, "source": "mock_vendors", "data": dict(row)}
            # Return all vendors for entity
            rows = await conn.fetch(
                "SELECT * FROM mock_vendors WHERE entity_code = $1 OR $1 = 'ALL'", entity_code
            )
            if rows:
                return {"found": True, "source": "mock_vendors", "data": [dict(r) for r in rows]}
                
        elif intent == "agent_6" and ref:
            row = await conn.fetchrow(
                "SELECT * FROM mock_purchase_orders WHERE po_number = $1 AND status = 'DOCK_SCAN'", ref
            )
            if row:
                return {"found": True, "source": "mock_purchase_orders", "data": dict(row)}
                
        elif intent == "agent_7_loan":
            rows = await conn.fetch(
                "SELECT * FROM mock_borrowed_stock WHERE entity_code = $1 AND status = 'ACTIVE'",
                entity_code
            )
            if rows:
                return {"found": True, "source": "mock_borrowed_stock", "data": [dict(r) for r in rows]}
                
        elif intent == "agent_8" and ref:
            row = await conn.fetchrow(
                "SELECT * FROM mock_bank_transactions WHERE txn_ref = $1", ref
            )
            if row:
                data = dict(row)
                if isinstance(data.get("target_invoices"), str):
                    data["target_invoices"] = json.loads(data["target_invoices"])
                return {"found": True, "source": "mock_bank_transactions", "data": data}
                
        elif intent == "agent_9":
            row = await conn.fetchrow(
                "SELECT * FROM mock_entity_cash WHERE entity_code = $1", entity_code
            )
            if row:
                return {"found": True, "source": "mock_entity_cash", "data": dict(row)}

        elif intent == "agent_4":
            if ref:
                book = next((b for b in IN_MEMORY_PRICE_BOOKS if b["book_reference"].upper() == ref.upper()), None)
                if book:
                    return {"found": True, "source": "price_book", "data": book}
            books = [b for b in IN_MEMORY_PRICE_BOOKS if b["entity_code"] == entity_code or entity_code == "ALL"]
            return {"found": True, "source": "price_books", "data": books or IN_MEMORY_PRICE_BOOKS}
                
        elif intent == "agent_1":
            query = params.get("part_description", params.get("reference_doc", ""))
            if query:
                results = await search_catalog_semantic(pool, query, entity_code, limit=3)
                if results:
                    return {"found": True, "source": "semantic_search", "data": results}
                    
        elif intent == "hitl_queue":
            rows = await conn.fetch(
                """SELECT id, agent_id, entity_code, module_code, reference_doc, 
                   deterministic_payload, llm_draft_narrative, created_at 
                   FROM draft_agent_actions WHERE entity_code = $1 AND status = 'PENDING'
                   ORDER BY created_at DESC LIMIT 10""",
                entity_code
            )
            items = []
            for r in rows:
                payload_raw = r["deterministic_payload"]
                if isinstance(payload_raw, str):
                    try: payload_obj = json.loads(payload_raw)
                    except: payload_obj = {}
                else:
                    payload_obj = payload_raw or {}
                items.append({
                    "id": str(r["id"]), "agent_id": r["agent_id"],
                    "module": r["module_code"], "ref_doc": r["reference_doc"],
                    "narrative": (r["llm_draft_narrative"] or "")[:150] + "...",
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None
                })
            return {"found": bool(items), "source": "draft_agent_actions", "data": items}
            
        elif intent == "audit_trail":
            rows = await conn.fetch(
                """SELECT a.id, a.operator_id, a.event_action, a.created_at,
                   d.agent_id, d.module_code, d.reference_doc
                   FROM audit_trail_logs a
                   LEFT JOIN draft_agent_actions d ON a.draft_action_id = d.id
                   WHERE a.entity_code = $1 ORDER BY a.created_at DESC LIMIT 10""",
                entity_code
            )
            items = [{
                "id": str(r["id"]), "operator": r["operator_id"],
                "action": r["event_action"], "agent": r["agent_id"] or "system",
                "module": r["module_code"] or "N/A", "ref_doc": r["reference_doc"] or "N/A",
                "time": r["created_at"].isoformat() if r["created_at"] else None
            } for r in rows]
            return {"found": bool(items), "source": "audit_trail_logs", "data": items}

        elif intent == "list_po":
            rows = await conn.fetch(
                "SELECT * FROM mock_purchase_orders WHERE entity_code = $1 OR $1 = 'ALL' ORDER BY po_number ASC LIMIT 10",
                entity_code
            )
            return {"found": bool(rows), "source": "mock_purchase_orders", "data": [dict(r) for r in rows]}

        elif intent == "list_parts":
            rows = await conn.fetch(
                "SELECT * FROM mock_master_price WHERE entity_code = $1 OR $1 = 'ALL' ORDER BY part_number ASC LIMIT 10",
                entity_code
            )
            return {"found": bool(rows), "source": "mock_master_price", "data": [dict(r) for r in rows]}
    
    return {"found": False}


# ============================================================================
# INTENT CLASSIFIER (CLAUDE API + FALLBACK)
# ============================================================================
async def classify_intent(message: str, entity_code: str) -> Dict[str, Any]:
    """Uses OpenAI-compatible (Sumopod), Ollama (local), or Claude API for intent classification. Falls back to keyword matching."""
    provider = getattr(settings, "LLM_PROVIDER", "openai_compatible").lower().strip()

    # 1. OpenAI Compatible (Sumopod / OpenAI / Groq)
    if provider in ("openai_compatible", "openai", "sumopod"):
        base_url = (getattr(settings, "OPENAI_BASE_URL", "https://ai.sumopod.com/v1") or "https://ai.sumopod.com/v1").rstrip("/")
        model_name = getattr(settings, "OPENAI_MODEL", "qwen3.7-flash-2026-07-15")
        api_key = (getattr(settings, "OPENAI_API_KEY", "") or "").strip()
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json={
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                            {"role": "user", "content": f"Entity aktif: {entity_code}\nPesan user: {message}"}
                        ],
                        "temperature": 0.1
                    }
                )
                if response.status_code == 200:
                    text = response.json()["choices"][0]["message"]["content"].strip()
                    if text.startswith("```"):
                        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                    first_brace = text.find("{")
                    last_brace = text.rfind("}")
                    if first_brace != -1 and last_brace != -1:
                        text = text[first_brace:last_brace+1]
                    return json.loads(text)
        except Exception as e:
            logger.warning(f"[CHAT] OpenAI-compatible intent classification failed ({e}). Using keyword fallback.")
            return keyword_intent_fallback(message)

    # 2. Ollama Intent Classifier
    if provider == "ollama":
        base_url = (getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434") or "http://127.0.0.1:11434").rstrip("/")
        model_name = getattr(settings, "OLLAMA_MODEL", "qwen2.5:1.5b")
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                response = await client.post(
                    f"{base_url}/v1/chat/completions",
                    json={
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                            {"role": "user", "content": f"Entity aktif: {entity_code}\nPesan user: {message}"}
                        ],
                        "temperature": 0.1
                    }
                )
                if response.status_code == 200:
                    text = response.json()["choices"][0]["message"]["content"].strip()
                    if text.startswith("```"):
                        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                    # Menangani kemungkinan output JSON diawali dengan teks bebas
                    first_brace = text.find("{")
                    last_brace = text.rfind("}")
                    if first_brace != -1 and last_brace != -1:
                        text = text[first_brace:last_brace+1]
                    return json.loads(text)
        except Exception as e:
            logger.warning(f"[CHAT] Ollama intent classification failed ({e}). Using keyword fallback.")
            return keyword_intent_fallback(message)

    # 2. Claude API Intent Classifier
    api_key = (settings.ANTHROPIC_API_KEY or "").strip()
    if api_key and api_key not in ("your_anthropic_api_key_here", "none", "null", ""):
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": settings.DEFAULT_LLM_MODEL,
                        "max_tokens": 300,
                        "system": INTENT_SYSTEM_PROMPT,
                        "messages": [{"role": "user", "content": f"Entity aktif: {entity_code}\nPesan user: {message}"}]
                    }
                )
                if response.status_code == 200:
                    text = response.json()["content"][0]["text"].strip()
                    # Clean potential markdown wrapping
                    if text.startswith("```"): 
                        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                    first_brace = text.find("{")
                    last_brace = text.rfind("}")
                    if first_brace != -1 and last_brace != -1:
                        text = text[first_brace:last_brace+1]
                    return json.loads(text)
        except Exception as e:
            logger.warning(f"[CHAT] Claude intent classification failed ({e}). Using keyword fallback.")
    
    # Keyword-based fallback
    return keyword_intent_fallback(message)


def keyword_intent_fallback(message: str) -> Dict[str, Any]:
    """Robust keyword-based intent classifier as fallback when LLM is unavailable."""
    msg = message.lower().strip()
    
    # 0. Entity switching detection (Priority check)
    import re
    entity_switch_match = re.search(
        r'(?:ganti|pindah|switch|ubah|set)\s+(?:ke\s+|entitas\s+|entity\s+)*(sg|vn|kr|in|jp|singapore|singapura|vietnam|korea|india|japan|jepang)\b',
        msg
    )
    if not entity_switch_match:
        entity_switch_match = re.search(r'\b(?:ke|to)\s+(?:entitas|entity)\s+(sg|vn|kr|in|jp)\b', msg)
    if entity_switch_match:
        raw_ent = entity_switch_match.group(1).lower()
        ent_map = {
            "sg": "SG", "singapore": "SG", "singapura": "SG",
            "vn": "VN", "vietnam": "VN",
            "kr": "KR", "korea": "KR",
            "in": "IN", "india": "IN",
            "jp": "JP", "japan": "JP", "jepang": "JP"
        }
        target_entity = ent_map.get(raw_ent, "SG")
        return {"intent": "switch_entity", "params": {"target_entity": target_entity}, "confidence": 0.95}

    # Extract reference documents
    ref_match = re.search(r'\b(PO|SO|RFQ|TXN|LOAN|MP)-[A-Za-z0-9-]+\b', message, re.IGNORECASE)
    if not ref_match:
        ref_match = re.search(r'(PO|SO|RFQ|TXN|LOAN)[-\s]?\d{4}[-\s]?\d{2,5}', message, re.IGNORECASE)
    ref_doc = ref_match.group(0).replace(" ", "-").upper() if ref_match else ""
    
    params: Dict[str, Any] = {}
    if ref_doc:
        params["reference_doc"] = ref_doc
    
    # Extract numbers
    numbers = re.findall(r'[\d,]+\.?\d*', msg)
    
    # Intent matching
    if any(kw in msg for kw in ["hitl", "antrean", "pending", "menunggu approval", "draf"]):
        return {"intent": "hitl_queue", "params": params, "confidence": 0.9}
    
    if any(kw in msg for kw in ["audit", "riwayat", "log keputusan", "trail"]):
        return {"intent": "audit_trail", "params": params, "confidence": 0.9}

    # Explicit list of POs (Purchase Orders)
    if any(kw in msg for kw in ["daftar po", "list po", "tampilkan po", "semua po", "lihat po", "purchase order list", "daftar purchase order", "ada po apa", "cek po"]):
        return {"intent": "list_po", "params": params, "confidence": 0.95}

    # Explicit list of Parts / Master Price Catalog
    if any(kw in msg for kw in ["daftar part", "list part", "daftar katalog", "katalog part", "daftar barang", "list barang", "semua part", "daftar sku", "daftar master price", "katalog suku cadang", "ada part apa"]):
        return {"intent": "list_parts", "params": params, "confidence": 0.95}
    
    if any(kw in msg for kw in ["margin", "mismatch", "moq", "po vs so", "validasi po"]):
        return {"intent": "agent_2", "params": params, "confidence": 0.85}
    
    if any(kw in msg for kw in ["backlog", "delay", "keterlambatan", "rdd", "eta", "terlambat"]):
        return {"intent": "agent_3", "params": params, "confidence": 0.85}
    
    if any(kw in msg for kw in ["vendor", "supplier", "pemasok", "performa", "skor vendor"]):
        return {"intent": "agent_5", "params": params, "confidence": 0.85}
    
    if any(kw in msg for kw in ["penerimaan", "gudang", "goods receipt", "barang rusak", "rma", "dock"]):
        return {"intent": "agent_6", "params": params, "confidence": 0.85}
    
    if any(kw in msg for kw in ["triangle", "pod", "logical gr", "logical gi"]):
        return {"intent": "agent_7_triangle", "params": params, "confidence": 0.85}
    
    if any(kw in msg for kw in ["pinjam", "borrowed", "loan", "stok pinjam"]):
        return {"intent": "agent_7_loan", "params": params, "confidence": 0.85}
    
    if any(kw in msg for kw in ["bank", "rekonsiliasi", "kurs", "valas", "fx", "selisih"]):
        return {"intent": "agent_8", "params": params, "confidence": 0.85}
    
    if any(kw in msg for kw in ["cash", "kas", "runway", "likuiditas", "cash flow"]):
        return {"intent": "agent_9", "params": params, "confidence": 0.85}
    
    if any(kw in msg for kw in ["renewal", "jatuh tempo", "expired", "kedaluwarsa", "master price", "validitas harga", "katalog expired", "price book", "kontrak harga", "radar harga", "ps03"]) or (ref_doc and ref_doc.startswith("MP-")):
        return {"intent": "agent_4", "params": params, "confidence": 0.85}

    if any(kw in msg for kw in ["rfq", "quotation", "penawaran", "harga", "katalog", "part", "sfp", "transceiver"]):
        params["part_description"] = msg
        return {"intent": "agent_1", "params": params, "confidence": 0.8}
    
    return {"intent": "general", "params": params, "confidence": 0.5}



# ============================================================================
# AGENT EXECUTION ROUTER
# ============================================================================
async def execute_agent_logic(
    intent: str, params: dict, entity_code: str, db_data: dict, pool
) -> Dict[str, Any]:
    """Executes the appropriate deterministic engine and generates narrative."""
    
    result: Dict[str, Any] = {
        "agent_used": None,
        "rich_card": None,
        "reply": "",
        "requires_hitl": False,
        "draft_action_id": None,
        "suggested_actions": []
    }
    
    # --- HITL Queue View ---
    if intent == "hitl_queue":
        items = db_data.get("data", [])
        if not items:
            result["reply"] = f"✅ Tidak ada draf tindakan yang menunggu otorisasi di entitas {entity_code} saat ini. Semua bersih!"
            result["suggested_actions"] = ["Lihat audit trail", "Cek cash flow", "Evaluasi vendor"]
        else:
            result["reply"] = f"📋 Ada **{len(items)} draf tindakan** menunggu otorisasi di entitas {entity_code}:"
            result["rich_card"] = {"type": "hitl_queue", "items": items, "entity": entity_code}
            result["suggested_actions"] = ["Buka halaman HITL", "Lihat audit trail"]
        return result
    
    # --- Audit Trail View ---
    if intent == "audit_trail":
        items = db_data.get("data", [])
        if not items:
            result["reply"] = f"📭 Belum ada riwayat audit trail untuk entitas {entity_code}."
        else:
            result["reply"] = f"📜 **{len(items)} event audit trail** terbaru untuk entitas {entity_code}:"
            result["rich_card"] = {"type": "audit_trail", "items": items, "entity": entity_code}
        result["suggested_actions"] = ["Lihat antrean HITL", "Cek cash flow"]
        return result

    # --- List Purchase Orders ---
    if intent == "list_po":
        items = db_data.get("data", [])
        if not items:
            result["reply"] = f"⚠️ Tidak ditemukan data Purchase Order untuk entitas **{entity_code}**."
            result["suggested_actions"] = ["Daftar part", "Lihat antrean HITL"]
        else:
            result["reply"] = f"📋 **Daftar Purchase Order (PO)** — Terpantau **{len(items)} PO** pada entitas **{entity_code}**:"
            result["rich_card"] = {"type": "po_list", "items": items, "entity": entity_code}
            result["suggested_actions"] = [
                f"Cek margin {items[0]['po_number']}",
                f"Cek GR {items[0]['po_number']}",
                "Daftar part",
                "Lihat antrean HITL"
            ]
        return result

    # --- List Parts / Master Price Catalog ---
    if intent == "list_parts":
        items = db_data.get("data", [])
        if not items:
            result["reply"] = f"⚠️ Tidak ada suku cadang terdaftar di Master Price untuk entitas **{entity_code}**."
            result["suggested_actions"] = ["Cek radar validitas harga", "Daftar PO"]
        else:
            result["reply"] = f"📦 **Katalog Suku Cadang (Master Price PS03)** — Ditemukan **{len(items)} SKU** untuk entitas **{entity_code}**:"
            result["rich_card"] = {"type": "part_list", "items": items, "entity": entity_code}
            result["suggested_actions"] = [
                f"Carikan harga {items[0]['part_number']}",
                "Cek radar validitas harga",
                "Daftar PO"
            ]
        return result
    
    # --- Agent 1: RFQ Pricing ---
    if intent == "agent_1":
        result["agent_used"] = "agent_1"
        if db_data.get("found") and db_data.get("source") == "semantic_search":
            top = db_data["data"][0]
            cost = float(top.get("unit_cost", 0))
            calc = compute_agent1_rfq_pricing(cost, 18.0)
            ref_doc = params.get("reference_doc", f"RFQ-AUTO-{datetime.now().strftime('%H%M')}")
            narrative = await generate_grounded_draft("agent_1", entity_code, calc, f"Catalog Match: {top.get('part_number')}")
            
            draft_id = await _persist_draft(pool, "agent_1", entity_code, "PS01", ref_doc, calc, narrative)
            
            result["reply"] = narrative
            result["rich_card"] = {"type": "agent_result", "agent": "agent_1", "agent_name": "Quotation Response Assistant", "metrics": calc, "catalog_match": top}
            result["requires_hitl"] = True
            result["draft_action_id"] = draft_id
            result["suggested_actions"] = ["Lihat antrean HITL", "Cari part lain"]
        else:
            calc = compute_agent1_rfq_pricing(None, 18.0)
            narrative = await generate_grounded_draft("agent_1", entity_code, calc, f"Part tidak ditemukan di katalog")
            result["reply"] = narrative
            result["rich_card"] = {"type": "agent_result", "agent": "agent_1", "agent_name": "Quotation Response Assistant", "metrics": calc}
            result["suggested_actions"] = ["Cari part lain di katalog", "Cek vendor tersedia"]
        return result
    
    # --- Agent 2: PO Margin Validation ---
    if intent == "agent_2":
        result["agent_used"] = "agent_2"
        if db_data.get("found") and db_data.get("po"):
            po = db_data["po"]
            so = db_data.get("so")
            so_price = float(so["selling_price"]) if so else float(po.get("po_cost_price", 0)) * 1.2
            calc = compute_agent2_po_margin(
                so_price=so_price,
                po_cost=float(po["po_cost_price"]),
                ordered_qty=int(po["ordered_qty"]),
                moq=int(po["supplier_moq"]),
                tier2_cost=float(po["tier2_cost_price"]) if po.get("tier2_cost_price") else None
            )
            ref_doc = po["po_number"]
            narrative = await generate_grounded_draft("agent_2", entity_code, calc, f"PO: {ref_doc}, Supplier: {po['supplier_name']}")
            
            draft_id = await _persist_draft(pool, "agent_2", entity_code, "PS02", ref_doc, calc, narrative)
            
            result["reply"] = narrative
            result["rich_card"] = {"type": "agent_result", "agent": "agent_2", "agent_name": "SO/PO Mismatch Pre-Checker", "metrics": calc, "po_ref": ref_doc}
            result["requires_hitl"] = True
            result["draft_action_id"] = draft_id
        else:
            result["reply"] = f"⚠️ Data PO dengan referensi '{params.get('reference_doc', 'tidak diketahui')}' tidak ditemukan di database entitas {entity_code}. Pastikan nomor PO benar (contoh: PO-2026-4412)."
            result["suggested_actions"] = ["Cek PO-2026-4412", "Cek PO-2026-9902"]
        return result
    
    # --- Agent 3: RDD Delay ---
    if intent == "agent_3":
        result["agent_used"] = "agent_3"
        if db_data.get("found"):
            so = db_data["data"]
            calc = compute_agent3_rdd_delay(
                str(so["rdd_target"]), str(so["eta_delivery"]), float(so["order_value"])
            )
            ref_doc = so["so_number"]
            narrative = await generate_grounded_draft("agent_3", entity_code, calc, f"SO: {ref_doc}, Customer: {so['customer_name']}")
            
            draft_id = await _persist_draft(pool, "agent_3", entity_code, "PS06", ref_doc, calc, narrative)
            
            result["reply"] = narrative
            result["rich_card"] = {"type": "agent_result", "agent": "agent_3", "agent_name": "Backlog & Exception Narrator", "metrics": calc, "so_ref": ref_doc, "customer": so["customer_name"]}
            result["requires_hitl"] = calc.get("needs_escalation", False)
            result["draft_action_id"] = draft_id
        else:
            result["reply"] = f"⚠️ Data SO '{params.get('reference_doc', '')}' tidak ditemukan. Coba: SO-2026-4401, SO-2026-1182, SO-2026-9021."
            result["suggested_actions"] = ["Cek backlog SO-2026-4401", "Cek backlog SO-2026-9021"]
        return result
    
    # --- Agent 5: Vendor Scoring ---
    if intent == "agent_5":
        result["agent_used"] = "agent_5"
        if db_data.get("found"):
            data = db_data["data"]
            if isinstance(data, list):
                # Multiple vendors — show summary
                vendor_cards = []
                for v in data:
                    calc = compute_agent5_vendor_score(float(v["on_time_rate"]), float(v["quality_rate"]), float(v["price_variance_pct"]))
                    vendor_cards.append({**calc, "vendor_name": v["vendor_name"], "vendor_code": v["vendor_code"]})
                result["reply"] = f"📊 Evaluasi performa **{len(vendor_cards)} vendor** di entitas {entity_code}:"
                result["rich_card"] = {"type": "vendor_list", "vendors": vendor_cards, "entity": entity_code}
            else:
                calc = compute_agent5_vendor_score(float(data["on_time_rate"]), float(data["quality_rate"]), float(data["price_variance_pct"]))
                ref_doc = data.get("vendor_code", data.get("vendor_name", "VENDOR"))
                narrative = await generate_grounded_draft("agent_5", entity_code, calc, f"Vendor: {data['vendor_name']}")
                
                draft_id = await _persist_draft(pool, "agent_5", entity_code, "PS07", ref_doc, calc, narrative)
                
                result["reply"] = narrative
                result["rich_card"] = {"type": "agent_result", "agent": "agent_5", "agent_name": "Vendor Performance Advisor", "metrics": calc, "vendor": data["vendor_name"]}
                result["requires_hitl"] = True
                result["draft_action_id"] = draft_id
        else:
            result["reply"] = f"Tidak ada data vendor ditemukan untuk entitas {entity_code}."
        result["suggested_actions"] = ["Lihat semua vendor", "Cek cash flow"]
        return result
    
    # --- Agent 6: GR Split ---
    if intent == "agent_6":
        result["agent_used"] = "agent_6"
        if db_data.get("found"):
            po = db_data["data"]
            calc = compute_agent6_gr_split(int(po["expected_qty"]), int(po["scanned_qty"]), int(po["damaged_qty"]), float(po["po_cost_price"]))
            ref_doc = po["po_number"]
            narrative = await generate_grounded_draft("agent_6", entity_code, calc, f"PO Dock Scan: {ref_doc}")
            
            draft_id = await _persist_draft(pool, "agent_6", entity_code, "IN01", ref_doc, calc, narrative)
            
            result["reply"] = narrative
            result["rich_card"] = {"type": "agent_result", "agent": "agent_6", "agent_name": "GR Discrepancy Handler", "metrics": calc}
            result["requires_hitl"] = True
            result["draft_action_id"] = draft_id
        else:
            result["reply"] = f"⚠️ Tidak ada PO dengan status DOCK_SCAN ditemukan untuk referensi '{params.get('reference_doc', '')}'."
        result["suggested_actions"] = ["Cek PO-2026-9902 (Dock Scan)", "Lihat antrean HITL"]
        return result
    
    # --- Agent 7: Triangle Trade ---
    if intent == "agent_7_triangle":
        result["agent_used"] = "agent_7"
        calc = compute_agent7_triangle_pod(True, params.get("po_ref", "PO-8812"), params.get("so_ref", "SO-3310"))
        narrative = await generate_grounded_draft("agent_7", entity_code, calc, "Triangle Trade POD Verification")
        
        draft_id = await _persist_draft(pool, "agent_7", entity_code, "6.3_TT", params.get("po_ref", "PO-8812"), calc, narrative)
        
        result["reply"] = narrative
        result["rich_card"] = {"type": "agent_result", "agent": "agent_7", "agent_name": "Triangle Trade & Borrowed Stock", "metrics": calc}
        result["requires_hitl"] = True
        result["draft_action_id"] = draft_id
        result["suggested_actions"] = ["Cek pinjaman stok aktif", "Lihat antrean HITL"]
        return result
    
    # --- Agent 7: Loan Maturity ---
    if intent == "agent_7_loan":
        result["agent_used"] = "agent_7"
        if db_data.get("found"):
            loans = db_data["data"]
            loan_results = []
            for loan in loans:
                calc = compute_agent7_loan_maturity(str(loan["borrowed_date"]), int(loan["max_loan_days"]))
                loan_results.append({
                    **calc, "loan_ref": loan["loan_ref"], "partner": loan["partner_name"],
                    "part": loan["part_number"], "qty": loan["qty"]
                })
            result["reply"] = f"📦 Status **{len(loan_results)} pinjaman stok aktif** di entitas {entity_code}:"
            result["rich_card"] = {"type": "loan_list", "loans": loan_results, "entity": entity_code}
        else:
            result["reply"] = f"Tidak ada pinjaman stok aktif di entitas {entity_code}."
        result["suggested_actions"] = ["Cek triangle trade", "Cek cash flow"]
        return result
    
    # --- Agent 8: FX Reconciliation ---
    if intent == "agent_8":
        result["agent_used"] = "agent_8"
        if db_data.get("found"):
            txn = db_data["data"]
            remit = float(txn.get("remittance_amount") or txn.get("booked_amount") or 50000.0)
            b_rate = float(txn.get("book_rate") or txn.get("agreed_fx_rate") or 1.35)
            s_rate = float(txn.get("settle_rate") or txn.get("actual_fx_rate") or 1.42)
            calc = compute_agent8_fx_split(remit, b_rate, s_rate)
            ref_doc = txn.get("txn_ref", "TXN-AUTO-FX")
            narrative = await generate_grounded_draft("agent_8", entity_code, calc, f"Bank Txn: {ref_doc}")
            
            draft_id = await _persist_draft(pool, "agent_8", entity_code, "AC02", ref_doc, calc, narrative)
            
            result["reply"] = narrative
            result["rich_card"] = {"type": "agent_result", "agent": "agent_8", "agent_name": "AR/AP Multi-Currency Reconciler", "metrics": calc}
            result["requires_hitl"] = True
            result["draft_action_id"] = draft_id
        else:
            result["reply"] = f"⚠️ Transaksi bank '{params.get('reference_doc', '')}' tidak ditemukan. Coba: TXN-DBS-88319, TXN-SHB-44102."
        result["suggested_actions"] = ["Cek TXN-DBS-88319", "Cek cash flow"]
        return result
    
    # --- Agent 9: Cash Runway ---
    if intent == "agent_9":
        result["agent_used"] = "agent_9"
        if db_data.get("found"):
            cash = db_data["data"]
            curr_cash = float(cash.get("current_cash") or cash.get("current_cash_balance") or 1850000.0)
            burn_rate = float(cash.get("weekly_burn_rate") or (cash.get("monthly_burn_rate", 320000) / 4) or 80000.0)
            loan_due = float(cash.get("loan_due_7days") or cash.get("loan_due") or 50000.0)
            calc = compute_agent9_cash_runway(curr_cash, burn_rate, loan_due)
            ref_doc = cash.get("period_ref", f"CASH-{entity_code}")
            narrative = await generate_grounded_draft("agent_9", entity_code, calc, f"Cash Runway: {ref_doc}")
            
            draft_id = await _persist_draft(pool, "agent_9", entity_code, "AC01", ref_doc, calc, narrative)
            
            result["reply"] = narrative
            result["rich_card"] = {"type": "agent_result", "agent": "agent_9", "agent_name": "Cash Flow & Loan Narrative", "metrics": calc, "period": ref_doc}
            result["requires_hitl"] = calc.get("alert_treasury_lead", False)
            result["draft_action_id"] = draft_id
        else:
            result["reply"] = f"⚠️ Data kas operasional untuk entitas {entity_code} belum tersedia."
        result["suggested_actions"] = ["Cek rekonsiliasi bank", "Lihat audit trail"]
        return result

    # --- Natural Language Entity Switching ---
    if intent == "switch_entity":
        target = params.get("target_entity", "SG").upper()
        entity_names = {
            "SG": "Singapore HQ",
            "VN": "Vietnam SSC",
            "KR": "Korea Branch",
            "IN": "India Back-Office",
            "JP": "Japan Office"
        }
        flags = {"SG": "🇸🇬", "VN": "🇻🇳", "KR": "🇰🇷", "IN": "🇮🇳", "JP": "🇯🇵"}
        target_name = entity_names.get(target, target)
        flag = flags.get(target, "🌐")
        result["switch_entity"] = target
        result["reply"] = (
            f"{flag} **Entitas Berhasil Dialihkan ke {target} ({target_name})**\n\n"
            f"Konteks sistem telah diperbarui secara otomatis. Semua kalkulasi kas operasional, "
            f"katalog harga, vendor scoring, dan antrean HITL sekarang disinkronkan dengan **{target_name}**."
        )
        result["suggested_actions"] = [
            f"Cek runway kas operasional {target}",
            f"Evaluasi semua vendor entitas {target}",
            f"Lihat antrean HITL {target}",
            "Cek radar validitas harga"
        ]
        return result

    # --- Agent 4: Master Price Validity & Renewal Radar (Module PS03) ---
    if intent == "agent_4":
        result["agent_used"] = "agent_4"
        if db_data.get("found"):
            data = db_data["data"]
            if isinstance(data, list):
                # Multiple books — show radar summary
                items = []
                for b in data:
                    calc = compute_agent4_price_validity(int(b["days_left"]), int(b["items_count"]))
                    items.append({
                        "id": b["book_reference"],
                        "vendor": b["vendor"],
                        "category": b["category"],
                        "validity": b["validity"],
                        "days_left": b["days_left"],
                        "status": calc["status"],
                        "urgency": calc["renewal_urgency"],
                        "items_count": b["items_count"]
                    })
                result["reply"] = f"📅 **Master Price Validity Radar (Module PS03)** — Terpantau **{len(items)} buku katalog harga** untuk entitas {entity_code}:"
                result["rich_card"] = {"type": "price_book_list", "items": items, "entity": entity_code}
                result["suggested_actions"] = [
                    f"Buat paket renewal {items[0]['id']}" if items else "Cek cash flow",
                    "Lihat antrean HITL",
                    "Cari part di katalog"
                ]
            else:
                # Single book renewal package
                book = data
                calc = compute_agent4_price_validity(int(book["days_left"]), int(book["items_count"]))
                ref_doc = book["book_reference"]
                narrative = (
                    f"Agent 4 mendeteksi katalog harga {book['vendor']} ({ref_doc}) akan kedaluwarsa dalam {calc['days_left']} hari.\n\n"
                    f"Paket Pembaruan Otomatis Terbentuk:\n"
                    f"• Penyesuaian indeks inflasi: +{calc['recommended_inflation_adjustment_pct']}% pre-calculated\n"
                    f"• Format file: Template resmi bulk Excel ERP (.xlsx) untuk {calc['items_count']} baris SKU\n"
                    f"• Target periode baru: Q4 2026 renewal dispatch\n\n"
                    f"Draf paket renewal telah disiapkan untuk otorisasi Human-in-the-Loop."
                )
                draft_id = await _persist_draft(pool, "agent_4", entity_code, "PS03", ref_doc, calc, narrative)
                result["reply"] = narrative
                result["rich_card"] = {
                    "type": "agent_result",
                    "agent": "agent_4",
                    "agent_name": "Price Validity & Renewal Radar",
                    "metrics": calc,
                    "book_reference": ref_doc,
                    "vendor": book["vendor"]
                }
                result["requires_hitl"] = calc["requires_renewal_action"]
                result["draft_action_id"] = draft_id
                result["suggested_actions"] = ["Lihat antrean HITL", "Cek radar harga lain"]
        else:
            result["reply"] = f"⚠️ Tidak ada data price book ditemukan untuk entitas {entity_code}."
            result["suggested_actions"] = ["Cek radar harga MP-CS-2026-Q2", "Cek cash flow"]
        return result
    
    # --- General / Fallback ---
    result["reply"] = (
        f"Halo! Saya adalah **Batu Networks Agentic AI** 🤖\n\n"
        f"Saya dapat membantu Anda dengan operasi ERP berikut:\n\n"
        f"• **Quotation & Pricing** — \"Carikan harga SFP-10G-LR\"\n"
        f"• **Validasi Margin PO** — \"Cek margin PO-2026-4412\"\n"
        f"• **Backlog Pengiriman** — \"Cek backlog SO-2026-4401\"\n"
        f"• **Price Validity & Renewal** — \"Cek radar validitas harga\"\n"
        f"• **Evaluasi Vendor** — \"Tampilkan skor vendor entitas {entity_code}\"\n"
        f"• **Penerimaan Gudang** — \"Cek GR PO-2026-9902\"\n"
        f"• **Triangle Trade** — \"Verifikasi POD triangle trade\"\n"
        f"• **Pinjaman Stok** — \"Cek pinjaman stok aktif\"\n"
        f"• **Rekonsiliasi Bank** — \"Rekonsiliasi TXN-DBS-88319\"\n"
        f"• **Cash Flow** — \"Cek runway kas {entity_code}\"\n"
        f"• **Ganti Entitas** — \"Pindah ke entitas VN\"\n"
        f"• **HITL Queue & Audit** — \"Tampilkan antrean approval\"\n\n"
        f"Ketik pertanyaan Anda dalam bahasa Indonesia atau Inggris. Entitas aktif: **{entity_code}**."
    )
    result["suggested_actions"] = [
        "Cek cash flow", "Cek radar validitas harga", "Lihat antrean HITL", "Evaluasi semua vendor",
        f"Cek backlog SO-2026-4401", "Ganti entitas ke VN"
    ]
    return result



async def _persist_draft(pool, agent_id, entity_code, module_code, ref_doc, calc, narrative) -> Optional[str]:
    """Persist agent result as a HITL draft action and return draft_action_id."""
    if pool is None:
        draft_id = str(uuid.uuid4())
        IN_MEMORY_DRAFTS.insert(0, {
            "id": draft_id,
            "agent_id": agent_id,
            "entity_code": entity_code,
            "module_code": module_code,
            "reference_doc": ref_doc,
            "deterministic_payload": calc,
            "llm_draft_narrative": narrative,
            "status": "PENDING",
            "created_at": datetime.now().isoformat()
        })
        return draft_id
    try:
        async with pool.acquire() as conn:
            draft_id = await conn.fetchval(
                """INSERT INTO draft_agent_actions 
                   (agent_id, entity_code, module_code, reference_doc, deterministic_payload, llm_draft_narrative)
                   VALUES ($1, $2, $3, $4, $5, $6) RETURNING id;""",
                agent_id, entity_code, module_code, ref_doc, json.dumps(calc), narrative
            )
            return str(draft_id)
    except Exception as e:
        logger.warning(f"[CHAT] Failed to persist draft: {e}")
        return None


# ============================================================================
# MAIN CHAT ENDPOINT
# ============================================================================
@router.post("/message", response_model=ChatResponse)
async def chat_message(req: ChatRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Main conversational endpoint. Classifies intent, fetches data, 
    executes deterministic agent logic, and returns structured response.
    Gracefully falls back to in-memory mock store if DB pool is offline.
    """
    pool = get_pool()
    username = current_user.get("username", "system")
    entity_code = req.entity_code
    
    # 1. Create or retrieve conversation
    conversation_id = req.conversation_id
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        if pool is not None:
            try:
                async with pool.acquire() as conn:
                    conv_id = await conn.fetchval(
                        """INSERT INTO chat_conversations (entity_code, username, title)
                           VALUES ($1, $2, $3) RETURNING id;""",
                        entity_code, username, req.message[:80]
                    )
                    conversation_id = str(conv_id)
            except Exception:
                pass
        else:
            IN_MEMORY_CONVERSATIONS.insert(0, {
                "id": conversation_id,
                "title": req.message[:80],
                "entity_code": entity_code,
                "username": username,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })
    
    # 2. Save user message
    user_msg_id = str(uuid.uuid4())
    if pool is not None:
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO chat_messages (conversation_id, role, content)
                       VALUES ($1::uuid, 'user', $2);""",
                    conversation_id, req.message
                )
        except Exception:
            pass
    else:
        if conversation_id not in IN_MEMORY_MESSAGES:
            IN_MEMORY_MESSAGES[conversation_id] = []
        IN_MEMORY_MESSAGES[conversation_id].append({
            "id": user_msg_id,
            "role": "user",
            "content": req.message,
            "created_at": datetime.now().isoformat()
        })
    
    # 3. Classify intent
    intent_result = await classify_intent(req.message, entity_code)
    intent = intent_result.get("intent", "general")
    params = intent_result.get("params", {})
    
    logger.info(f"[CHAT] User: {username} | Intent: {intent} | Params: {params}")
    
    # 4. Lookup data from DB or in-memory
    db_data = await lookup_db_data(pool, intent, params, entity_code)
    
    # 5. Execute agent logic
    agent_result = await execute_agent_logic(intent, params, entity_code, db_data, pool)
    
    # 6. Save assistant message
    asst_msg_id = str(uuid.uuid4())
    if pool is not None:
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO chat_messages (conversation_id, role, content, agent_used, rich_card, draft_action_id)
                       VALUES ($1::uuid, 'assistant', $2, $3, $4, $5::uuid);""",
                    conversation_id, agent_result["reply"],
                    agent_result.get("agent_used"),
                    json.dumps(agent_result.get("rich_card")) if agent_result.get("rich_card") else None,
                    agent_result.get("draft_action_id")
                )
        except Exception:
            pass
    else:
        if conversation_id not in IN_MEMORY_MESSAGES:
            IN_MEMORY_MESSAGES[conversation_id] = []
        IN_MEMORY_MESSAGES[conversation_id].append({
            "id": asst_msg_id,
            "role": "assistant",
            "content": agent_result["reply"],
            "agent_used": agent_result.get("agent_used"),
            "rich_card": agent_result.get("rich_card"),
            "draft_action_id": agent_result.get("draft_action_id"),
            "created_at": datetime.now().isoformat()
        })
    
    return ChatResponse(
        conversation_id=conversation_id,
        reply=agent_result["reply"],
        agent_used=agent_result.get("agent_used"),
        rich_card=agent_result.get("rich_card"),
        requires_hitl=agent_result.get("requires_hitl", False),
        draft_action_id=agent_result.get("draft_action_id"),
        suggested_actions=agent_result.get("suggested_actions", []),
        switch_entity=agent_result.get("switch_entity")
    )



@router.get("/history/{conversation_id}")
async def get_chat_history(conversation_id: str):
    """Retrieves all messages for a conversation."""
    pool = get_pool()
    if pool is None:
        return {
            "conversation_id": conversation_id,
            "messages": IN_MEMORY_MESSAGES.get(conversation_id, [])
        }
    
    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Format conversation_id tidak valid.")
    
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT id, role, content, agent_used, rich_card, draft_action_id, created_at
               FROM chat_messages WHERE conversation_id = $1 ORDER BY created_at ASC;""",
            conv_uuid
        )
    
    messages = []
    for r in rows:
        rich = r["rich_card"]
        if isinstance(rich, str):
            try: rich = json.loads(rich)
            except: rich = None
        messages.append({
            "id": str(r["id"]),
            "role": r["role"],
            "content": r["content"],
            "agent_used": r["agent_used"],
            "rich_card": rich,
            "draft_action_id": str(r["draft_action_id"]) if r["draft_action_id"] else None,
            "created_at": r["created_at"].isoformat() if r["created_at"] else None
        })
    
    return {"conversation_id": conversation_id, "messages": messages}


@router.get("/conversations/{entity_code}/{username}")
async def list_conversations(entity_code: str, username: str, limit: int = 20):
    """Lists recent conversations for a user + entity."""
    pool = get_pool()
    if pool is None:
        filtered = [
            c for c in IN_MEMORY_CONVERSATIONS 
            if (c.get("entity_code") == entity_code or entity_code == "ALL") and c.get("username") == username
        ]
        return filtered[:limit]
    
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT id, title, created_at, updated_at FROM chat_conversations
               WHERE entity_code = $1 AND username = $2
               ORDER BY updated_at DESC LIMIT $3;""",
            entity_code, username, limit
        )
    
    return [{
        "id": str(r["id"]),
        "title": r["title"],
        "created_at": r["created_at"].isoformat() if r["created_at"] else None,
        "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None
    } for r in rows]

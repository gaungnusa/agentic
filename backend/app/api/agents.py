from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import json

from app.core.database import get_pool
from app.engine.llm_synthesizer import generate_grounded_draft
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
from app.schemas.agent_payloads import (
    Agent1Request,
    POValidationRequest,
    Agent3RDDRequest,
    Agent4Request,
    Agent5VendorScoreRequest,
    Agent6Request,
    Agent7TriangleRequest,
    Agent7LoanMaturityRequest,
    BankMatchingRequest,
    Agent9CashRunwayRequest
)

import uuid
from datetime import datetime

router = APIRouter(prefix="/api/v1/agents", tags=["Agents Execution"])

async def save_agent_draft(agent_id: str, entity_code: str, module_code: str, reference_doc: str, calc: dict, draft_text: str) -> str:
    pool = get_pool()
    if pool is None:
        from app.api.chat import IN_MEMORY_DRAFTS
        draft_id = str(uuid.uuid4())
        IN_MEMORY_DRAFTS.insert(0, {
            "id": draft_id,
            "agent_id": agent_id,
            "entity_code": entity_code,
            "module_code": module_code,
            "reference_doc": reference_doc,
            "deterministic_payload": calc,
            "llm_draft_narrative": draft_text,
            "status": "PENDING",
            "created_at": datetime.now().isoformat()
        })
        return draft_id

    async with pool.acquire() as conn:
        draft_id = await conn.fetchval(
            """
            INSERT INTO draft_agent_actions 
            (agent_id, entity_code, module_code, reference_doc, deterministic_payload, llm_draft_narrative)
            VALUES ($1, $2, $3, $4, $5, $6) RETURNING id;
            """,
            agent_id, entity_code, module_code, reference_doc, json.dumps(calc), draft_text
        )
        return str(draft_id)

# ==========================================
# ENDPOINTS
# ==========================================

# Agent 1: RFQ & Quotation Sourcing
@router.post("/agent-1/process-rfq")
async def trigger_agent_1(req: Agent1Request):
    calc = compute_agent1_rfq_pricing(req.unit_cost, req.target_margin_pct)
    draft_text = await generate_grounded_draft(
        agent_id="agent_1",
        entity_code=req.entity_code,
        deterministic_data=calc,
        raw_context=f"RFQ Inbound: {req.reference_doc}"
    )
    draft_id = await save_agent_draft("agent_1", req.entity_code, "PS01", req.reference_doc, calc, draft_text)
    return {"status": "QUEUED_IN_STAGING", "draft_action_id": draft_id, "metrics": calc, "draft_preview": draft_text}

# Agent 2: SO/PO Mismatch & MOQ Pre-Checker
@router.post("/agent-2/validate-po")
async def trigger_agent_2(payload: POValidationRequest):
    calc = compute_agent2_po_margin(
        so_price=payload.so_selling_price,
        po_cost=payload.po_cost_price,
        ordered_qty=payload.ordered_qty,
        moq=payload.supplier_moq,
        tier2_cost=payload.tier2_cost_price
    )
    draft_text = await generate_grounded_draft(
        agent_id="agent_2",
        entity_code=payload.entity_code,
        deterministic_data=calc,
        raw_context=f"PO: {payload.reference_doc}, SO: {payload.so_number}, Supplier: {payload.supplier_name}"
    )
    draft_id = await save_agent_draft("agent_2", payload.entity_code, "PS02", payload.reference_doc, calc, draft_text)
    return {"status": "QUEUED_IN_STAGING", "draft_action_id": draft_id, "metrics": calc, "draft_preview": draft_text}

# Agent 3: RDD Delivery Deviation & Backlog Escalation
@router.post("/agent-3/evaluate-rdd")
async def trigger_agent_3(req: Agent3RDDRequest):
    calc = compute_agent3_rdd_delay(req.rdd_target_str, req.eta_str, req.order_value)
    draft_text = await generate_grounded_draft(
        agent_id="agent_3",
        entity_code=req.entity_code,
        deterministic_data=calc,
        raw_context=f"Project / SO Ref: {req.reference_doc}, Target RDD: {req.rdd_target_str}, ETA: {req.eta_str}"
    )
    draft_id = await save_agent_draft("agent_3", req.entity_code, "PS06", req.reference_doc, calc, draft_text)
    return {"status": "QUEUED_IN_STAGING", "draft_action_id": draft_id, "metrics": calc, "draft_preview": draft_text}

# Agent 4: Master Price Validity Radar & Bulk Template Generator
@router.post("/agent-4/evaluate-price-book")
async def trigger_agent_4(req: Agent4Request):
    calc = compute_agent4_price_validity(req.days_left, req.items_count, req.inflation_adj_pct)
    draft_text = await generate_grounded_draft(
        agent_id="agent_4",
        entity_code=req.entity_code,
        deterministic_data=calc,
        raw_context=f"Price Book: {req.reference_doc} ({req.items_count} SKU, {req.days_left} days left, +{req.inflation_adj_pct}% inflation)"
    )
    draft_id = await save_agent_draft("agent_4", req.entity_code, "PS03", req.reference_doc, calc, draft_text)
    return {"status": "QUEUED_IN_STAGING", "draft_action_id": draft_id, "metrics": calc, "draft_preview": draft_text}

# Agent 5: Vendor Performance Scoring & Quota Allocation
@router.post("/agent-5/evaluate-vendor")
async def trigger_agent_5(req: Agent5VendorScoreRequest):
    calc = compute_agent5_vendor_score(req.on_time_rate, req.quality_rate, req.price_variance_pct)
    draft_text = await generate_grounded_draft(
        agent_id="agent_5",
        entity_code=req.entity_code,
        deterministic_data=calc,
        raw_context=f"Vendor Evaluation: {req.reference_doc} (On-Time: {req.on_time_rate}%, Quality: {req.quality_rate}%)"
    )
    draft_id = await save_agent_draft("agent_5", req.entity_code, "PS07", req.reference_doc, calc, draft_text)
    return {"status": "QUEUED_IN_STAGING", "draft_action_id": draft_id, "metrics": calc, "draft_preview": draft_text}

# Agent 6: Goods Receipt (GR) & RMA Damaged Goods Split
@router.post("/agent-6/handle-gr")
async def trigger_agent_6(req: Agent6Request):
    calc = compute_agent6_gr_split(req.po_expected_qty, req.scanned_qty, req.damaged_qty, req.unit_cost)
    draft_text = await generate_grounded_draft(
        agent_id="agent_6",
        entity_code=req.entity_code,
        deterministic_data=calc,
        raw_context=f"PO Inbound Dock Scan: {req.reference_doc}"
    )
    draft_id = await save_agent_draft("agent_6", req.entity_code, "IN01", req.reference_doc, calc, draft_text)
    return {"status": "QUEUED_IN_STAGING", "draft_action_id": draft_id, "metrics": calc, "draft_preview": draft_text}

# Agent 7: Triangle Trade POD & Synchronized Logical GR/GI
@router.post("/agent-7/verify-triangle")
async def trigger_agent_7(req: Agent7TriangleRequest):
    calc = compute_agent7_triangle_pod(req.is_pod_received, req.po_ref, req.so_ref)
    draft_text = await generate_grounded_draft(
        agent_id="agent_7",
        entity_code=req.entity_code,
        deterministic_data=calc,
        raw_context=f"Triangle Trade Route: PO {req.po_ref} to SO {req.so_ref}"
    )
    draft_id = await save_agent_draft("agent_7", req.entity_code, "6.3_TT", req.po_ref, calc, draft_text)
    return {"status": "QUEUED_IN_STAGING", "draft_action_id": draft_id, "metrics": calc, "draft_preview": draft_text}

# Agent 7: Inter-Partner Stock Loan Maturity Radar
@router.post("/agent-7/check-loan-maturity")
async def trigger_agent_7_loan(req: Agent7LoanMaturityRequest):
    calc = compute_agent7_loan_maturity(req.borrowed_date_str, req.max_loan_days)
    draft_text = await generate_grounded_draft(
        agent_id="agent_7",
        entity_code=req.entity_code,
        deterministic_data=calc,
        raw_context=f"Stock Loan Ref: {req.reference_doc}, Borrowed Date: {req.borrowed_date_str}"
    )
    draft_id = await save_agent_draft("agent_7", req.entity_code, "6.3_STOCK", req.reference_doc, calc, draft_text)
    return {"status": "QUEUED_IN_STAGING", "draft_action_id": draft_id, "metrics": calc, "draft_preview": draft_text}

# Agent 8: Multi-Currency AR/AP Bank Reconciliation
@router.post("/agent-8/reconcile-bank")
async def trigger_agent_8(payload: BankMatchingRequest):
    calc = compute_agent8_fx_split(
        amount_foreign=payload.remittance_amount,
        book_rate=payload.invoice_book_rate,
        settle_rate=payload.bank_settlement_rate
    )
    draft_text = await generate_grounded_draft(
        agent_id="agent_8",
        entity_code=payload.entity_code,
        deterministic_data=calc,
        raw_context=f"Bank Txn: {payload.reference_doc}, Invoices: {payload.target_invoices}"
    )
    draft_id = await save_agent_draft("agent_8", payload.entity_code, "AC02", payload.reference_doc, calc, draft_text)
    return {"status": "QUEUED_IN_STAGING", "draft_action_id": draft_id, "metrics": calc, "draft_preview": draft_text}

# Agent 9: Operational Cash Flow & Liquidity Runway
@router.post("/agent-9/assess-cash-runway")
async def trigger_agent_9(req: Agent9CashRunwayRequest):
    calc = compute_agent9_cash_runway(req.current_cash, req.weekly_burn_rate, req.loan_due_7days)
    draft_text = await generate_grounded_draft(
        agent_id="agent_9",
        entity_code=req.entity_code,
        deterministic_data=calc,
        raw_context=f"Cash Runway Assessment: Ref {req.reference_doc}, Current Cash: {req.current_cash}"
    )
    draft_id = await save_agent_draft("agent_9", req.entity_code, "AC01", req.reference_doc, calc, draft_text)
    return {"status": "QUEUED_IN_STAGING", "draft_action_id": draft_id, "metrics": calc, "draft_preview": draft_text}
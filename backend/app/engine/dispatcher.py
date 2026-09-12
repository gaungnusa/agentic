import json
import logging
from typing import Dict, Any

logger = logging.getLogger("action_dispatcher")
logger.setLevel(logging.INFO)

async def dispatch_approved_action(agent_id: str, entity_code: str, reference_doc: str, payload: Dict[str, Any], final_narrative: str) -> Dict[str, Any]:
    """
    Eksekutor aksi nyata setelah PIC menekan tombol APPROVE.
    Mengirimkan webhook/email/file generator sesuai SOP masing-masing agen.
    """
    logger.info(f"[DISPATCHER] Memulai eksekusi untuk {agent_id} | Ref: {reference_doc} | Entitas: {entity_code}")
    
    execution_result = {
        "agent_id": agent_id,
        "reference_doc": reference_doc,
        "entity_code": entity_code,
        "dispatched": True,
        "action_details": {}
    }

    # =========================================================================
    # AGENT 1: Outbound Dispatch RFQ Vendor / Draf Penawaran Client
    # =========================================================================
    if agent_id == "agent_1":
        if payload.get("action_required") == "GENERATE_CUSTOMER_QUOTE":
            # Simulasi pengiriman draf penawaran resmi ke modul sales / email client
            execution_result["action_details"] = {
                "type": "EMAIL_DISPATCH",
                "recipient": "sales.operation@batunetworks.com",
                "subject": f"[{entity_code}] Official Quotation - {reference_doc}",
                "status": "SENT_TO_OUTBOX",
                "quote_price": payload.get("recommended_quote_price")
            }
        else:
            # Pemicu RFQ paralel ke 3 vendor terdaftar
            execution_result["action_details"] = {
                "type": "PARALLEL_VENDOR_SOURCING",
                "vendors_notified": ["Amphenol SG", "Molex APAC", "CommScope Japan"],
                "status": "RFQS_TRANSMITTED"
            }

    # =========================================================================
    # AGENT 2: Update PO Staging Table & Buka Kuncian Approval
    # =========================================================================
    elif agent_id == "agent_2":
        remedy = payload.get("remedy")
        execution_result["action_details"] = {
            "type": "ERP_PO_MUTATION",
            "po_number": reference_doc,
            "status": "PO_UNLOCKED_WITH_ADJUSTMENTS",
            "applied_qty": remedy.get("suggested_qty") if remedy else None,
            "projected_margin": remedy.get("projected_margin") if remedy else None
        }

    # =========================================================================
    # AGENT 3: Backlog Delay Escalation & Project Alert
    # =========================================================================
    elif agent_id == "agent_3":
        execution_result["action_details"] = {
            "type": "BACKLOG_DELAY_ESCALATION",
            "severity": payload.get("severity"),
            "delta_days": payload.get("delta_days"),
            "recipient": "project.operations@batunetworks.com",
            "status": "ESCALATION_DISPATCHED" if payload.get("needs_escalation") else "MONITORED"
        }

    # =========================================================================
    # AGENT 4: Bulk Excel Generator untuk Master Price Renewal
    # =========================================================================
    elif agent_id == "agent_4":
        execution_result["action_details"] = {
            "type": "EXCEL_EXPORT",
            "file_generated": f"MasterPrice_Renewal_{reference_doc}_{entity_code}.xlsx",
            "inflation_index_applied": payload.get("recommended_inflation_adjustment_pct"),
            "download_url": f"/api/v1/files/exports/{reference_doc}.xlsx"
        }

    # =========================================================================
    # AGENT 5: Vendor Quota Allocation Update
    # =========================================================================
    elif agent_id == "agent_5":
        execution_result["action_details"] = {
            "type": "VENDOR_ALLOCATION_UPDATE",
            "vendor_name": reference_doc,
            "composite_score": payload.get("composite_score"),
            "assigned_tier": payload.get("vendor_tier"),
            "suggested_quota_pct": payload.get("suggested_allocation_pct"),
            "status": "VENDOR_TIER_COMMITTED"
        }

    # =========================================================================
    # AGENT 6: Posting Partial GR & Draft Surat Klaim RMA Vendor
    # =========================================================================
    elif agent_id == "agent_6":
        execution_result["action_details"] = {
            "type": "WAREHOUSE_SPLIT_EXECUTION",
            "partial_gr_voucher": f"PGR-{reference_doc}-01",
            "valid_units_received": payload.get("valid_gr_qty"),
            "rma_claim_ref": f"RMA-{reference_doc}-CLAIM" if payload.get("rma_required") else None,
            "debit_note_amount": payload.get("debit_claim_amount")
        }

    # =========================================================================
    # AGENT 7: Synchronized Logical GR/GI (Triangle Trade) & Stock Loan Advice
    # =========================================================================
    elif agent_id == "agent_7":
        if "days_left" in payload:
            execution_result["action_details"] = {
                "type": "STOCK_LOAN_RETURN_ADVICE",
                "loan_reference": reference_doc,
                "days_left": payload.get("days_left"),
                "action_required": payload.get("action_required"),
                "status": "RETURN_ADVICE_TRANSMITTED" if payload.get("is_expiring_soon") else "MONITORING"
            }
        else:
            execution_result["action_details"] = {
                "type": "TRIANGLE_TRADE_DUAL_POSTING",
                "logical_gr_voucher": f"LGR-{payload.get('po_reference')}",
                "logical_gi_voucher": f"LGI-{payload.get('so_reference')}",
                "physical_inventory_impact": "NONE_BYPASS_SG_HUB",
                "transit_cleared": True
            }

    # =========================================================================
    # AGENT 8: Posting Jurnal Kliring AR/AP & FX Difference ke Buku Besar
    # =========================================================================
    elif agent_id == "agent_8":
        execution_result["action_details"] = {
            "type": "GL_CLEARING_VOUCHER_POSTED",
            "voucher_id": f"JV-CLEAR-{reference_doc}",
            "fx_account": payload.get("allocated_account"),  # 7210 (Loss) / 7110 (Gain)
            "fx_variance_posted": payload.get("fx_variance"),
            "ledger_status": "POSTED_BALANCED"
        }

    # =========================================================================
    # AGENT 9: Treasury Liquidity Advisory Alert
    # =========================================================================
    elif agent_id == "agent_9":
        execution_result["action_details"] = {
            "type": "TREASURY_LIQUIDITY_ALERT",
            "weeks_runway": payload.get("weeks_runway"),
            "liquidity_status": payload.get("liquidity_status"),
            "target_audience": ["cfo@batunetworks.com", "treasury.lead@batunetworks.com"],
            "status": "TREASURY_ALERT_DISPATCHED" if payload.get("alert_treasury_lead") else "NORMAL_LOGGED"
        }

    else:
        execution_result["action_details"] = {
            "type": "GENERIC_ADVISORY_ACKNOWLEDGED",
            "status": "LOGGED"
        }

    logger.info(f"[DISPATCHER] Eksekusi sukses: {json.dumps(execution_result)}")
    return execution_result
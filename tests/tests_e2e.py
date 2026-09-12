import httpx
import asyncio
import json

BASE_URL = "http://localhost:8000/api/v1"

async def test_full_agent_workflow():
    async with httpx.AsyncClient(timeout=20.0) as client:
        print("==================================================")
        print("BATU NETWORKS ERP - AGENTIC AI END-TO-END TEST SUITE")
        print("==================================================")

        # 1. Health Check
        print("\n--- 1. Health Check API ---")
        res_health = await client.get("http://localhost:8000/health")
        assert res_health.status_code == 200, f"Health check failed: {res_health.text}"
        print("Status:", res_health.json())

        # 2. Agent 1: Quotation Response Assistant
        print("\n--- 2. Pengujian Agent 1 (Quotation Auto-Pricing) ---")
        a1_payload = {
            "entity_code": "SG",
            "reference_doc": "RFQ-2026-E2E-01",
            "unit_cost": 38.50,
            "target_margin_pct": 18.0
        }
        res_a1 = await client.post(f"{BASE_URL}/agents/agent-1/process-rfq", json=a1_payload)
        assert res_a1.status_code == 200, f"Agent 1 failed: {res_a1.text}"
        data_a1 = res_a1.json()
        print(f"Agent 1 Draft ID: {data_a1['draft_action_id']} | Price: ${data_a1['metrics']['recommended_quote_price']}")

        # 3. Agent 2: SO/PO Mismatch Pre-Checker
        print("\n--- 3. Pengujian Agent 2 (Margin & MOQ Enforcement) ---")
        a2_payload = {
            "entity_code": "KR",
            "reference_doc": "PO-2026-E2E-02",
            "so_number": "SO-2026-KR-11",
            "supplier_name": "Broadcom APAC Korea",
            "so_selling_price": 120.00,
            "po_cost_price": 108.50,
            "ordered_qty": 350,
            "supplier_moq": 500,
            "tier2_cost_price": 94.00
        }
        res_a2 = await client.post(f"{BASE_URL}/agents/agent-2/validate-po", json=a2_payload)
        assert res_a2.status_code == 200, f"Agent 2 failed: {res_a2.text}"
        data_a2 = res_a2.json()
        print(f"Agent 2 Draft ID: {data_a2['draft_action_id']} | Margin: {data_a2['metrics']['gross_margin_pct']}%")

        # 4. Agent 3: Backlog & Exception Narrator
        print("\n--- 4. Pengujian Agent 3 (RDD Delay & Backlog Severity) ---")
        a3_payload = {
            "entity_code": "VN",
            "reference_doc": "SO-2026-VN-99",
            "rdd_target_str": "2026-09-01",
            "eta_str": "2026-09-18",
            "order_value": 75000.00
        }
        res_a3 = await client.post(f"{BASE_URL}/agents/agent-3/evaluate-rdd", json=a3_payload)
        assert res_a3.status_code == 200, f"Agent 3 failed: {res_a3.text}"
        data_a3 = res_a3.json()
        print(f"Agent 3 Draft ID: {data_a3['draft_action_id']} | Severity: {data_a3['metrics']['severity']}")

        # 5. Agent 5: Vendor Performance Advisor
        print("\n--- 5. Pengujian Agent 5 (Vendor Scorecard & Quota Allocation) ---")
        a5_payload = {
            "entity_code": "SG",
            "reference_doc": "Amphenol Singapore Pte Ltd",
            "on_time_rate": 96.0,
            "quality_rate": 97.5,
            "price_variance_pct": 0.8
        }
        res_a5 = await client.post(f"{BASE_URL}/agents/agent-5/evaluate-vendor", json=a5_payload)
        assert res_a5.status_code == 200, f"Agent 5 failed: {res_a5.text}"
        data_a5 = res_a5.json()
        print(f"Agent 5 Draft ID: {data_a5['draft_action_id']} | Tier: {data_a5['metrics']['vendor_tier']}")

        # 6. Agent 6: GR Discrepancy Handler
        print("\n--- 6. Pengujian Agent 6 (GR Partial & RMA Debit Note) ---")
        a6_payload = {
            "entity_code": "SG",
            "reference_doc": "PO-2026-SG-GR01",
            "po_expected_qty": 1000,
            "scanned_qty": 1000,
            "damaged_qty": 50,
            "unit_cost": 42.00
        }
        res_a6 = await client.post(f"{BASE_URL}/agents/agent-6/handle-gr", json=a6_payload)
        assert res_a6.status_code == 200, f"Agent 6 failed: {res_a6.text}"
        data_a6 = res_a6.json()
        print(f"Agent 6 Draft ID: {data_a6['draft_action_id']} | Claim: ${data_a6['metrics']['debit_claim_amount']}")

        # 7. Agent 7: Triangle Trade POD & Stock Loan Radar
        print("\n--- 7. Pengujian Agent 7 (Triangle Trade & Loan Maturity) ---")
        a7_pod_payload = {
            "entity_code": "SG",
            "po_ref": "PO-TT-7701",
            "so_ref": "SO-TT-8802",
            "is_pod_received": True
        }
        res_a7 = await client.post(f"{BASE_URL}/agents/agent-7/verify-triangle", json=a7_pod_payload)
        assert res_a7.status_code == 200, f"Agent 7 TT failed: {res_a7.text}"
        print(f"Agent 7 Triangle Trade Eligible: {res_a7.json()['metrics']['posting_eligible']}")

        a7_loan_payload = {
            "entity_code": "SG",
            "reference_doc": "LOAN-2026-SG-01",
            "borrowed_date_str": "2026-08-10",
            "max_loan_days": 30
        }
        res_a7_loan = await client.post(f"{BASE_URL}/agents/agent-7/check-loan-maturity", json=a7_loan_payload)
        assert res_a7_loan.status_code == 200, f"Agent 7 Loan failed: {res_a7_loan.text}"
        data_a7_loan = res_a7_loan.json()
        print(f"Agent 7 Loan Action: {data_a7_loan['metrics']['action_required']} | Days Left: {data_a7_loan['metrics']['days_left']}")

        # 8. Agent 8: Multi-Currency AR/AP Bank Reconciler
        print("\n--- 8. Pengujian Agent 8 (Bank Matching & FX Allocation) ---")
        a8_payload = {
            "entity_code": "SG",
            "reference_doc": "TXN-DBS-E2E-88",
            "bank_account_ref": "DBS USD Treasury",
            "remittance_amount": 74500.00,
            "remittance_currency": "USD",
            "target_invoices": ["INV-2026-001", "INV-2026-002"],
            "invoice_book_rate": 1.3500,
            "bank_settlement_rate": 1.3420
        }
        res_a8 = await client.post(f"{BASE_URL}/agents/agent-8/reconcile-bank", json=a8_payload)
        assert res_a8.status_code == 200, f"Agent 8 failed: {res_a8.text}"
        data_a8 = res_a8.json()
        print(f"Agent 8 Draft ID: {data_a8['draft_action_id']} | FX Type: {data_a8['metrics']['fx_type']} (${data_a8['metrics']['fx_variance']})")

        # 9. Agent 9: Cash Runway & Liquidity Protection
        print("\n--- 9. Pengujian Agent 9 (Operational Cash Runway) ---")
        a9_payload = {
            "entity_code": "SG",
            "reference_doc": "TREASURY-WK36",
            "current_cash": 185000.00,
            "weekly_burn_rate": 32000.00,
            "loan_due_7days": 45000.00
        }
        res_a9 = await client.post(f"{BASE_URL}/agents/agent-9/assess-cash-runway", json=a9_payload)
        assert res_a9.status_code == 200, f"Agent 9 failed: {res_a9.text}"
        data_a9 = res_a9.json()
        print(f"Agent 9 Draft ID: {data_a9['draft_action_id']} | Status: {data_a9['metrics']['liquidity_status']} ({data_a9['metrics']['weeks_runway']} wks)")

        # 10. HITL Gateway Queue Inspection
        print("\n--- 10. Verifikasi Antrean HITL Gateway (Entity: SG) ---")
        res_queue = await client.get(f"{BASE_URL}/hitl/queue/SG")
        assert res_queue.status_code == 200, f"HITL queue failed: {res_queue.text}"
        queue_items = res_queue.json()
        print(f"Jumlah draf tertahan di antrean SG: {len(queue_items)}")
        assert len(queue_items) > 0, "Antrean tidak boleh kosong setelah pemicuan agen"

        # 11. Otorisasi Keputusan PIC: APPROVE dan EDITED
        login_res = await client.post(
            f"{BASE_URL}/auth/login",
            json={"username": "admin", "password": "BatuAdmin2026!"}
        )
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        auth_token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {auth_token}"}

        target_draft = queue_items[0]
        print(f"\n--- 11. Otorisasi Keputusan PIC untuk {target_draft['ref_doc']} ---")
        approval_res = await client.post(
            f"{BASE_URL}/hitl/decision",
            headers=headers,
            json={
                "draft_action_id": target_draft["id"],
                "operator_id": "auditor.lead@batunetworks.com",
                "decision": "EDIT",
                "modified_narrative": f"[DISETUJUI PIC DENGAN KOREKSI] {target_draft['narrative']}"
            }
        )
        assert approval_res.status_code == 200, f"Approval decision failed: {approval_res.text}"
        print("Hasil Keputusan:", approval_res.json()["action_taken"], "-", approval_res.json()["message"])

        # 12. Verifikasi Audit Trail Explorer
        print("\n--- 12. Verifikasi Live Audit Trail Explorer (Entity: SG) ---")
        res_audit = await client.get(f"{BASE_URL}/hitl/audit/SG")
        assert res_audit.status_code == 200, f"Audit trail failed: {res_audit.text}"
        audit_logs = res_audit.json()
        print(f"Total catatan audit logs SG: {len(audit_logs)}")
        if len(audit_logs) > 0:
            latest = audit_logs[0]
            print(f"Log Terkini: ID={latest['id']} | Action={latest['event_action']} | PIC={latest['operator_id']}")

        # 13. Verifikasi Read-Replica Explorer API
        print("\n--- 13. Verifikasi ERP Read-Replica Explorer API ---")
        res_rep_price = await client.get(f"{BASE_URL}/replica/master-price/SG")
        assert res_rep_price.status_code == 200, f"Replica price failed: {res_rep_price.text}"
        print(f"Replica Master Prices di SG: {len(res_rep_price.json())} item")

        res_rep_cash = await client.get(f"{BASE_URL}/replica/cash-position/SG")
        assert res_rep_cash.status_code == 200, f"Replica cash failed: {res_rep_cash.text}"
        print(f"Replica Kas Operasional SG: ${res_rep_cash.json().get('current_cash', 0):,.2f}")

        print("\n==================================================")
        print("[SUCCESS] SEMUA PENGUJIAN END-TO-END LULUS 100% SUKSES!")
        print("==================================================")

if __name__ == "__main__":
    asyncio.run(test_full_agent_workflow())
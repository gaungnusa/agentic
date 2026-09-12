import unittest
from datetime import date, timedelta
import sys
import os

# Tambahkan path backend ke sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

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

class TestDeterministicEngine(unittest.TestCase):

    def test_agent1_rfq_pricing(self):
        # Catalog matched
        res = compute_agent1_rfq_pricing(unit_cost=38.50, target_margin_pct=18.0)
        self.assertTrue(res["catalog_matched"])
        self.assertEqual(res["unit_cost"], 38.50)
        self.assertAlmostEqual(res["recommended_quote_price"], 46.95, places=2)
        self.assertEqual(res["action_required"], "GENERATE_CUSTOMER_QUOTE")

        # Unmatched catalog -> Parallel Sourcing
        res_none = compute_agent1_rfq_pricing(unit_cost=None)
        self.assertFalse(res_none["catalog_matched"])
        self.assertEqual(res_none["action_required"], "DISPATCH_PARALLEL_SOURCING_RFQ")

    def test_agent2_po_margin(self):
        # Margin healthy & MOQ met
        res_ok = compute_agent2_po_margin(so_price=100.0, po_cost=80.0, ordered_qty=500, moq=500)
        self.assertEqual(res_ok["gross_margin_pct"], 20.0)
        self.assertFalse(res_ok["is_margin_breached"])
        self.assertFalse(res_ok["is_moq_breached"])
        self.assertIsNone(res_ok["remedy"])

        # Margin breach (<15%) & MOQ breach with tier2 remedy
        res_breach = compute_agent2_po_margin(so_price=120.0, po_cost=108.5, ordered_qty=350, moq=500, tier2_cost=94.0)
        self.assertTrue(res_breach["is_margin_breached"])
        self.assertTrue(res_breach["is_moq_breached"])
        self.assertIsNotNone(res_breach["remedy"])
        self.assertEqual(res_breach["remedy"]["suggested_qty"], 500)
        self.assertAlmostEqual(res_breach["remedy"]["projected_margin"], 21.67, places=2)

    def test_agent3_rdd_delay(self):
        # No delay
        res_on_time = compute_agent3_rdd_delay("2026-09-20", "2026-09-18", 50000.0)
        self.assertFalse(res_on_time["is_delayed"])
        self.assertEqual(res_on_time["severity"], "NORMAL")
        self.assertFalse(res_on_time["needs_escalation"])

        # Warning delay (5 days)
        res_warn = compute_agent3_rdd_delay("2026-09-10", "2026-09-15", 50000.0)
        self.assertTrue(res_warn["is_delayed"])
        self.assertEqual(res_warn["severity"], "WARNING")
        self.assertTrue(res_warn["needs_escalation"])

        # Critical delay (20 days)
        res_crit = compute_agent3_rdd_delay("2026-09-01", "2026-09-21", 50000.0)
        self.assertTrue(res_crit["is_delayed"])
        self.assertEqual(res_crit["severity"], "CRITICAL")
        self.assertTrue(res_crit["needs_escalation"])

    def test_agent4_price_validity(self):
        # Expiring soon (<= 30 days)
        res_exp = compute_agent4_price_validity(days_left=28, items_count=45, inflation_adj_pct=2.1)
        self.assertEqual(res_exp["status"], "EXPIRING_SOON")
        self.assertEqual(res_exp["renewal_urgency"], "HIGH")
        self.assertTrue(res_exp["requires_renewal_action"])
        self.assertEqual(res_exp["bulk_template_format"], "xlsx")

        # Scheduled (31 - 60 days)
        res_sched = compute_agent4_price_validity(days_left=45, items_count=120)
        self.assertEqual(res_sched["status"], "SCHEDULED")
        self.assertEqual(res_sched["renewal_urgency"], "MEDIUM")
        self.assertTrue(res_sched["requires_renewal_action"])

        # Healthy (> 60 days)
        res_ok = compute_agent4_price_validity(days_left=75, items_count=50)
        self.assertEqual(res_ok["status"], "HEALTHY")
        self.assertEqual(res_ok["renewal_urgency"], "LOW")
        self.assertFalse(res_ok["requires_renewal_action"])

    def test_agent5_vendor_score(self):
        # Tier 1 Preferred (composite >= 88)
        res_t1 = compute_agent5_vendor_score(on_time_rate=95.0, quality_rate=95.0, price_variance_pct=0.0)
        self.assertGreaterEqual(res_t1["composite_score"], 88.0)
        self.assertEqual(res_t1["vendor_tier"], "TIER_1_PREFERRED")
        self.assertEqual(res_t1["suggested_allocation_pct"], 70)
        self.assertTrue(res_t1["is_eligible_for_po"])

        # Restricted Tier (< 70)
        res_t3 = compute_agent5_vendor_score(on_time_rate=60.0, quality_rate=60.0, price_variance_pct=15.0)
        self.assertEqual(res_t3["vendor_tier"], "TIER_3_RESTRICTED")
        self.assertFalse(res_t3["is_eligible_for_po"])

    def test_agent6_gr_split(self):
        res = compute_agent6_gr_split(po_expected_qty=1000, scanned_qty=1000, damaged_qty=80, unit_cost=39.0)
        self.assertEqual(res["valid_gr_qty"], 920)
        self.assertEqual(res["damaged_qty"], 80)
        self.assertTrue(res["rma_required"])
        self.assertEqual(res["debit_claim_amount"], 3120.0)
        self.assertTrue(res["is_partial_gr"])

    def test_agent7_triangle_pod(self):
        res = compute_agent7_triangle_pod(is_pod_received=True, po_ref="PO-101", so_ref="SO-202")
        self.assertTrue(res["posting_eligible"])
        self.assertFalse(res["warehouse_mutation_required"])

    def test_agent7_loan_maturity_month_rollover_edge_case(self):
        # Test case yang sebelumnya crash karena borrowed_date.replace(day=day+30)
        # Tanggal 15 Agustus + 30 hari -> 14 September (tidak crash!)
        res = compute_agent7_loan_maturity("2026-08-15", max_loan_days=30)
        self.assertIn("days_left", res)
        self.assertIn("action_required", res)

        # Tanggal 28 Februari + 30 hari -> Maret (edge case)
        res_feb = compute_agent7_loan_maturity("2026-02-28", max_loan_days=30)
        self.assertIn("days_left", res_feb)

    def test_agent8_fx_split(self):
        # FX Gain
        res_gain = compute_agent8_fx_split(amount_foreign=10000.0, book_rate=1.30, settle_rate=1.35)
        self.assertEqual(res_gain["fx_type"], "GAIN")
        self.assertEqual(res_gain["allocated_account"], "7110")
        self.assertEqual(res_gain["fx_variance"], 500.0)

        # FX Loss
        res_loss = compute_agent8_fx_split(amount_foreign=10000.0, book_rate=1.35, settle_rate=1.30)
        self.assertEqual(res_loss["fx_type"], "LOSS")
        self.assertEqual(res_loss["allocated_account"], "7210")
        self.assertEqual(res_loss["fx_variance"], -500.0)

    def test_agent9_cash_runway(self):
        # Healthy
        res_healthy = compute_agent9_cash_runway(current_cash=200000.0, weekly_burn_rate=20000.0, loan_due_7days=20000.0)
        self.assertEqual(res_healthy["liquidity_status"], "HEALTHY")
        self.assertFalse(res_healthy["alert_treasury_lead"])

        # Critical Deficit (< 2 weeks)
        res_crit = compute_agent9_cash_runway(current_cash=30000.0, weekly_burn_rate=20000.0, loan_due_7days=10000.0)
        self.assertEqual(res_crit["liquidity_status"], "CRITICAL_DEFICIT")
        self.assertTrue(res_crit["alert_treasury_lead"])

    def test_semantic_embedding_cosine(self):
        from app.engine.semantic_search import text_to_embedding
        import math

        emb1 = text_to_embedding("SFP+ 10G Optical Transceiver Module")
        emb2 = text_to_embedding("SFP 10G Transceiver Optic")
        emb_unrelated = text_to_embedding("Enterprise Accounting Invoice Payment")

        self.assertEqual(len(emb1), 384)
        self.assertEqual(len(emb2), 384)

        # Ensure unit norm
        norm1 = math.sqrt(sum(x * x for x in emb1))
        self.assertAlmostEqual(norm1, 1.0, places=3)

        # Cosine similarity: dot product of normalized vectors
        cos_sim_related = sum(a * b for a, b in zip(emb1, emb2))
        cos_sim_unrelated = sum(a * b for a, b in zip(emb1, emb_unrelated))

        # Related telecom parts should have significantly higher similarity than unrelated accounting terms
        self.assertGreater(cos_sim_related, cos_sim_unrelated)
        self.assertGreater(cos_sim_related, 0.45)

    def test_auth_password_and_jwt(self):
        from app.core.auth import (
            hash_password,
            verify_password,
            create_access_token,
            decode_access_token
        )

        pwd = "EnterpriseSecurePass2026!"
        h, salt = hash_password(pwd)
        self.assertTrue(verify_password(pwd, h, salt))
        self.assertFalse(verify_password("WrongPassword!", h, salt))

        # Test JWT token lifecycle
        claims = {"sub": "sg_purchaser", "role": "purchasing", "entity": "SG"}
        token = create_access_token(claims)
        self.assertIsInstance(token, str)
        self.assertEqual(len(token.split('.')), 3)

        decoded = decode_access_token(token)
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded["sub"], "sg_purchaser")
        self.assertEqual(decoded["role"], "purchasing")
        self.assertEqual(decoded["entity"], "SG")

    def test_rbac_permissions(self):
        from app.core.auth import require_role_for_agent
        from fastapi import HTTPException

        purchaser = {"username": "sg_purchaser", "role": "purchasing"}
        sales = {"username": "sg_sales", "role": "sales"}
        admin = {"username": "admin", "role": "admin"}

        # Agent 1 (Quote) allows purchasing and admin
        require_role_for_agent("agent_1", purchaser)  # Should not raise
        require_role_for_agent("agent_1", admin)      # Should not raise
        with self.assertRaises(HTTPException):
            require_role_for_agent("agent_1", sales)  # Sales cannot approve procurement quotes!

        # Agent 3 (Backlog) allows sales and admin
        require_role_for_agent("agent_3", sales)      # Should not raise
        with self.assertRaises(HTTPException):
            require_role_for_agent("agent_3", purchaser) # Purchaser cannot approve sales backlogs!

if __name__ == "__main__":
    unittest.main()

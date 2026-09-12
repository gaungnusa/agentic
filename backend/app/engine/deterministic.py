from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any

# ==========================================
# FASE 1: FOUNDATION PILOT AGENTS
# ==========================================

def compute_agent3_rdd_delay(rdd_target_str: str, eta_str: str, order_value: float) -> dict:
    """Agent 3: Deteksi keterlambatan Request Delivery Date (RDD) & skor keparahan backlog"""
    rdd = datetime.strptime(rdd_target_str, "%Y-%m-%d").date()
    eta = datetime.strptime(eta_str, "%Y-%m-%d").date()
    delta_days = (eta - rdd).days
    is_delayed = delta_days > 0

    severity = "NORMAL"
    if delta_days > 14:
        severity = "CRITICAL"
    elif delta_days > 3:
        severity = "WARNING"

    return {
        "is_delayed": is_delayed,
        "delta_days": max(0, delta_days),
        "severity": severity,
        "order_value": order_value,
        "needs_escalation": severity in ["WARNING", "CRITICAL"]
    }

def compute_agent5_vendor_score(on_time_rate: float, quality_rate: float, price_variance_pct: float) -> dict:
    """Agent 5: Evaluasi performa vendor & rekomendasi kuota pengadaan sourcing"""
    # Bobot evaluasi: On-time 40%, Kualitas 40%, Selisih harga 20%
    price_score = max(0.0, 100.0 - abs(price_variance_pct * 2))
    composite_score = (on_time_rate * 0.4) + (quality_rate * 0.4) + (price_score * 0.2)
    
    tier = "TIER_3_RESTRICTED"
    allocation_pct = 0
    if composite_score >= 88.0:
        tier = "TIER_1_PREFERRED"
        allocation_pct = 70
    elif composite_score >= 70.0:
        tier = "TIER_2_STANDARD"
        allocation_pct = 30

    return {
        "composite_score": round(composite_score, 1),
        "vendor_tier": tier,
        "suggested_allocation_pct": allocation_pct,
        "is_eligible_for_po": composite_score >= 70.0
    }

def compute_agent9_cash_runway(current_cash: float, weekly_burn_rate: float, loan_due_7days: float) -> dict:
    """Agent 9: Perhitungan sisa runway kas operasional & proteksi denda likuiditas pinjaman OA"""
    net_usable_cash = current_cash - loan_due_7days
    weeks_runway = net_usable_cash / weekly_burn_rate if weekly_burn_rate > 0 else 999.0
    
    liquidity_status = "HEALTHY"
    if weeks_runway < 2.0 or net_usable_cash < 0:
        liquidity_status = "CRITICAL_DEFICIT"
    elif weeks_runway < 4.0:
        liquidity_status = "TIGHT"

    return {
        "net_usable_cash": round(net_usable_cash, 2),
        "weeks_runway": round(weeks_runway, 1),
        "liquidity_status": liquidity_status,
        "alert_treasury_lead": liquidity_status != "HEALTHY"
    }

# ==========================================
# FASE 2: VALIDATION AGENTS
# ==========================================

def compute_agent1_rfq_pricing(unit_cost: Optional[float], target_margin_pct: float = 18.0) -> dict:
    """Agent 1: Pencocokan katalog harga (PS03) vs kebutuhan RFQ sourcing paralel"""
    if unit_cost is not None and unit_cost > 0:
        selling_price = unit_cost / (1 - (target_margin_pct / 100))
        return {
            "catalog_matched": True,
            "unit_cost": round(unit_cost, 2),
            "target_margin_pct": target_margin_pct,
            "recommended_quote_price": round(selling_price, 2),
            "action_required": "GENERATE_CUSTOMER_QUOTE"
        }
    return {
        "catalog_matched": False,
        "unit_cost": None,
        "recommended_quote_price": None,
        "action_required": "DISPATCH_PARALLEL_SOURCING_RFQ"
    }

def compute_agent4_price_validity(days_left: int, items_count: int, inflation_adj_pct: float = 2.1) -> dict:
    """Agent 4: Master Price Validity Radar & Bulk Template Generator (Module PS03)"""
    status = "HEALTHY"
    if days_left <= 30:
        status = "EXPIRING_SOON"
    elif days_left <= 60:
        status = "SCHEDULED"

    renewal_urgency = "HIGH" if days_left <= 30 else ("MEDIUM" if days_left <= 60 else "LOW")
    return {
        "days_left": days_left,
        "items_count": items_count,
        "status": status,
        "renewal_urgency": renewal_urgency,
        "recommended_inflation_adjustment_pct": inflation_adj_pct,
        "bulk_template_format": "xlsx",
        "requires_renewal_action": days_left <= 60
    }


def compute_agent2_po_margin(so_price: float, po_cost: float, ordered_qty: int, moq: int, tier2_cost: Optional[float] = None) -> dict:
    """Agent 2: Hitung margin kotor deterministik dan cek batas MOQ"""
    gross_margin = ((so_price - po_cost) / so_price) * 100
    is_margin_breached = gross_margin < 15.0
    is_moq_breached = ordered_qty < moq
    
    remedy = None
    if (is_margin_breached or is_moq_breached) and tier2_cost:
        projected_margin = ((so_price - tier2_cost) / so_price) * 100
        remedy = {
            "suggested_qty": moq,
            "tier_price": tier2_cost,
            "projected_margin": round(projected_margin, 2),
            "buffer_stock_qty": moq - ordered_qty
        }
        
    return {
        "gross_margin_pct": round(gross_margin, 2),
        "is_margin_breached": is_margin_breached,
        "is_moq_breached": is_moq_breached,
        "remedy": remedy
    }

def compute_agent6_gr_split(po_expected_qty: int, scanned_qty: int, damaged_qty: int, unit_cost: float) -> dict:
    """Agent 6: Pemisahan penerimaan gudang (Partial GR valid vs Klaim Debit RMA barang rusak)"""
    valid_qty = scanned_qty - damaged_qty
    has_damage = damaged_qty > 0
    claim_amount = damaged_qty * unit_cost

    return {
        "po_expected_qty": po_expected_qty,
        "scanned_total": scanned_qty,
        "valid_gr_qty": max(0, valid_qty),
        "damaged_qty": damaged_qty,
        "rma_required": has_damage,
        "debit_claim_amount": round(claim_amount, 2),
        "is_partial_gr": valid_qty < po_expected_qty
    }

# ==========================================
# FASE 3: DEEP SYNC AGENTS
# ==========================================

def compute_agent7_triangle_pod(is_pod_received: bool, po_ref: str, so_ref: str) -> dict:
    """Agent 7: Verifikasi POD forwarder untuk posting sinkron Logical GR/GI bypass gudang fisik SG"""
    return {
        "pod_verified": is_pod_received,
        "po_reference": po_ref,
        "so_reference": so_ref,
        "posting_eligible": is_pod_received,
        "warehouse_mutation_required": False  # Aturan Section 6.3 Triangle Trade
    }

def compute_agent7_loan_maturity(borrowed_date_str: str, max_loan_days: int = 30) -> dict:
    """Agent 7: Radar jatuh tempo peminjaman stok antar-mitra (Alert H-5)"""
    borrowed_date = datetime.strptime(borrowed_date_str, "%Y-%m-%d").date()
    maturity_date = borrowed_date + timedelta(days=max_loan_days)
    days_left = (maturity_date - date.today()).days

    return {
        "days_left": days_left,
        "is_expiring_soon": days_left <= 5,
        "is_overdue": days_left < 0,
        "action_required": "DISPATCH_RETURN_ADVICE" if days_left <= 5 else "MONITOR"
    }

def compute_agent8_fx_split(amount_foreign: float, book_rate: float, settle_rate: float, currency_base: str = "SGD") -> dict:
    """Agent 8: Hitung selisih kurs transaksi vs settlement dan jurnal kliring"""
    book_value = amount_foreign * book_rate
    settle_value = amount_foreign * settle_rate
    fx_variance = settle_value - book_value  # Negatif = FX Loss, Positif = FX Gain
    
    return {
        "book_value": round(book_value, 2),
        "settle_value": round(settle_value, 2),
        "fx_variance": round(fx_variance, 2),
        "fx_type": "GAIN" if fx_variance >= 0 else "LOSS",
        "allocated_account": "7210" if fx_variance < 0 else "7110",
        "currency_base": currency_base
    }
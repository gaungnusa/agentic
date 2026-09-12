from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class AgentTriggerBase(BaseModel):
    entity_code: str = Field(..., examples=["SG"])
    reference_doc: str = Field(..., examples=["PO-2026-4412"])

# Agent 1: RFQ & Quotation
class Agent1Request(AgentTriggerBase):
    unit_cost: Optional[float] = Field(None, examples=[38.50])
    target_margin_pct: float = Field(18.0, examples=[18.0])

# Agent 2: SO/PO Mismatch
class POValidationRequest(AgentTriggerBase):
    so_number: str
    supplier_name: str
    so_selling_price: float
    po_cost_price: float
    ordered_qty: int
    supplier_moq: int
    tier2_cost_price: Optional[float] = None

# Agent 3: RDD Delay & Backlog
class Agent3RDDRequest(AgentTriggerBase):
    rdd_target_str: str = Field(..., examples=["2026-09-10"], description="Target Request Delivery Date (YYYY-MM-DD)")
    eta_str: str = Field(..., examples=["2026-09-20"], description="Estimated Time of Arrival (YYYY-MM-DD)")
    order_value: float = Field(..., examples=[45000.0])

# Agent 4: Price Validity & Renewal Radar
class Agent4Request(AgentTriggerBase):
    days_left: int = Field(..., examples=[28])
    items_count: int = Field(..., examples=[45])
    inflation_adj_pct: float = Field(2.1, examples=[2.1])

# Agent 5: Vendor Performance
class Agent5VendorScoreRequest(AgentTriggerBase):
    on_time_rate: float = Field(..., examples=[92.5], description="Percentage of on-time deliveries (0-100)")
    quality_rate: float = Field(..., examples=[95.0], description="Percentage of items passing QA (0-100)")
    price_variance_pct: float = Field(..., examples=[2.5], description="Price deviation from benchmark (%)")

# Agent 6: Goods Receipt & Damaged Goods Split
class Agent6Request(AgentTriggerBase):
    po_expected_qty: int = Field(..., examples=[1000])
    scanned_qty: int = Field(..., examples=[1000])
    damaged_qty: int = Field(..., examples=[80])
    unit_cost: float = Field(..., examples=[39.00])

# Agent 7: Triangle Trade POD
class Agent7TriangleRequest(BaseModel):
    entity_code: str = Field(..., examples=["SG"])
    po_ref: str = Field(..., examples=["PO-8812"])
    so_ref: str = Field(..., examples=["SO-3310"])
    is_pod_received: bool = Field(..., examples=[True])

# Agent 7: Loan Maturity Radar
class Agent7LoanMaturityRequest(AgentTriggerBase):
    borrowed_date_str: str = Field(..., examples=["2026-08-15"], description="Borrow date (YYYY-MM-DD)")
    max_loan_days: int = Field(30, examples=[30])

# Agent 8: AR/AP Reconciler
class BankMatchingRequest(AgentTriggerBase):
    bank_account_ref: str
    remittance_amount: float
    remittance_currency: str
    target_invoices: list[str]
    invoice_book_rate: float
    bank_settlement_rate: float

# Agent 9: Cash Flow & Runway
class Agent9CashRunwayRequest(AgentTriggerBase):
    current_cash: float = Field(..., examples=[120000.0], description="Current usable cash balance")
    weekly_burn_rate: float = Field(..., examples=[35000.0], description="Average weekly operational burn")
    loan_due_7days: float = Field(..., examples=[25000.0], description="Open account loan maturing in 7 days")

# HITL Decision Action
class HITLDecisionRequest(BaseModel):
    draft_action_id: str
    operator_id: str
    decision: str = Field(..., pattern="^(APPROVE|EDIT|DISCARD)$")
    modified_narrative: Optional[str] = None

# Chat Conversational Interface
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, examples=["Cek margin PO-2026-4412"])
    entity_code: str = Field(..., examples=["SG"])
    conversation_id: Optional[str] = Field(None, description="UUID of existing conversation, or null for new")

class ChatMessageOut(BaseModel):
    id: str
    role: str
    content: str
    agent_used: Optional[str] = None
    rich_card: Optional[Dict[str, Any]] = None
    draft_action_id: Optional[str] = None
    created_at: Optional[str] = None

class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    agent_used: Optional[str] = None
    rich_card: Optional[Dict[str, Any]] = None
    requires_hitl: bool = False
    draft_action_id: Optional[str] = None
    suggested_actions: list[str] = []
    switch_entity: Optional[str] = None
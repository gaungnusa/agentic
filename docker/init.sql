CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ============================================================================
-- 1. TABEL STAGING HUMAN-IN-THE-LOOP GATEWAY
-- ============================================================================
CREATE TABLE IF NOT EXISTS draft_agent_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(50) NOT NULL,            -- agent_1 s/d agent_9
    entity_code VARCHAR(10) NOT NULL,         -- SG, VN, KR, IN, JP
    module_code VARCHAR(20) NOT NULL,         -- PS01, PS02, PS03, PS06, PS07, IN01, 6.3_TT, AC01, AC02
    reference_doc VARCHAR(100) NOT NULL,      -- RFQ-xxx, PO-xxx, SO-xxx, TXN-xxx, LOAN-xxx
    deterministic_payload JSONB NOT NULL,     -- Data terverifikasi Python
    llm_draft_narrative TEXT,                 -- Teks draf rekomendasi AI
    status VARCHAR(20) DEFAULT 'PENDING',     -- PENDING, APPROVED, EDITED, DISCARDED
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_draft_entity_status ON draft_agent_actions(entity_code, status);
CREATE INDEX IF NOT EXISTS idx_draft_agent ON draft_agent_actions(agent_id);

-- ============================================================================
-- 2. TABEL AUDIT LOG PERMANEN (IMMUTABLE)
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_trail_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    draft_action_id UUID REFERENCES draft_agent_actions(id),
    operator_id VARCHAR(100) NOT NULL,
    entity_code VARCHAR(10) NOT NULL,
    event_action VARCHAR(50) NOT NULL,        -- APPROVED, EDITED, DISCARDED
    original_text TEXT,
    final_dispatched_text TEXT,
    execution_result JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_operator ON audit_trail_logs(operator_id);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_trail_logs(entity_code);

-- ============================================================================
-- 3. MOCK DATA ERP READ-REPLICA (5 LEGAL ENTITIES: SG, VN, KR, IN, JP)
-- ============================================================================

-- A. Master Price Catalog (PS03)
CREATE TABLE IF NOT EXISTS mock_master_price (
    part_number VARCHAR(50) PRIMARY KEY,
    description TEXT,
    unit_cost NUMERIC(12, 2),
    currency VARCHAR(5),
    moq_threshold INT,
    valid_until DATE,
    entity_code VARCHAR(10),
    embedding vector(384)
);

CREATE INDEX IF NOT EXISTS idx_master_price_vector ON mock_master_price USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10);

INSERT INTO mock_master_price (part_number, description, unit_cost, currency, moq_threshold, valid_until, entity_code)
VALUES 
('SFP-10G-LR', 'SFP+ 10G-LR Transceiver Module 10km', 38.50, 'USD', 100, '2026-12-31', 'SG'),
('OP-CABLE-48C', 'High-Density Patch Cord 48C Custom', 108.50, 'USD', 500, '2026-09-30', 'KR'),
('QSFP-100G-SR4', 'QSFP28 100G-SR4 Multi-Mode Optical Transceiver', 185.00, 'USD', 50, '2026-09-22', 'SG'),
('FIBER-OM4-12C', 'Indoor OM4 Fiber Optic Trunk Cable 12C', 450000.00, 'VND', 200, '2027-01-31', 'VN'),
('SWITCH-ACC-48P', 'Enterprise Gigabit Access Switch 48-Port PoE+', 85000.00, 'INR', 20, '2026-11-30', 'IN'),
('DWDM-MUX-16CH', '16-Channel Dense Wavelength Division Mux', 320000.00, 'JPY', 10, '2026-10-15', 'JP')
ON CONFLICT (part_number) DO NOTHING;

-- B. Borrowed Stock Inter-Partner (BRD 6.3 - Agent 7)
CREATE TABLE IF NOT EXISTS mock_borrowed_stock (
    loan_ref VARCHAR(50) PRIMARY KEY,
    partner_name VARCHAR(100) NOT NULL,
    part_number VARCHAR(50) NOT NULL,
    qty INT NOT NULL,
    borrowed_date DATE NOT NULL,
    max_loan_days INT DEFAULT 30,
    status VARCHAR(20) DEFAULT 'ACTIVE',     -- ACTIVE, RETURNED, OVERDUE
    entity_code VARCHAR(10) NOT NULL
);

INSERT INTO mock_borrowed_stock (loan_ref, partner_name, part_number, qty, borrowed_date, max_loan_days, status, entity_code)
VALUES
('LOAN-2026-SG-01', 'Singtel Network Services', 'SFP-10G-LR', 150, '2026-08-10', 30, 'ACTIVE', 'SG'),
('LOAN-2026-KR-02', 'SK Telecom Infra Tech', 'OP-CABLE-48C', 80, '2026-08-25', 30, 'ACTIVE', 'KR'),
('LOAN-2026-VN-03', 'Viettel Network Logistics', 'FIBER-OM4-12C', 300, '2026-08-01', 30, 'ACTIVE', 'VN')
ON CONFLICT (loan_ref) DO NOTHING;

-- C. Sales Orders & Backlog Tracker (PS06/07 - Agent 3)
CREATE TABLE IF NOT EXISTS mock_sales_orders (
    so_number VARCHAR(50) PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    part_number VARCHAR(50) NOT NULL,
    ordered_qty INT NOT NULL,
    selling_price NUMERIC(12, 2) NOT NULL,
    order_value NUMERIC(14, 2) NOT NULL,
    rdd_target DATE NOT NULL,
    eta_delivery DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'IN_PROGRESS',
    entity_code VARCHAR(10) NOT NULL
);

INSERT INTO mock_sales_orders (so_number, customer_name, part_number, ordered_qty, selling_price, order_value, rdd_target, eta_delivery, status, entity_code)
VALUES
('SO-2026-1182', 'Samsung SDS Seoul', 'OP-CABLE-48C', 350, 120.00, 42000.00, '2026-09-15', '2026-09-14', 'IN_PROGRESS', 'KR'),
('SO-2026-9021', 'VNPT Telecom Hanoi', 'FIBER-OM4-12C', 100, 520000.00, 52000000.00, '2026-09-10', '2026-09-22', 'IN_PROGRESS', 'VN'),
('SO-2026-4401', 'StarHub Singapore HQ', 'QSFP-100G-SR4', 200, 230.00, 46000.00, '2026-09-01', '2026-09-21', 'IN_PROGRESS', 'SG'),
('SO-3310', 'NTT Communications Tokyo', 'SFP-10G-LR', 500, 55.00, 27500.00, '2026-09-25', '2026-09-24', 'IN_PROGRESS', 'JP')
ON CONFLICT (so_number) DO NOTHING;

-- D. Purchase Orders & Goods Receipt (PS02, IN01 - Agent 2, 6, 7)
CREATE TABLE IF NOT EXISTS mock_purchase_orders (
    po_number VARCHAR(50) PRIMARY KEY,
    so_number VARCHAR(50),
    supplier_name VARCHAR(100) NOT NULL,
    part_number VARCHAR(50) NOT NULL,
    ordered_qty INT NOT NULL,
    po_cost_price NUMERIC(12, 2) NOT NULL,
    supplier_moq INT NOT NULL,
    tier2_cost_price NUMERIC(12, 2),
    expected_qty INT NOT NULL,
    scanned_qty INT DEFAULT 0,
    damaged_qty INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'ISSUED',
    entity_code VARCHAR(10) NOT NULL
);

INSERT INTO mock_purchase_orders (po_number, so_number, supplier_name, part_number, ordered_qty, po_cost_price, supplier_moq, tier2_cost_price, expected_qty, scanned_qty, damaged_qty, status, entity_code)
VALUES
('PO-2026-4412', 'SO-2026-1182', 'Broadcom APAC Ltd', 'OP-CABLE-48C', 350, 108.50, 500, 94.00, 350, 0, 0, 'ISSUED', 'KR'),
('PO-2026-9902', 'SO-2026-4401', 'Molex Asia Pacific', 'SFP-10G-LR', 1000, 39.00, 500, 35.00, 1000, 1000, 80, 'DOCK_SCAN', 'SG'),
('PO-8812', 'SO-3310', 'Sumitomo Electric Japan', 'SFP-10G-LR', 500, 38.50, 100, 34.00, 500, 500, 0, 'IN_TRANSIT', 'SG')
ON CONFLICT (po_number) DO NOTHING;

-- E. Vendor Performance Directory (PS07 - Agent 5)
CREATE TABLE IF NOT EXISTS mock_vendors (
    vendor_code VARCHAR(50) PRIMARY KEY,
    vendor_name VARCHAR(100) NOT NULL,
    country VARCHAR(10) NOT NULL,
    on_time_rate NUMERIC(5, 2) NOT NULL,
    quality_rate NUMERIC(5, 2) NOT NULL,
    price_variance_pct NUMERIC(5, 2) NOT NULL,
    entity_code VARCHAR(10) NOT NULL
);

INSERT INTO mock_vendors (vendor_code, vendor_name, country, on_time_rate, quality_rate, price_variance_pct, entity_code)
VALUES
('VEND-SG-01', 'Amphenol Singapore Pte Ltd', 'SG', 95.50, 96.00, 1.20, 'SG'),
('VEND-KR-02', 'Broadcom APAC Korea Ltd', 'KR', 82.00, 89.50, 3.50, 'KR'),
('VEND-VN-03', 'Foxconn Precision Vietnam', 'VN', 65.00, 68.00, 11.50, 'VN'),
('VEND-JP-04', 'Sumitomo Electric Industries', 'JP', 98.00, 99.00, -0.50, 'JP'),
('VEND-IN-05', 'Sterlite Technologies Pune', 'IN', 88.50, 91.00, 2.00, 'IN')
ON CONFLICT (vendor_code) DO NOTHING;

-- F. Bank Transactions & Multi-Currency Statements (AC02 - Agent 8)
CREATE TABLE IF NOT EXISTS mock_bank_transactions (
    txn_ref VARCHAR(50) PRIMARY KEY,
    bank_account_ref VARCHAR(50) NOT NULL,
    remittance_currency VARCHAR(5) NOT NULL,
    remittance_amount NUMERIC(14, 2) NOT NULL,
    book_rate NUMERIC(10, 4) NOT NULL,
    settle_rate NUMERIC(10, 4) NOT NULL,
    target_invoices JSONB NOT NULL,
    entity_code VARCHAR(10) NOT NULL
);

INSERT INTO mock_bank_transactions (txn_ref, bank_account_ref, remittance_currency, remittance_amount, book_rate, settle_rate, target_invoices, entity_code)
VALUES
('TXN-DBS-88319', 'DBS USD Treasury', 'USD', 74500.00, 1.3500, 1.3420, '["INV-0412", "INV-0413"]'::jsonb, 'SG'),
('TXN-SHB-44102', 'Shinhan Bank KRW Operating', 'USD', 52000.00, 1340.0000, 1355.0000, '["INV-KR-901"]'::jsonb, 'KR'),
('TXN-VCB-11928', 'Vietcombank Operating VND', 'USD', 35000.00, 24500.0000, 24620.0000, '["INV-VN-332"]'::jsonb, 'VN')
ON CONFLICT (txn_ref) DO NOTHING;

-- G. Operational Cash & Liquidity Reserves (AC01 - Agent 9)
CREATE TABLE IF NOT EXISTS mock_entity_cash (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_code VARCHAR(10) UNIQUE NOT NULL,
    period_ref VARCHAR(50) NOT NULL,
    current_cash NUMERIC(14, 2) NOT NULL,
    weekly_burn_rate NUMERIC(14, 2) NOT NULL,
    loan_due_7days NUMERIC(14, 2) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO mock_entity_cash (entity_code, period_ref, current_cash, weekly_burn_rate, loan_due_7days)
VALUES
('SG', 'CASH-WK36-2026', 185000.00, 32000.00, 45000.00),
('VN', 'CASH-WK36-2026', 95000.00, 18000.00, 15000.00),
('KR', 'CASH-WK36-2026', 34000.00, 22000.00, 12000.00),
('IN', 'CASH-WK36-2026', 42000.00, 10000.00, 5000.00),
('JP', 'CASH-WK36-2026', 220000.00, 25000.00, 30000.00)
ON CONFLICT (entity_code) DO UPDATE 
SET current_cash = EXCLUDED.current_cash,
    weekly_burn_rate = EXCLUDED.weekly_burn_rate,
    loan_due_7days = EXCLUDED.loan_due_7days,
    updated_at = NOW();

-- ============================================================================
-- 4. USER AUTHENTICATION & ROLE-BASED ACCESS CONTROL (RBAC)
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    role VARCHAR(30) NOT NULL,            -- 'purchasing', 'sales', 'warehouse', 'treasury', 'auditor', 'admin'
    entity_code VARCHAR(10) NOT NULL,     -- 'SG', 'VN', 'KR', 'IN', 'JP', 'ALL'
    salt VARCHAR(64) NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

INSERT INTO users (username, full_name, email, role, entity_code, salt, password_hash)
VALUES
('admin', 'Enterprise System Administrator', 'admin@batu-networks.com', 'admin', 'ALL', 'd981a2f1c8b3e4a5', '25f448c5a2c2049d53ea7fbb05fbcba0e08f2343c3f29bda16999330da37f261'),
('sg_purchaser', 'Tan Wei Ming (Purchasing Specialist)', 'weiming.tan@batu-networks.sg', 'purchasing', 'SG', '7f8b9c0d1e2f3a4b', 'a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0'),
('sg_sales', 'Clara Lim (Regional Sales Director)', 'clara.lim@batu-networks.sg', 'sales', 'SG', '1a2b3c4d5e6f7a8b', 'b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef01'),
('vn_logistics', 'Nguyen Van Thao (Warehouse Supervisor)', 'thao.nguyen@batu-networks.vn', 'warehouse', 'VN', '3c4d5e6f7a8b1a2b', 'c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef012'),
('sg_treasurer', 'Marcus Goh (Treasury Controller)', 'marcus.goh@batu-networks.sg', 'treasury', 'SG', '5e6f7a8b1a2b3c4d', 'd4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0123'),
('compliance_auditor', 'Sarah Jenkins (Senior Audit Officer)', 'sarah.jenkins@batu-networks.com', 'auditor', 'ALL', '7a8b1a2b3c4d5e6f', 'e5f67890123456789abcdef0123456789abcdef0123456789abcdef01234')
ON CONFLICT (username) DO NOTHING;

-- ============================================================================
-- 5. CHAT CONVERSATION HISTORY (PERSISTENT AGENTIC DIALOG)
-- ============================================================================
CREATE TABLE IF NOT EXISTS chat_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_code VARCHAR(10) NOT NULL,
    username VARCHAR(50) NOT NULL,
    title VARCHAR(200) DEFAULT 'Percakapan Baru',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_conv_user ON chat_conversations(username, entity_code);

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES chat_conversations(id) ON DELETE CASCADE,
    role VARCHAR(10) NOT NULL,            -- 'user' | 'assistant'
    content TEXT NOT NULL,
    agent_used VARCHAR(20),               -- 'agent_1' .. 'agent_9' | null
    rich_card JSONB,                      -- Structured data for frontend rendering
    draft_action_id UUID,                 -- Link to HITL staging table
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_msg_conv ON chat_messages(conversation_id, created_at);
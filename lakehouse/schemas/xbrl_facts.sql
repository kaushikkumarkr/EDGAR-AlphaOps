CREATE TABLE IF NOT EXISTS xbrl_facts (
    id VARCHAR, -- validation_id or similar unique ID if needed, else composite PK
    cik VARCHAR NOT NULL,
    taxonomy VARCHAR NOT NULL, -- us-gaap, dei
    tag VARCHAR NOT NULL, -- RevenueFromContractWithCustomerExcludingAssessedTax, NetIncomeLoss
    period_start DATE, -- Null for instant concepts (Balance Sheet)
    period_end DATE,
    period_instant DATE, -- Null for duration concepts (Income Statement)
    unit VARCHAR, -- USD, shares, pure
    value DOUBLE, -- Numeric value
    accession_number VARCHAR, -- Link to source filing
    fy INTEGER, -- Fiscal Year
    fp VARCHAR, -- Fiscal Period (Q1, Q2, Q3, FY)
    form VARCHAR, -- 10-K, 10-Q
    filed_date DATE,
    frame VARCHAR, -- e.g. "CY2023Q1I" - useful for cross-company comparison
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast lookup by company and tag
CREATE INDEX IF NOT EXISTS idx_xbrl_cik_tag ON xbrl_facts(cik, tag);
-- Index for time-series range
CREATE INDEX IF NOT EXISTS idx_xbrl_period_end ON xbrl_facts(period_end);

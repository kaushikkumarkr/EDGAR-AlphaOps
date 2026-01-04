CREATE TABLE IF NOT EXISTS filings (
    accession_number VARCHAR PRIMARY KEY,
    cik VARCHAR NOT NULL,
    ticker VARCHAR, -- Nullable, processed later
    company_name VARCHAR,
    form_type VARCHAR NOT NULL,
    filing_date DATE,
    report_period DATE,
    acceptance_datetime TIMESTAMP,
    primary_doc_url VARCHAR,
    filing_html_path VARCHAR, -- Local path
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_filings_cik ON filings(cik);
CREATE INDEX IF NOT EXISTS idx_filings_date ON filings(filing_date);

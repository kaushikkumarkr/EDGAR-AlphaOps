CREATE TABLE IF NOT EXISTS companies (
    cik VARCHAR PRIMARY KEY,
    ticker VARCHAR NOT NULL,
    company_name VARCHAR NOT NULL,
    sic VARCHAR, -- Standard Industrial Classification
    sic_description VARCHAR, -- e.g. "Services-Packaged Software"
    exchanges VARCHAR[], -- List of exchanges if available in data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_companies_ticker ON companies(ticker);

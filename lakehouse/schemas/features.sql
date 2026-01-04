CREATE TABLE IF NOT EXISTS features (
    cik VARCHAR NOT NULL,
    ticker VARCHAR NOT NULL,
    asof_date DATE NOT NULL,
    period_end DATE,
    
    -- Fundamentals (TTM or Point in Time)
    revenue_ttm DOUBLE,
    net_income_ttm DOUBLE,
    revenue_growth_yoy DOUBLE,
    net_margin DOUBLE,
    
    -- Market Data (Snapshot at asof_date)
    price_close DOUBLE,
    price_1d_return DOUBLE,
    volatility_30d DOUBLE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (cik, asof_date)
);

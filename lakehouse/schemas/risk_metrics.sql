CREATE TABLE IF NOT EXISTS risk_metrics (
    metric_id VARCHAR PRIMARY KEY, -- uuid
    ticker VARCHAR NOT NULL,
    asof_date DATE NOT NULL,
    
    -- Volatility
    volatility_30d DOUBLE, -- Redundant with prices, but good for snapshots
    volatility_regime VARCHAR, -- "Low", "Normal", "High", "Crisis"
    
    -- Value at Risk
    var_95 DOUBLE, -- 95% Confidence VaR (1-day)
    var_99 DOUBLE, -- 99% Confidence VaR (1-day)
    cvar_95 DOUBLE, -- Conditional VaR (Expected Shortfall)
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_risk_ticker ON risk_metrics(ticker, asof_date);

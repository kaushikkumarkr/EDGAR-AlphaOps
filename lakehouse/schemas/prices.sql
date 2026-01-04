CREATE TABLE IF NOT EXISTS prices (
    ticker VARCHAR NOT NULL,
    date DATE NOT NULL,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume BIGINT,
    adjusted_close DOUBLE,
    daily_return DOUBLE,
    volatility_30d DOUBLE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ticker, date)
);

CREATE INDEX IF NOT EXISTS idx_prices_ticker_date ON prices(ticker, date);

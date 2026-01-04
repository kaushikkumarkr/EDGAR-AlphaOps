CREATE TABLE IF NOT EXISTS event_studies (
    study_id VARCHAR PRIMARY KEY, -- uuid
    cik VARCHAR NOT NULL,
    ticker VARCHAR NOT NULL,
    event_date DATE NOT NULL,
    event_type VARCHAR, -- e.g. "10-K", "10-Q"
    
    -- Parameters
    estimation_window_start DATE,
    estimation_window_end DATE,
    
    -- Results
    alpha DOUBLE,
    beta DOUBLE,
    r_squared DOUBLE,
    
    car_window VARCHAR, -- e.g. "-2,2"
    car_value DOUBLE, -- Cumulative Abnormal Return
    t_stat DOUBLE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_events_ticker ON event_studies(ticker);

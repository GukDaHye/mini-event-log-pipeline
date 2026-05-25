CREATE TABLE IF NOT EXISTS events (
    event_id      BIGSERIAL PRIMARY KEY,
    event_type    VARCHAR(20)  NOT NULL,
    user_id       VARCHAR(36)  NOT NULL,
    session_id    VARCHAR(36)  NOT NULL,
    event_time    TIMESTAMPTZ  NOT NULL,
    page_url      TEXT,
    product_id    VARCHAR(20),
    quantity      INTEGER,
    amount        NUMERIC(12,2),
    error_code    VARCHAR(20),
    error_message TEXT,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_events_type ON events (event_type);
CREATE INDEX IF NOT EXISTS idx_events_time ON events (event_time);
CREATE INDEX IF NOT EXISTS idx_events_user ON events (user_id);

-- ============================================================================
-- Postgres seed script for the Optimized Batch ML Inference quickstart.
--
-- Run this against your external Postgres instance (RDS, on-prem, etc.) before
-- starting the quickstart. It creates a `payments.transactions` table with
-- 50,000 synthetic card transactions over the last 90 days.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS payments;

DROP TABLE IF EXISTS payments.transactions;
CREATE TABLE payments.transactions (
    txn_id              BIGINT PRIMARY KEY,
    customer_id         INTEGER NOT NULL,
    txn_amount          NUMERIC(12, 2) NOT NULL,
    txn_timestamp       TIMESTAMP NOT NULL,
    merchant_category   TEXT NOT NULL,
    merchant_country    TEXT NOT NULL,
    is_online           BOOLEAN NOT NULL
);

INSERT INTO payments.transactions
SELECT
    i AS txn_id,
    1 + floor(random() * 500)::INT AS customer_id,
    round((random() * 2000 + 5)::numeric, 2) AS txn_amount,
    NOW() - (random() * interval '90 days') AS txn_timestamp,
    (ARRAY['travel','online_retail','electronics','restaurant','gas','grocery'])[1 + floor(random() * 6)] AS merchant_category,
    (ARRAY['US','CA','GB','FR','DE','JP'])[1 + floor(random() * 6)] AS merchant_country,
    random() < 0.4 AS is_online
FROM generate_series(1, 50000) AS i;

CREATE INDEX idx_txn_customer ON payments.transactions(customer_id);
CREATE INDEX idx_txn_timestamp ON payments.transactions(txn_timestamp);

SELECT COUNT(*) AS total_transactions FROM payments.transactions;

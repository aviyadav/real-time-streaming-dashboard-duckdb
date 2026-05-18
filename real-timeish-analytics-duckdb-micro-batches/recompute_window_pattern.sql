CREATE TABLE IF NOT EXISTS rollup_minute (
  minute TIMESTAMP,
  event  VARCHAR,
  cnt    BIGINT,
  PRIMARY KEY (minute, event)
);

-- Recompute last 5 minutes (idempotent)
BEGIN TRANSACTION;

DELETE FROM rollup_minute
WHERE minute >= date_trunc('minute', now() - INTERVAL 5 MINUTE);

INSERT INTO rollup_minute
SELECT
  date_trunc('minute', ts) AS minute,
  event,
  count(*) AS cnt
FROM read_parquet('lake/events/**/*.parquet')
WHERE ts >= now() - INTERVAL 5 MINUTE
GROUP BY 1, 2;

COMMIT;
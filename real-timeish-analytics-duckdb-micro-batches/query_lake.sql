SELECT
  date_trunc('minute', ts) AS minute,
  event,
  count(*) AS cnt
FROM read_parquet('lake/events/**/*.parquet')
WHERE ts >= now() - INTERVAL 15 MINUTE
GROUP BY 1, 2
ORDER BY 1, 2;
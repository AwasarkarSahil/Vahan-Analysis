-- create tables from CSV (sqlite CLI example)
.mode csv
.import data/processed/maker_monthly.csv maker_monthly

-- Yearly aggregation
CREATE TABLE maker_yearly AS
SELECT strftime('%Y', date) as year, maker, SUM(registrations) as registrations
FROM maker_monthly
GROUP BY year, maker;

-- YoY percent change (SQLite window functions)
SELECT year, maker, registrations,
  (registrations - LAG(registrations) OVER (PARTITION BY maker ORDER BY year))*100.0 / LAG(registrations) OVER (PARTITION BY maker ORDER BY year) as yoy_pct
FROM maker_yearly
ORDER BY maker, year;

DROP VIEW IF EXISTS view_date;
CREATE VIEW view_date AS
WITH RECURSIVE bounds AS (SELECT min(date_key) lo,max(date_key) hi FROM activity_points),
calendar(d,last) AS (
 SELECT date(substr(lo,1,4)||'-'||substr(lo,5,2)||'-'||substr(lo,7,2)),
 date(substr(hi,1,4)||'-'||substr(hi,5,2)||'-'||substr(hi,7,2)) FROM bounds WHERE lo IS NOT NULL
 UNION ALL SELECT date(d,'+1 day'),last FROM calendar WHERE d<last)
SELECT cast(strftime('%Y%m%d',d) AS INTEGER) AS date_key,d AS date,
 cast(strftime('%Y',d) AS INTEGER) AS year,cast(strftime('%m',d) AS INTEGER) AS month_number,
 cast((cast(strftime('%m',d) AS INTEGER)-1)/3+1 AS INTEGER) AS quarter_number,
 cast(strftime('%W',d) AS INTEGER) AS week_number,
 cast(strftime('%w',d) AS INTEGER) AS day_of_week,
 date(d, '-' || ((cast(strftime('%w',d) AS INTEGER)+6)%7) || ' days') AS week_start_date,
 date(d, '-' || ((cast(strftime('%w',d) AS INTEGER)+6)%7) || ' days', '+6 days') AS week_end_date
FROM calendar;

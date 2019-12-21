DROP VIEW IF EXISTS model_expedition;
CREATE VIEW model_expedition AS
SELECT
     e.expid      AS expedition_id
    ,e.peakid     AS peak_id
    ,e.year       AS expedition_year
    ,s.seasonname AS season
    ,p.himal      AS himal
    ,CASE e.comrte
        WHEN 1 THEN 'Y'
        ELSE 'N'
     END AS commercial_route
FROM hdb_expedition AS e
INNER JOIN feat_peak AS p
    ON (e.peakid = p.peak_id)
LEFT JOIN hdb_season AS s
    ON (e.season = s.season)
WHERE   e.claimed  = 0
    AND e.disputed = 0;
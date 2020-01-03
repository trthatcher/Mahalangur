DROP VIEW IF EXISTS model_member;
CREATE VIEW model_member AS
SELECT
     m.expid  AS expedition_id
    ,m.membid AS member_id
    ,m.sex
    ,m.calcage AS age
    ,CASE m.mo2used
        WHEN 1 THEN 'Y'
        ELSE 'N'
     END AS o2_used
    ,CASE
        WHEN m.msmtterm = 1 THEN 'Y'
        ELSE 'N'
     END AS successful_summit
FROM hdb_member AS m
WHERE   m.HIRED     = 0
    AND m.SHERPA    = 0
    AND m.TIBETAN   = 0
    AND m.mclaimed  = 0
    AND m.mdisputed = 0;
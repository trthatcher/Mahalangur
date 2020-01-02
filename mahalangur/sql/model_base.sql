DROP VIEW IF EXISTS model_base;
CREATE VIEW model_base AS
SELECT
     e.expedition_id
    ,m.member_id
    ,e.expedition_year
    ,e.season
    ,e.himal
    ,e.peak_id
    ,e.height
    ,e.commercial_route
    ,e.total_members
    ,e.total_hired
    ,m.sex
    ,m.age
    ,m.o2_used
    ,m.successful_summit
FROM model_expedition AS e
INNER JOIN model_member AS m
    ON (e.expedition_id = m.expedition_id);
DROP TABLE IF EXISTS hdb_season;
CREATE TABLE hdb_season(
     season     INTEGER NOT NULL PRIMARY KEY
    ,seasonname TEXT
    ,startday   INT
) WITHOUT ROWID;
DROP TABLE IF EXISTS hdb_termreason;
CREATE TABLE hdb_termreason(
     TERMREASON     INTEGER NOT NULL PRIMARY KEY
    ,TERMREASONDESC TEXT
) WITHOUT ROWID;
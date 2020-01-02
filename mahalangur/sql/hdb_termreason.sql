DROP TABLE IF EXISTS hdb_termreason;
CREATE TABLE hdb_termreason(
     termreason     INTEGER NOT NULL PRIMARY KEY
    ,termreasondesc TEXT
) WITHOUT ROWID;
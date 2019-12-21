DROP TABLE IF EXISTS hdb_injurytype;
CREATE TABLE hdb_injurytype(
     injurytype     INTEGER NOT NULL PRIMARY KEY
    ,injurytypedesc TEXT
) WITHOUT ROWID;
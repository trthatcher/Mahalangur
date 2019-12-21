DROP TABLE IF EXISTS hdb_deathtype;
CREATE TABLE hdb_deathtype(
     deathtype     INTEGER NOT NULL PRIMARY KEY
    ,deathtypedesc TEXT
) WITHOUT ROWID;
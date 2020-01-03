DROP TABLE IF EXISTS hdb_msmtnote;
CREATE TABLE hdb_msmtnote(
     msmtnote     INTEGER NOT NULL PRIMARY KEY
    ,msmtnotedesc TEXT
) WITHOUT ROWID;
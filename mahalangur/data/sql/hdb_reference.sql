DROP TABLE IF EXISTS hdb_reference;
CREATE TABLE hdb_reference(
     expid      CHAR(9)      NOT NULL
    ,refid      CHAR(2)      NOT NULL
    ,ryear      CHAR(4)
    ,rtype      INTEGER
    ,rjrnl      VARCHAR(4)
    ,rauthor    VARCHAR(140)
    ,rtitle     VARCHAR(210)
    ,rpublisher VARCHAR(70)
    ,rpubdate   CHAR(4)
    ,rlanguage  VARCHAR(30)
    ,rcitation  VARCHAR(30)
    ,ryak94     VARCHAR(5)
    ,rnotes     TEXT
    ,PRIMARY KEY (EXPID ASC, REFID ASC)
) WITHOUT ROWID;
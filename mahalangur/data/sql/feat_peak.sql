DROP TABLE IF EXISTS feat_peak;
CREATE TABLE feat_peak(
     peak_id                 CHAR(4) NOT NULL PRIMARY KEY
    ,peak_name               TEXT
    ,alt_names               TEXT
    ,"location"              TEXT
    ,height                  INTEGER
    ,approximate_coordinates CHAR(1)
    ,longitude               REAL
    ,latitude                REAL
    ,dms_longitude           TEXT
    ,dms_latitude            TEXT
    ,coordinate_notes        TEXT
    ,himal                   TEXT
) WITHOUT ROWID;
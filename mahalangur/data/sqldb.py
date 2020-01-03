import logging
import sqlite3
import importlib.resources as res
from . import utils
from .. import DATA_DIR, DATABASE_PATH, LOG_FORMAT
from pathlib import Path


### Globals
SCHEMA_TABLES = [
    'ref_peak.sql',
    'hdb_deathclass.sql',
    'hdb_deathtype.sql',
    'hdb_expedition.sql',
    'hdb_himal.sql',
    'hdb_injurytype.sql',
    'hdb_member.sql',
    'hdb_msmtbid.sql',
    'hdb_msmtnote.sql',
    'hdb_msmtterm.sql',
    'hdb_peak.sql',
    'hdb_reference.sql',
    'hdb_season.sql',
    'hdb_termreason.sql'
]

SCHEMA_VIEWS = [
    'model_expedition.sql',
    'model_member.sql',
    'model_base.sql'
]

DATA_FILES = {
    'hdb_member'    : ['processed', 'hdb_member.txt'    ],
    'hdb_peak'      : ['processed', 'hdb_peak.txt'      ],
    'hdb_expedition': ['processed', 'hdb_expedition.txt'],
    'hdb_reference' : ['processed', 'hdb_reference.txt' ]
}

METADATA_FILES = {
    'ref_peak'      : 'ref_peak.txt'      ,
    'hdb_deathclass': 'hdb_deathclass.txt',
    'hdb_deathtype' : 'hdb_deathtype.txt' ,
    'hdb_himal'     : 'hdb_himal.txt'     ,
    'hdb_injurytype': 'hdb_injurytype.txt',
    'hdb_msmtbid'   : 'hdb_msmtbid.txt'   ,
    'hdb_msmtnote'  : 'hdb_msmtnote.txt'  ,
    'hdb_msmtterm'  : 'hdb_msmtterm.txt'  ,
    'hdb_season'    : 'hdb_season.txt'    ,
    'hdb_termreason': 'hdb_termreason.txt'
}


### Functions

def create_objects(db_conn, object_list, object_type='table',
                   logger=logging.getLogger(__name__)):
    db_csr = db_conn.cursor()
    for object in object_list:
        with res.open_text('mahalangur.data.sql', object) as sql_file:
            sql_script = sql_file.read()

        db_csr.executescript(sql_script)

        logger.info('created {} \'{}\''.format(object_type, object))
    
    db_csr.close()
    db_conn.commit()


def load_metadata_tables(db_conn, metadata_files):
    for table_name, file_name in metadata_files.items():
        with res.path('mahalangur.data.metadata', file_name) as dsv_path:
            utils.import_delimited(db_conn, table_name, dsv_path)

    return db_conn


def load_data_tables(db_conn, data_dir, data_files):
    if isinstance(data_dir, str):
        data_dir = Path(data_dir)

    for table_name, file_path in data_files.items():
        dsv_path = data_dir.joinpath(*file_path).resolve()

        utils.import_delimited(db_conn, table_name, dsv_path)

    return db_conn


def create_database():
    logger = logging.getLogger('mahalangur.data.sqldb')

    logger.info('creating database \'{}\'...'.format(DATABASE_PATH.name))
    db_conn = sqlite3.connect(DATABASE_PATH)

    logger.info('creating database schema...')
    create_objects(db_conn, object_list=SCHEMA_TABLES, object_type='table',
                   logger=logger)
    create_objects(db_conn, object_list=SCHEMA_VIEWS, object_type='view',
                   logger=logger)

    logger.info('loading metadata tables...')
    load_metadata_tables(db_conn, METADATA_FILES)

    logger.info('loading data tables...')
    load_data_tables(db_conn, DATA_DIR, DATA_FILES)

    db_conn.close()
    logger.info('closed connection to \'{}\''.format(DATABASE_PATH.name))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    create_database()

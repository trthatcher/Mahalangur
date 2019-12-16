import csv
import logging
import sqlite3
from pathlib import Path
from .  import utils
from .. import DATASETS_DIR, LOG_FORMAT, PACKAGE_DIR


### Globals
SQL_DIR = (PACKAGE_DIR / 'data' / 'sql').resolve()
SCHEMA_TABLES = [
    'hdb_deathclass',
    'hdb_deathtype',
    'hdb_expedition',
    'hdb_himal',
    'hdb_injurytype',
    'hdb_member',
    'hdb_msmtbid',
    'hdb_msmtnote',
    'hdb_msmtterm',
    'hdb_peak',
    'hdb_reference',
    'hdb_season',
    'hdb_termreason'
]

DATA_FILES = {
    'hdb_member'    : ['interim', 'hdb_members.txt'],
    'hdb_peak'      : ['interim', 'hdb_peaks.txt'],
    'hdb_expedition': ['interim', 'hdb_exped.txt'],
    'hdb_reference' : ['interim', 'hdb_refer.txt'],
    'hdb_deathclass': ['static', 'hdb_deathclass.txt'],
    'hdb_deathtype' : ['static', 'hdb_deathtype.txt'],
    'hdb_himal'     : ['static', 'hdb_himal.txt'],
    'hdb_injurytype': ['static', 'hdb_injurytype.txt'],
    'hdb_msmtbid'   : ['static', 'hdb_msmtbid.txt'],
    'hdb_msmtnote'  : ['static', 'hdb_msmtnote.txt'],
    'hdb_msmtterm'  : ['static', 'hdb_msmtterm.txt'],
    'hdb_season'    : ['static', 'hdb_season.txt'],
    'hdb_termreason': ['static', 'hdb_termreason.txt']
}


### Functions

def create_objects(db_conn, script_dir, object_list, object_type='table',
                   logger=logging.getLogger(__name__)):
    if isinstance(script_dir, str):
        script_dir = Path(script_dir)

    db_csr = db_conn.cursor()
    for object in object_list:
        sql_path = (script_dir / '{}.sql'.format(object)).resolve()

        with open(sql_path, 'r', encoding='utf-8') as sql_file:
            db_csr.executescript(sql_file.read())

        logger.info('created {} \'{}\''.format(object_type, object))
    
    db_csr.close()
    db_conn.commit()


def load_tables(db_conn, data_dir, data_files):
    if isinstance(data_dir, str):
        data_dir = Path(data_dir)

    for table_name, file_path in data_files.items():
        dsv_path = data_dir.joinpath(*file_path).resolve()

        utils.import_delimited(db_conn, table_name, dsv_path)


def main():
    logger = logging.getLogger('mahalangur.data.sqlitedb')

    db_path = (DATASETS_DIR / 'mahalangur.db').resolve()

    logger.info('creating database \'{}\''.format(db_path.name))
    db_conn = sqlite3.connect(db_path)

    logger.info('creating database schema')
    create_objects(db_conn, script_dir=SQL_DIR, object_list=SCHEMA_TABLES,
                   object_type='table', logger=logger)

    logger.info('loading tables')
    load_tables(db_conn, DATASETS_DIR, DATA_FILES)

    db_conn.close()
    logger.info('closed connection to \'{}\''.format(db_path.name))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    main()

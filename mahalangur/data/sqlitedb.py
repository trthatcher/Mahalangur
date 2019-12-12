import csv
import logging
import sqlite3
from pathlib import Path
from .  import utils
from .. import DATASETS_DIR, LOG_FORMAT, PACKAGE_DIR


### Globals
INTERIM_DIR = (DATASETS_DIR / 'interim').resolve()
SQL_DIR = (PACKAGE_DIR / 'data' / 'sql').resolve()
SCHEMA_TABLES = ['hdb_peak', 'hdb_expedition', 'hdb_member', 'hdb_reference']

DATA_FILES = {
    'hdb_members.txt': 'hdb_member',
    'hdb_peaks.txt'  : 'hdb_peak',
    'hdb_exped.txt'  : 'hdb_expedition',
    'hdb_refer.txt'  : 'hdb_reference'
}

### Functions

def create_objects(db_conn, script_dir, object_list, object_type='table'):
    if isinstance(script_dir, str):
        script_dir = Path(script_dir)

    logger = logging.getLogger(__name__)

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

    for file_name, table_name in data_files.items():
        dsv_path = (data_dir / file_name).resolve()

        utils.import_delimited(db_conn, table_name, dsv_path)


def main():
    logger = logging.getLogger(__name__)

    db_path = (DATASETS_DIR / 'mahalangur.db').resolve()

    logger.info('creating database \'{}\''.format(db_path.name))
    db_conn = sqlite3.connect(db_path)

    logger.info('creating database schema')

    create_objects(db_conn, script_dir=SQL_DIR, object_list=SCHEMA_TABLES,
                   object_type='table')

    logger.info('loading tables')

    load_tables(db_conn, INTERIM_DIR, DATA_FILES)

    db_conn.close()
    logger.info('closed connection to \'{}\''.format(db_path.name))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    main()

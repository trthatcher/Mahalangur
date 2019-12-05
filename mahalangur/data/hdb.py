# -*- coding: utf-8 -*-
import csv
import logging
import zipfile
from .. import DATASETS_DIR, LOG_FORMAT
from .utils import download_file
from dbfread import DBF
from pathlib import Path, PurePath
from tqdm import tqdm


### Globals

HDB_ZIP_PATH = (DATASETS_DIR / 'raw' / 'himalayan-database.zip').resolve()
HDB_RAW_DIR = (DATASETS_DIR / 'raw' / 'himalayan-database').resolve()
HDB_INTERIM_DIR = (DATASETS_DIR / 'interim').resolve()
HDB_URL = ('https://www.himalayandatabase.com/downloads/' +
           'Himalayan%20Database.zip')
HDB_TABLES = ['members', 'exped', 'peaks', 'refer']
HDB_DUPLICATES = {
    'exped'  : (('EXPID',), 'YEAR'),
    'members': (('EXPID', 'MEMBID'), 'MYEAR'),
    'refer'  : (('EXPID', 'REFID'), 'RYEAR'),
    'peaks'  : (('PEAKID',), 'PEAKID')
}


### Functions

def download_hdb(url=HDB_URL, zip_path=HDB_ZIP_PATH, force_download=False):
    if isinstance(zip_path, str):
        zip_path = Path(zip_path)

    logger = logging.getLogger(__name__)

    if zip_path.exists() and not force_download:
        log_msg = 'file \'{}\' already exists - skipping download'
        logger.info(log_msg.format(zip_path.name))
    else:
        log_msg = 'downloading Himalayan Database to file \'{}\''
        logger.info(log_msg.format(zip_path.name))
        download_file(url, zip_path)


def extract_hdb(zip_path=HDB_ZIP_PATH, export_dir=HDB_RAW_DIR):
    """Extract files from Himalayan Database zip file"""
    logger = logging.getLogger(__name__)

    if not export_dir.exists():
        export_dir.mkdir()

    export_files = {'{}.{}'.format(file_name, suffix)
                    for file_name in HDB_TABLES for suffix in ['dbf', 'fpt']}

    with zipfile.ZipFile(zip_path, 'r') as zip_file:
        for zipped_file in zip_file.infolist():
            file_name = PurePath(zipped_file.filename).name.lower()

            if file_name in export_files:
                log_msg = 'extracting \'{}\' from zip archive \'{}\''
                logger.info(log_msg.format(file_name, zip_path.name))

                file_path = (export_dir / file_name).resolve()
                with open(file_path, 'wb') as file:
                    file.write(zip_file.read(zipped_file))


def convert_hdb(raw_dir=HDB_RAW_DIR, converted_dir=HDB_INTERIM_DIR):
    """Description"""
    logger = logging.getLogger(__name__)

    if not converted_dir.exists():
        converted_dir.mkdir()

    for table_name in HDB_TABLES:
        dbf_path = (raw_dir / '{}.dbf'.format(table_name)).resolve()

        dbf_table = DBF(dbf_path, ignore_missing_memofile=False)

        log_msg = 'scanning \'{}\' for duplicate records'
        logger.info(log_msg.format(dbf_path.name))

        # Expedition and member tables have a duplicate climb record with
        # expid 'KANG10101' from 1910 and 2010 - this code will record all the
        # duplicate records so we know what to include in the second scan

        key_cols, cmp_col = HDB_DUPLICATES.get(table_name, (None, None))
        get_key = lambda rec: tuple(rec[col] for col in key_cols)

        whitelist = {}
        for record in tqdm(iterable=dbf_table, unit='records', leave=False):
            key = get_key(record)
            value = record[cmp_col]

            if key in whitelist:
                if value > whitelist[key]:
                    whitelist[key] = value
            else:
                whitelist[key] = value

        txt_path = (converted_dir / '{}.txt'.format(table_name)).resolve()

        log_msg = 'converting \'{}\' to delimited text file \'{}\''
        logger.info(log_msg.format(dbf_path.name, txt_path.name))

        # Export the records that match our whitelist (must match the
        # disambiguation column specified in the HDB_DUPLICATES global)

        row_count = 0
        blacklist = []
        with open(txt_path, 'w', newline='', encoding='utf-8') as dsv_file:
            dsv_writer = csv.writer(dsv_file, delimiter='|')

            dsv_writer.writerow(dbf_table.field_names)

            for record in tqdm(dbf_table, unit='rows', leave=False):
                key = get_key(record)
                value = record[cmp_col]

                if value == whitelist[key]:
                    row = [int(field) if type(field) is bool else field
                           for field in list(record.values())]
                    dsv_writer.writerow(row)
                    row_count += 1
                else:
                    blacklist.append((key, value))

        log_msg = 'wrote {}/{} records to \'{}\''
        logger.info(log_msg.format(row_count, len(dbf_table), txt_path.name))

        # Print the warnings last because it interferes with tqdm's output
        log_msg = 'ignored record with key={} and {}=\'{}\''
        for key, value in blacklist:
            logger.warning(log_msg.format(key, cmp_col, value))


def main():
    download_hdb()
    extract_hdb()
    convert_hdb()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    main()

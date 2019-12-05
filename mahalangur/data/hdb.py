# -*- coding: utf-8 -*-
import logging
import zipfile
from .. import DATASETS_DIR, LOG_FORMAT
from .utils import download_file
from pathlib import Path, PurePath


### Globals

HDB_ZIP_PATH = (DATASETS_DIR / 'raw' / 'himalayan-database.zip').resolve()
HDB_DIR = (DATASETS_DIR / 'raw' / 'himalayan-database').resolve()
HDB_URL = ('https://www.himalayandatabase.com/downloads/' +
           'Himalayan%20Database.zip')
HDB_TABLES = ['members', 'exped', 'peaks', 'refer']


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


def extract_hdb(zip_path=HDB_ZIP_PATH, export_dir=HDB_DIR):
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


def main():
    download_hdb()
    extract_hdb()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    main()

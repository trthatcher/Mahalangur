# -*- coding: utf-8 -*-
import csv
import logging
import sqlite3
import socket
from pathlib import Path
from time    import sleep
from tqdm    import tqdm
from urllib.request import urlopen
from urllib.error   import URLError


### Functions - Web

def retry_urlopen(url, timeout, retries, delay,
                  logger=logging.getLogger(__name__)):
    '''Open the URL url, which can be either a string or a Request object and
    retry if an exception is raised up to retries times.

    Parameters
    ----------
    url : string

    timeout : the optional timeout parameter specifies a timeout in seconds 
        for blocking operations like the connection attempt (if not specified,
        the global default timeout setting will be used). This actually only
        works for HTTP, HTTPS and FTP connections

    retries : number of retries before an error is raised. The maximum number
        of attempts is retries + 1

    delay : the delay in seconds between subsequent retries

    Returns
    -------
    '''
    if retries < 0:
        msg = 'retries={} must a non-negative integer'.format(retries)
        raise ValueError(msg)

    logger.info('opening URL')

    for i in range(retries + 1):
        try:
            response = urlopen(url, timeout=timeout)
            return response
        except (URLError, socket.timeout) as err:
            if i == 0 and retries == 0:
                raise err
            elif i == 0:
                logger.warning(err)
            else:
                logger.warning('Retry {} got \'{}\''.format(i, err))

            if i != retries:
                sleep(delay)

    raise URLError('urlopen failed after {} retries'.format(retries))


def download_file(url, file_path, chunk_size=1024*1024, timeout=5.0,
                  retries=5, delay=0.5, logger=logging.getLogger(__name__)):
    '''Download a file from the specified url to the specified file_path.
    
    Parameters
    ----------
    url : string

    file_path : string or path object giving path to destination file

    timeout : the optional timeout parameter specifies a timeout in seconds 
        for blocking operations like the connection attempt (if not specified,
        the global default timeout setting will be used). This actually only 
        works for HTTP, HTTPS and FTP connections

    retries : number of retries before an error is raised. The maximum number
        of attempts is retries + 1

    delay : the delay in seconds between subsequent retries
    '''
    if isinstance(file_path, str):
        file_path = Path(file_path)

    response = retry_urlopen(url, timeout=timeout, retries=retries,
                             delay=delay, logger=logger)

    info = response.info()
    size = int(info['Content-Length']) if 'Content-Length' in info else None

    logger.info('downloading to file \'{}\''.format(file_path.name))

    prog_bar = tqdm(total=size, unit='B', unit_scale=True, leave=False)

    with open(file_path, 'wb') as file:
        for chunk in iter(lambda: response.read(chunk_size), b''):
            prog_bar.update(len(chunk))
            file.write(chunk)

    prog_bar.close()

    return file_path


### Functions - SQLite

def noneif(value, case):
    return None if value == case else value


def batched(reader, batch_size=100):
    batch = []

    for i, row in enumerate(reader, 1):
        batch.append(row)
        if i % batch_size == 0:
            yield batch
            batch = []

    yield batch


def import_delimited(db_conn, table_name, dsv_path,
                     logger=logging.getLogger(__name__)):
    if isinstance(dsv_path, str):
        dsv_path = Path(dsv_path)

    #logger = logging.getLogger(__name__)

    log_msg = 'importing records from delimited file \'{}\' to table \'{}\'...'
    logger.info(log_msg.format(dsv_path.name, table_name))

    with open(dsv_path, 'r', newline='', encoding='utf-8') as dsv_file:
        dsv_reader = csv.reader(dsv_file, delimiter='|')

        headers = next(dsv_reader)

        headers_sql = ','.join(headers)
        values_sql = ','.join(['?'] * len(headers))
        sql = 'INSERT INTO {}({}) VALUES ({})'.format(table_name, headers_sql,
                                                        values_sql)

        db_csr = db_conn.cursor()
        prog_bar = tqdm(unit='rows', leave=False)

        n = 0
        for batch in batched(dsv_reader, batch_size=50):
            processed_batch = [[noneif(v,'') for v in row] for row in batch]
            n_batch = len(processed_batch)

            db_csr.executemany(sql, processed_batch)

            prog_bar.update(n_batch)
            n += n_batch

        prog_bar.close()
        db_csr.close()

    db_conn.commit()

    logger.info('wrote {} records to table \'{}\''.format(n, table_name))

    return (table_name, n)


# Functions - delimited files

def write_delimited(records, dsv_path, logger=logging.getLogger(__name__)):
    if isinstance(dsv_path, str):
        dsv_path = Path(dsv_path)

    log_msg = 'writing to delimited text file \'{}\'...'
    logger.info(log_msg.format(dsv_path.name))

    n = len(records) - 1

    with open(dsv_path, 'w', newline='', encoding='utf-8') as dsv_file:
        dsv_writer = csv.writer(dsv_file, delimiter='|',
                                quoting=csv.QUOTE_MINIMAL)

        for record in tqdm(records, unit='rows', leave=False):
            processed_record = [noneif(field,'') for field in record]
            dsv_writer.writerow(processed_record)

    log_msg = 'wrote {} records to delimited text file \'{}\''
    logger.info(log_msg.format(n, dsv_path.name))

    return (dsv_path, n)
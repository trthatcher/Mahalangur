# -*- coding: utf-8 -*-
import logging
from time import sleep
from tqdm import tqdm
from urllib.request import urlopen
from urllib.error import URLError


### Functions

def retry_urlopen(url, timeout, retries, delay):
    '''Open the URL url, which can be either a string or a Request object and
    retry if an exception is raised up to retries times.

    Parameters
    ----------
    url : string or Request object

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

    logger = logging.getLogger(__name__)

    for i in range(retries + 1):
        try:
            response = urlopen(url, timeout=timeout)
            return response
        except URLError as err:
            if i == 0 and retries == 0:
                raise err
            elif i == 0:
                logger.warning(err)
            else:
                logger.warning('Retry {} got {}'.format(i, err))

            if i != retries:
                sleep(delay)

    raise URLError('urlopen failed after {} retries'.format(retries))


def download_file(url, file_path, chunk_size=1024*1024, timeout=5.0,
                  retries=5, delay=0.5):
    '''Download a file from the specified url to the specified file_path.
    
    Parameters
    ----------
    url : string or Request object

    file_path : string or path object giving path to destination file

    timeout : the optional timeout parameter specifies a timeout in seconds 
        for blocking operations like the connection attempt (if not specified,
        the global default timeout setting will be used). This actually only 
        works for HTTP, HTTPS and FTP connections

    retries : number of retries before an error is raised. The maximum number
        of attempts is retries + 1

    delay : the delay in seconds between subsequent retries
    '''
    response = retry_urlopen(url, timeout=timeout, retries=retries,
                             delay=delay)

    info = response.info()
    size = int(info['Content-Length']) if 'Content-Length' in info else None

    with open(file_path, 'wb') as file:
        prog_bar = tqdm(total=size, unit='B', unit_scale=True, leave=False)

        for chunk in iter(lambda: response.read(chunk_size), b''):
            prog_bar.update(len(chunk))
            file.write(chunk)

        prog_bar.close()

    return file_path

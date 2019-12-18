# -*- coding: utf-8 -*-
'''mahalangur'''

import importlib.resources as res
from pathlib import Path

with res.path('mahalangur', '') as package_path:
    PACKAGE_DIR = Path(package_path)

with res.path('mahalangur', 'assets') as assets_path:
    ASSETS_DIR = Path(assets_path)

with res.path('mahalangur', 'datasets') as datasets_path:
    DATASETS_DIR = Path(datasets_path)

STATIC_DIR    = (DATASETS_DIR / 'static'       ).resolve()
PROCESSED_DIR = (DATASETS_DIR / 'processed'    ).resolve()
RAW_DIR       = (DATASETS_DIR / 'raw'          ).resolve()
DATABASE_PATH = (DATASETS_DIR / 'mahalangur.db').resolve()

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

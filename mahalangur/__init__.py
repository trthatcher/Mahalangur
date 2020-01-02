# -*- coding: utf-8 -*-
'''mahalangur'''

import os
from pathlib import Path

if 'MAHALANGUR_HOME' in os.environ:
    HOME_DIR = Path(os.environ.get('MAHALANGUR_HOME')).resolve()
else:
    HOME_DIR = (Path.home() / '.mahalangur').resolve()

if not HOME_DIR.exists():
    HOME_DIR.mkdir()

DATA_DIR = (HOME_DIR / 'data').resolve()
if not DATA_DIR.exists:
    DATA_DIR.mkdir()

MODEL_DIR = (HOME_DIR / 'model').resolve()
if not MODEL_DIR.exists:
    MODEL_DIR.mkdir()

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'




import importlib.resources as res

with res.path('mahalangur', '') as package_path:
    PACKAGE_DIR = Path(package_path)

with res.path('mahalangur', 'assets') as assets_path:
    ASSETS_DIR = Path(assets_path)

with res.path('mahalangur', 'datasets') as datasets_path:
    DATASETS_DIR = Path(datasets_path)

DATABASE_PATH = DATASETS_DIR / 'mahalangur.db'

with res.path('mahalangur', 'web') as web_path:
    WEB_DIR = Path(web_path)


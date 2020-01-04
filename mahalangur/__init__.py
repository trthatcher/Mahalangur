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

DATABASE_PATH = DATA_DIR / 'mahalangur.db'

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# -*- coding: utf-8 -*-
'''mahalangur'''

import importlib.resources as res
from pathlib import PurePath

with res.path('mahalangur', 'datasets') as datasets_path:
    DATASETS_DIR = PurePath(datasets_path)

with res.path('mahalangur', 'assets') as assets_path:
    ASSETS_DIR = PurePath(assets_path)

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

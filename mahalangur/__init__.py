# -*- coding: utf-8 -*-
'''mahalangur'''

import importlib.resources as res
from pathlib import Path

with res.path('mahalangur', '') as package_path:
    PACKAGE_DIR = Path(package_path)

with res.path('mahalangur', 'datasets') as datasets_path:
    DATASETS_DIR = Path(datasets_path)

with res.path('mahalangur', 'assets') as assets_path:
    ASSETS_DIR = Path(assets_path)

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

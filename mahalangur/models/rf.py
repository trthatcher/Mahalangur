# -*- coding: utf-8 -*-
import logging
import numpy as np
import pandas as pd
import pickle
import sklearn
import sqlite3
import joblib
from .. import ASSETS_DIR, LOG_FORMAT, DATABASE_PATH
from hashlib import sha256
from sklearn.ensemble import RandomForestClassifier


### Globals
HIMALS = [
    'ANNAPURNA',
    'BARUN',
    'CHANGLA',
    'DAMODAR',
    'DHAULAGIRI',
    'DOLPO',
    'GANESH',
    'GAUTAM',
    'GORAKH',
    'JANAK',
    'JUGAL',
    'KANJIROBA',
    'KANTI',
    #'KHUMBU',  Ignore, default
    'KUMBHAKARNA',
    'KUTANG',
    'LANGTANG',
    'MAKALU',
    'MANASLU',
    'MUSTANG',
    'NALAKANKAR',
    'NORTHERN',
    'PALCHUNGHAMGA',
    'PAMARI',
    'PERI',
    'ROLWALING',
    'SAIPAL',
    'SERANG',
    'SINGALILA',
    'UMBAK',
    'WESTERNSIKKIM',
    'YOKAPAHAR'
]

SEASONS = [
    'Spring',
    'Summer',
    #'Autumn',  Ignore, default
    'Winter'
]


### Logic

def partition(id_values, n_partitions=10):
    sha_string = sha256('-'.join(id_values).encode('utf-8')).hexdigest()
    return (int(sha_string, 16) % n_partitions) + 1


def get_data():
    sql = 'SELECT * FROM model_base WHERE expedition_year >= 1970;'

    conn = sqlite3.connect(DATABASE_PATH)
    df = pd.read_sql(sql, conn, index_col=['expedition_id', 'member_id'])
    conn.close()

    return df


def data_matrix(df):
    columns = [
        df['height'],
        df['expedition_year'],
        pd.Series(df['commercial_route'] == 'Y', name='commercial_route',
                  dtype=np.uint8),
        df['total_members'],
        df['total_hired'],
        df['age'],
        pd.Series(df['sex'] == 'F', name='female', dtype=np.uint8),
        pd.Series(df['o2_used'] == 'Y', name='o2_used', dtype=np.uint8)
    ]

    for himal in HIMALS:
        columns.append(pd.Series(df['himal'] == himal,
                                 name='himal_' + himal.lower(),
                                 dtype=np.uint8))

    for season in SEASONS:
        columns.append(pd.Series(df['season'] == season,
                                 name=season.lower(),
                                 dtype=np.uint8))

    X = pd.concat(columns, axis=1)
    y = df['successful_summit']

    return (X, y)


def train_model(X, y):
    rf_model = RandomForestClassifier(criterion='gini', max_depth=5,
                                      n_estimators=90, oob_score=True)

    rf_model.fit(X, y)

    return rf_model


def main():
    logger = logging.getLogger(__name__)

    logger.info('retrieving data')
    df = get_data()

    logger.info('creating data matrix')
    X, y = data_matrix(df)

    logger.info('training random forest model')
    rf_model = train_model(X, y)

    logger.info('out-of-bag score: {}'.format(rf_model.oob_score_))

    model_path = (ASSETS_DIR / 'model-rf_v1.0.pickle').resolve()
    logger.info('saving model to file \'{}\''.format(model_path.name))
    joblib.dump(rf_model, model_path)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    main()

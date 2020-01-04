# -*- coding: utf-8 -*-
import logging
import numpy as np
import pandas as pd
import pickle
import sklearn
import sqlite3
import joblib
from . import DATABASE_PATH, LOG_FORMAT, MODEL_DIR
from .feat import utils
from hashlib import sha256
from sklearn.ensemble import RandomForestClassifier


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


def train_model(X, y):
    rf_model = RandomForestClassifier(
        criterion='gini',
        max_depth=5,
        n_estimators=90,
        oob_score=True
    )

    rf_model.fit(X, y)

    return rf_model


def build_model():
    logger = logging.getLogger('mahalangur.rfmodel')

    logger.info('retrieving data')
    data_df = get_data()

    logger.info('creating data matrix')
    X = utils.data_matrix(data_df)
    y = (data_df['successful_summit'] == 'Y').astype(dtype=np.uint8)

    logger.info('training random forest model')
    rf_model = train_model(X, y)

    logger.info('out-of-bag score: {}'.format(rf_model.oob_score_))

    model_path = (MODEL_DIR / 'model-rf_v1.0.pickle').resolve()
    if not model_path.parent.exists():
        model_path.parent.mkdir(parents=True)

    logger.info('saving model to file \'{}\''.format(model_path.name))
    joblib.dump(rf_model, model_path)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    build_model()

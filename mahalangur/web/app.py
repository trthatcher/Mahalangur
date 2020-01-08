import csv
import importlib.resources as res
import joblib
import json
import pandas as pd
from ..feat import utils
from .. import LOG_FORMAT
from flask import Flask, render_template, request, jsonify

### Globals

app = Flask(__name__)

MODEL         = None
PEAK_GEOSJON  = None
HIMAL_GEOJSON = None
PEAK_DF       = None

DEFAULTS = {
    'expedition_year' : (int, 2020    ),
    'season'          : (str, 'Autumn'),
    'commercial_route': (str, 'N'     ),
    'total_members'   : (int, 5       ),
    'total_hired'     : (int, 3       ),
    'age'             : (int, 37      ),
    'sex'             : (str, 'M'     ),
    'o2_used'         : (str, 'N'     )
}


### Asset Loading

def load_assets():
    global MODEL
    global PEAK_GEOJSON
    global HIMAL_GEOJSON
    global PEAK_DF

    with res.path('mahalangur.assets', 'rfmodel.pickle') as model_path:
        MODEL = joblib.load(model_path)

    meta_dir = 'mahalangur.data.metadata'
    with res.path(meta_dir, 'web_peak.geojson') as peak_path:
        with open(peak_path, 'r') as geojson_file:
            PEAK_GEOJSON = json.load(geojson_file)

    with res.path(meta_dir, 'web_himal.geojson') as himal_path:
        with open(himal_path, 'r') as geojson_file:
            HIMAL_GEOJSON = json.load(geojson_file)

    peak_ids  = []
    peak_data = []
    for peak in PEAK_GEOJSON['features']:
        peak_ids.append(peak['id'])

        data = {
            'height': peak['properties']['height'],
            'himal' : peak['properties']['himal']
        }
        for col, value in DEFAULTS.items():
            data[col] = value[1]

        peak_data.append(data)
    
    PEAK_DF = utils.data_matrix(pd.DataFrame(peak_data, index=peak_ids))


### Prediction

def expedition_data(expedition_form):
    exped_data = {}
    for col, (dtype, value) in DEFAULTS.items():
        exped_data[col] = dtype(expedition_form.get(col, value))

    return exped_data


def predict(expedition_data):
    exped_df = PEAK_DF.copy(deep=True)
    utils.update_data_matrix(exped_df, data=expedition_data,
                             ignore_cols={'himal', 'height'})

    success = MODEL.predict_proba(exped_df)[:, 1]
    peaks = exped_df.index

    return {peak: round(100*prob, 2) for peak, prob in zip(peaks, success)}


### Web Application

@app.route('/')
@app.route('/index')
def index():
    return render_template('map.j2', peak_geojson=PEAK_GEOJSON,
                           himal_geojson=HIMAL_GEOJSON)

@app.route('/api/v1/', methods=['POST'])
def api_v1():
    try:
        exped_form = request.get_json()
        exped_data = expedition_data(exped_form)
        return jsonify({
            'status': 'success',
            'summit_probabilities': predict(exped_data)
        })
    except:
        return jsonify({'status': 'failure'})


if __name__ == "__main__":
    load_assets()
    app.run(debug=True)

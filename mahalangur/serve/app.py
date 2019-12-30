import csv
import joblib
import json
from .. import ASSETS_DIR, DATASETS_DIR
from .. import utils
from flask import Flask, render_template, request

### Globals

app = Flask(__name__)

MODEL  = None
PEAKS  = None
HIMALS = None

PEAKS_PATH  = (DATASETS_DIR / 'processed' / 'feat_peak.txt').resolve()
HIMALS_PATH = (DATASETS_DIR / 'static' / 'osm_himal.geojson').resolve()
MODEL_PATH  = (ASSETS_DIR / 'model-rf_v1.0.pickle').resolve()


### Logic

def load_assets():
    global MODEL
    global PEAKS
    global HIMALS

    himals = set()

    PEAKS = {} 
    with utils.open_dsv(PEAKS_PATH, 'r') as peaks_dsv:
        dsv_reader = utils.dsv_dictreader(peaks_dsv)

        for peak in dsv_reader:
            if peak.get('longitude') is None:
                continue

            if peak.get('himal') is not None:
                himals.add(peak.get('himal'))

            PEAKS[peak['peak_id']] = {k: peak[k] for k in [
                'peak_name',
                'height',
                'longitude',
                'latitude',
                'himal'
            ]}

    HIMALS = {}
    with open(HIMALS_PATH, 'r') as geojson_file:
        himal_geojson = json.load(geojson_file)

    for feature in himal_geojson['features']:
        feature_id = feature['id']
        if feature_id not in himals:
            continue

        HIMALS[feature_id] = feature

    MODEL = joblib.load(MODEL_PATH)


def predict(commercial=False, members=10, hired=5, female=False,
            o2_used=False):
    return True


### Web Application

@app.route('/')
@app.route('/index')
def index():
    return render_template('visualization.j2')

@app.route('/api/v1', methods=['POST', 'GET'])
def api_v1():
    return True
    #if request.method == 'POST':
    #    features = request.form.to_dict()
    #
    #else:
    #    return redirect('/', code=302)


if __name__ == "__main__":
    load_assets()
    app.run()

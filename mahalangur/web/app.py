import csv
import joblib
import json
import pandas as pd
from .. import ASSETS_DIR, DATASETS_DIR, WEB_DIR
from .. import utils
from flask import Flask, render_template, request, jsonify

### Globals

app = Flask(__name__)

MODEL    = None
PEAK_DF  = None

PEAKS_PATH  = (WEB_DIR / 'static' / 'peak.geojson' ).resolve()
MODEL_PATH  = (ASSETS_DIR / 'model-rf_v1.0.pickle').resolve()

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


### Asset Loading

def load_assets():
    global MODEL
    global PEAK_DF

    peak_headers = [
        'height',
        'expedition_year',
        'commercial_route',
        'total_members',
        'total_hired',
        'age',
        'female',
        'o2_used'
    ]
    peak_headers.extend(['himal_' + himal.lower() for himal in HIMALS])
    peak_headers.extend(['season_' + season.lower() for season in SEASONS])

    with open(PEAKS_PATH, 'r') as geojson_file:
        peaks_geojson = json.load(geojson_file)

    peak_index   = []
    peak_list    = []
    for peak in peaks_geojson['features']:
        peak_index.append(peak['id'])

        peak_data = [
            peak['properties']['height'],
            2020,  # Expedition Year
            0,     # Commercial Route
            1,     # Total Members
            0,     # Total Hired
            30,    # Age
            0,     # Female
            0,     # O2 Used
        ]

        peak_himal = peak['properties']['himal']

        peak_data.extend(
            [1 if peak_himal == himal else 0 for himal in HIMALS]
        )

        peak_data.extend([0 for season in SEASONS])

        peak_list.append(peak_data)

    PEAK_DF = pd.DataFrame(
        data=peak_list,
        index=peak_index,
        columns=peak_headers
    )
    MODEL = joblib.load(MODEL_PATH)


### Prediction

def predict(expedition_year=2019, season='Autumn', commercial_route=False,
            total_members=10, total_hired=5, age=37, female=False,
            o2_used=False):
    PEAK_DF['expedition_year' ] = expedition_year
    PEAK_DF['commercial_route'] = 1 if commercial_route else 0
    PEAK_DF['total_members'   ] = total_members
    PEAK_DF['total_hired'     ] = total_hired
    PEAK_DF['age'             ] = age
    PEAK_DF['female'          ] = 1 if female else 0
    PEAK_DF['o2_used'         ] = 1 if o2_used else 0
    PEAK_DF['season_summer'   ] = 1 if season == 'Summer' else 0
    PEAK_DF['season_spring'   ] = 1 if season == 'Spring' else 0
    PEAK_DF['season_winter'   ] = 1 if season == 'Winter' else 0

    success = MODEL.predict_proba(PEAK_DF)[:, 1]
    peaks = PEAK_DF.index

    return {peak: round(100*prob, 2) for peak, prob in zip(peaks, success)}


### Web Application

@app.route('/')
@app.route('/index')
def index():
    return render_template('map.j2')

@app.route('/api/v1', methods=['POST'])
def api_v1():
    features = request.get_json()

    expedition_year  = int(features['expedition_year'])
    season           = features['season']
    commercial_route = features['commercial_route'] == 'Y'
    total_members    = int(features['total_members'])
    total_hired      = int(features['total_hired'])
    age              = int(features['age'])
    female           = features['sex'] == 'F'
    o2_used          = features['o2_used'] == 'Y'

    success_probs = predict(
        expedition_year  = expedition_year ,
        season           = season,
        commercial_route = commercial_route,
        total_members    = total_members,
        total_hired      = total_hired,
        age              = age,
        female           = female,
        o2_used          = o2_used
    )

    return jsonify(success_probs)


if __name__ == "__main__":
    load_assets()
    app.run(debug=True)

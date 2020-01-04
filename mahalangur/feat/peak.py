# -*- coding: utf-8 -*-
import copy
import importlib.resources as res
import json
import logging
import pandas as pd
import re
from .. import DATA_DIR, LOG_FORMAT, METADATA_DIR
from ..data import utils
from Levenshtein import jaro_winkler
from shapely.geometry import Point, Polygon
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer


### Globals
HDB_DSV_PATH       = (DATA_DIR / 'processed' / 'hdb_peak.txt').resolve()
PEAK_GEOJSON_PATH  = (METADATA_DIR / 'web_peak.geojson').resolve()
PEAK_DSV_PATH      = (METADATA_DIR / 'ref_peak.txt'    ).resolve()

SUBSTITUTIONS = {
    r'(?<=\W)KANG'       : 'KHANG',
    r'(?<=\W)SE(?=\W|\Z)': 'SOUTH EAST',
    r'(?<=\W)NE(?=\W|\Z)': 'NORTH EAST'
}

TITLES = {'NORTH', 'WEST', 'EAST', 'SOUTH', 'CENTRAL', 'MIDDLE', 'I', 'II',
          'III', 'IV', 'V', 'VI', 'VII'}

IGNORE_WORDS = {'HIMAL', 'PEAK'}

# 0.7 override
MOTCA_OVERRIDE = {
    'RANI': '119', # Himalchuli Northeast = Himalchuli East?
    'LNKE': '233', # Lunchhung = Lungchhung
    'KABD': '143', # Kabru Dome = Kabru
    'URKM': '400', # Slight spelling variation of Urkenmang
    'KGUR': '154', # Naurgaon Pk is Kang Guru
}

HIMAL_OVERRIDE = {
    'GAMA': 'DHAULAGIRI',
    'MATA': 'KANJIROBA',
    'GHYM': 'KANJIROBA',
    'JUNC': 'DHAULAGIRI',
    'KTSU': 'KANJIROBA',
    'MACH': 'ANNAPURNA',
    'MING': 'KHUMBU',
    'OMBK': 'JANAK',
    'POIN': 'KHUMBU',
    'SNOW': 'DHAULAGIRI',
    'SRKU': 'KANJIROBA',
    'GAUG': 'DAMODAR',
    'PK41': 'KHUMBU',
    'DZAS': 'KHUMBU',
    'MYAG': 'DHAULAGIRI',
    'ROMA': 'SAIPAL',
    'TAWA': 'DAMODAR',
    'GOJN': 'KANTI',
    'LUNW': 'ROLWALING',
    'LUN2': 'ROLWALING',
    'DHEC': 'DAMODAR',
    'GDNG': 'CHANGLA',
    'PAWR': 'PERI',
    'NGOR': 'PERI',
    'FUTI': 'DAMODAR',
    'SANK': 'DAMODAR'
}


### Logic

def read_peaks(dsv_path, id_col):
    '''Read in the peak list as a {peak_id: peak} dictionary'''
    with utils.open_dsv(dsv_path, 'r') as dsv_file:
        reader = utils.dsv_dictreader(dsv_file)
        peaks = {row[id_col]: row for row in reader}

    return peaks


def read_himals(geojson_path):
    '''Read the himal polygons into a {himal_id: himal_poly} dictionary'''
    with open(geojson_path, 'r') as geojson_file:
        features = json.load(geojson_file)['features']
    
    black_list = set()
    for feature in features:
        parent = feature.get('properties', {}).get('parent')
        if parent is not None:
            black_list.add(parent)

    himals = {}
    for feature in features:
        himal_id = feature['id']
        if himal_id not in black_list:
            himals[himal_id] = Polygon(feature['geometry']['coordinates'][0])

    return himals


def process_name(name):
    '''Preprocesses a name by subsituting non-alphanumeric characters with
    whitespace, substituting several patterns and filtering some common words
    from the string'''
    name = re.sub(r'\W+', ' ', name).upper()

    for pattern, sub in SUBSTITUTIONS.items():
        name = re.sub(pattern, sub, name)

    name_parts = []
    titles = []
    for name_part in name.split():
        if name_part in IGNORE_WORDS:
            continue
        elif name_part.isdigit() or name_part in TITLES:
            titles.append(name_part)
        else:
            name_parts.append(name_part)
    
    return (''.join(name_parts), ' '.join(titles)) 


def name_dataframe(peaks, name1, name2):
    '''Create a dataframe of peak names'''
    names = []
    for peak_id, peak in peaks.items():
        name_string = peak.get(name1,'') + ',' + peak.get(name2,'')

        peak_names = [nm.strip() for nm in name_string.split(',')
                      if nm.strip() != '']

        for i, peak_name in enumerate(peak_names):
            name, title = process_name(peak_name)
            names.append([peak_id, i+1, peak_name, name, title])

    headers = [
        'id',
        'seq',
        'full_name',
        'name',
        'title'
    ]

    return pd.DataFrame(data=names, columns=headers)


def jaccard(list1, list2):
    set1 = set(list1)
    set2 = set(list2)
    if not set1 and not set2:
        return 0.0
    else:
        return len(set1.intersection(set2)) / len(set1.union(set2))


def choose_match(match_df):
    match = match_df.sort_values(by='similarity', ascending=False).iloc[0]

    main_df = match_df[match_df['seq'] == 1]
    if not main_df.empty:
        alt_match = main_df.sort_values(by='similarity',
                                        ascending=False).iloc[0]
        if alt_match['similarity'] > 0.85:
            match = alt_match

    return pd.Series({
        'name'      : match['full_name'],
        'match_id'  : match['match_id'],
        'match_name': match['match_full_name'],
        'similarity': match['similarity']
    })


def match_names(name1_df, name2_df, reduce=True):
    name_vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2,3))
    name_vectorizer.fit(list(name1_df['name']))

    name1_X = name_vectorizer.transform(name1_df['name'])
    name2_X = name_vectorizer.transform(name2_df['name'])

    similarity_matrix = cosine_similarity(name1_X, name2_X)

    matches = []
    for i, j in zip(*similarity_matrix.nonzero()):
            # Similarity between names
            name_sim_cs = similarity_matrix[i, j]

            if name_sim_cs < 0.5: continue

            match1 = name1_df.iloc[i]
            match2 = name2_df.iloc[j]

            name1 = match1['name']
            name2 = match2['name']

            name_sim_jw = jaro_winkler(name1, name2, 0.1)

            similarity = (name_sim_cs + name_sim_jw)/2

            # Similarity between titles

            title1 = match1['title']
            title2 = match2['title']

            titles = title1.split()
            title_sim = jaccard(titles, title2.split())
            if title1 != '':
                title_weight = min(len(titles), 2)*0.1

                similarity = (title_weight*title_sim +
                              (1-title_weight)*similarity)

            matches.append([
                match1['id'],
                match1['seq'],
                match1['full_name'],
                name1,
                title1,
                match2['id'],
                match2['seq'],
                match2['full_name'],
                name2,
                title2,
                name_sim_cs,
                name_sim_jw,
                title_sim,
                similarity
            ])

    headers = [
        'id',
        'seq',
        'full_name',
        'name',
        'title',
        'match_id',
        'match_seq',
        'match_full_name',
        'match_name',
        'match_title',
        'name_similarity_cs',
        'name_similarity_jw',
        'title_similarity',
        'similarity'
    ]

    match_df = pd.DataFrame(data=matches, columns=headers)

    if reduce:
        return match_df.groupby(['id']).apply(choose_match)
    else:
        return match_df


def name_link(name1_df, name2_df, override={}, threshold=0.6):
    matches_df = match_names(name1_df, name2_df, reduce=True)

    matches = copy.deepcopy(override)
    for id, match in matches_df.iterrows():
        if id not in matches and match['similarity'] >= threshold:
            matches[id] = match['match_id']

    return matches


def peak_list(hdb_peaks, himals, himal_override, osm_peaks, motca_peaks):
    peaks = [[
        'peak_id',
        'peak_name',
        'alt_names',
        'height',
        'location',
        'approximate_coordinates',
        'longitude',
        'latitude',
        'dms_longitude',
        'dms_latitude',
        'coordinate_notes',
        'himal'
    ]]
    for peak_id, hdb_peak in hdb_peaks.items():
        osm_peak   =   osm_peaks.get(peak_id, {})
        motca_peak = motca_peaks.get(peak_id, {})

        name = hdb_peak['pkname']

        location = hdb_peak['location']

        # Get all variations of the name
        alt_names = set()
        for peak, cols in [(osm_peak  , ['peak_name', 'alt_names']),
                           (motca_peak, ['peak_name', 'alt_names']),
                           (hdb_peak  , ['pkname2'               ])]:
            for col in [c for c in cols if c in peak]:
                for alt_name in peak[col].split(','):
                    alt_name = alt_name.strip()
                    if alt_name != '':
                        alt_names.add(alt_name)

        if name in alt_names:
            alt_names.remove(name)

        alt_names = ','.join(alt_names) if alt_names else None

        # Get latitude and longitude coordinates
        is_approx = None
        lon       = None
        lat       = None
        dms_lon   = None
        dms_lat   = None
        coord_notes = None

        for peak, approx, cite in [(osm_peak  , False, 'OSM'  ),
                                   (motca_peak, True , 'MoTCA')]:
            if peak.get('longitude') is not None:
                peak_lon = peak.get('dms_longitude')
                peak_lat = peak.get('dms_latitude')

                if lon is None:
                    is_approx = 'Y' if approx else 'N'
                    lon       = float(peak.get('longitude'))
                    lat       = float(peak.get('latitude' ))
                    dms_lon   = peak_lon
                    dms_lat   = peak_lat

                coord_note = '{}: ({}, {})'.format(cite, peak_lat, peak_lon)
                if coord_notes is None:
                    coord_notes = coord_note
                else:
                    coord_notes += '\n' + coord_note

        # Get himal details
        himal = himal_override.get(peak_id)
        if himal is None and lon is not None and lat is not None:
            peak_coord = Point(lon, lat)
            for himal_id, himal_poly in himals.items():
                if himal_poly.contains(peak_coord):
                    himal = himal_id
                    break

        # Peak elevation
        height = hdb_peak.get('heightm')

        # Append the records
        peaks.append([
            peak_id,
            name,
            alt_names,
            height,
            location,
            is_approx,
            lon,
            lat,
            dms_lon,
            dms_lat,
            coord_notes,
            himal
        ])

    return peaks


def peak_geojson(peak_list):
    property_names = [
        ('name'     ,  1),
        ('alt_names',  2),
        ('height'   ,  3),
        ('himal'    , 11)
    ]

    features = []
    for peak in peak_list:
        properties = {name: peak[col] for name, col in property_names
                      if peak[col] is not None}

        features.append({
            'id': peak[0],
            'type': 'Feature',
            'properties': properties,
            'geometry': {
                'type': 'Point',
                'coordinates': (peak[6], peak[7])
            }
        })

    return {
        'type': 'FeatureCollection',
        'features': features
    }


def peak_metadata():
    logger = logging.getLogger('mahalangur.features.peaks')

    # Read peaks as {id: record} dictionary
    hdb_peaks = read_peaks(HDB_DSV_PATH, id_col='peakid')

    with res.path('mahalangur.data.metadata', 'osm_peak.txt') as osm_dsv_path:
        osm_peaks = read_peaks(osm_dsv_path, id_col='peak_id')

    with res.path('mahalangur.data.metadata', 'mot_peak.txt') as mot_dsv_path:
        mot_peaks = read_peaks(mot_dsv_path, id_col='peak_number')

    # Read himal geometry
    with res.path('mahalangur.web.static', 'web_himal.geojson') as himal_path:
        himals = read_himals(himal_path)

    # Create a dataframe of names with header [id, seq, full_name, name, title]
    hdb_name_df = name_dataframe(hdb_peaks,
                                 name1='pkname',
                                 name2='pkname2')
    osm_name_df = name_dataframe(osm_peaks,
                                 name1='peak_name',
                                 name2='alt_names')
    mot_name_df = name_dataframe(mot_peaks,
                                 name1='peak_name',
                                 name2='alt_names')

    # Link the various datasets by choosing best match
    logger.info('matching HDB peaks to OSM peaks...')
    osm_link = name_link(hdb_name_df,
                         osm_name_df,
                         threshold=0.9)
    osm_peaks_linked = {hdb_pk: osm_peaks[osm_pk]
                        for hdb_pk, osm_pk in osm_link.items()}

    logger.info('matching HDB peaks to MoTCA peaks...')
    motca_link = name_link(hdb_name_df,
                           mot_name_df,
                           override=MOTCA_OVERRIDE,
                           threshold=0.7)
    motca_peaks_linked = {hdb_pk: mot_peaks[motca_pk]
                          for hdb_pk, motca_pk in motca_link.items()}

    # Combine into a table
    peaks = peak_list(hdb_peaks, himals, HIMAL_OVERRIDE, osm_peaks_linked,
                      motca_peaks_linked)

    if not PEAK_DSV_PATH.parent.exists():
        PEAK_DSV_PATH.parent.mkdir(parents=True)

    utils.write_delimited(peaks, PEAK_DSV_PATH)

    # Generate the geojson file
    peaks_geo = peak_geojson(peaks[1:])

    if not PEAK_GEOJSON_PATH.parent.exists():
        PEAK_GEOJSON_PATH.parent.mkdir(parents=True)

    logger.info('writing geojson \'{}\''.format(PEAK_GEOJSON_PATH.name))
    with open(PEAK_GEOJSON_PATH, 'w') as geojson_file:
        json.dump(peaks_geo, geojson_file)

    return (PEAK_DSV_PATH, PEAK_GEOJSON_PATH)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    peak_metadata()

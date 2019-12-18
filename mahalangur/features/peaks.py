# -*- coding: utf-8 -*-
import copy
import csv
import json
import logging
import numpy as np
import pandas as pd
import re
from .. import utils, LOG_FORMAT, DATASETS_DIR
from pathlib import Path
from shapely.geometry import Point, Polygon
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer



### Globals

MOTCA_PATH = (DATASETS_DIR / 'static' / 'motca_peak.txt').resolve() 
HDB_PATH   = (DATASETS_DIR / 'processed' / 'hdb_peaks.txt').resolve() 
OSM_PATH   = (DATASETS_DIR / 'static' / 'osm_peak.txt').resolve() 
PEAK_PATH  = (DATASETS_DIR / 'processed' / 'feat_peak.txt').resolve()
HIMAL_PATH = (DATASETS_DIR / 'static' / 'osm_himal.geojson').resolve()

COMMON_WORDS = {'NORTH', 'WEST', 'EAST', 'SOUTH', 'CENTRAL', 'HIMAL', 'I',
                'II', 'III', 'IV', 'V', 'VI', 'VII', 'PEAK'}

SUBSTITUTIONS = {
    r'\wKANG': ' KHANG',
    r'\wSE'  : ' SOUTH EAST',
    r'\wNE'  : ' NORTH EAST'
}

# 0.7 override
MOTCA_OVERRIDE = {
    'RANI': '119', # Himalchuli Northeast = Himalchuli East?
    'LNKE': '233', # Lunchhung = Lungchhung
    'KABD': '143', # Kabru Dome = Kabru
    'URKM': '400', # Slight spelling variation of Urkenmang
    'KGUR': '154', # Naurgaon Pk is Kang Guru
}


### Logic

def name_ngrams(name, n=2):
    name = re.sub(r'\W+', ' ', name).upper()

    for pattern, sub in SUBSTITUTIONS.items():
        name = re.sub(pattern, sub, name)

    words = []
    name_parts = []
    for name_part in name.split():
        if name_part in COMMON_WORDS or name_part.isdigit():
            words.append(name_part)
        else:
            name_parts.append(name_part)

    name = ''.join(name_parts)
    
    ngrams = zip(*[name[i:] for i in range(n)])
    words.extend([''.join(ngram) for ngram in ngrams])

    return words


def read_peaks(dsv_path, id_col):
    with utils.open_dsv(dsv_path, 'r') as dsv_file:
        reader = utils.dsv_dictreader(dsv_file)
        peaks = {row[id_col]: row for row in reader}

    return peaks


def read_himals(geojson_path):
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


def peak_names(peak_dict, name1, name2):
    peaks = []
    for peak_id, peak in peak_dict.items():
        name_string = peak.get(name1,'') + ',' + peak.get(name2,'')

        names = [nm.strip() for nm in name_string.split(',')
                 if nm.strip() != '']

        for i, name in enumerate(names):
            peaks.append([peak_id, i+1, name])

    return pd.DataFrame(data=peaks, columns=['id', 'seq', 'name'])


def name_matches(base_df, match_df):
    corpus = list(set(base_df['name']) | set(match_df['name']))

    vectorizer = TfidfVectorizer(min_df=1, analyzer=name_ngrams)
    vectorizer.fit(corpus)

    base_X = vectorizer.transform(base_df['name'])
    match_X = vectorizer.transform(match_df['name'])

    similarity_matrix = cosine_similarity(base_X, match_X)

    matches = []
    for i, j in zip(*similarity_matrix.nonzero()):
        similarity = similarity_matrix[i, j]

        if similarity < 0.5: continue

        base  = base_df.iloc[i]
        match = match_df.iloc[j]

        matches.append([
            base['id'],
            base['seq'],
            base['name'],
            match['id'],
            match['seq'],
            match['name'],
            similarity
        ])

    return pd.DataFrame(data=matches, columns=['id', 'seq', 'name',
                        'match_id', 'match_seq', 'match_name', 'similarity'])


def choose_match(match_df):
    match = match_df.sort_values(by='similarity', ascending=False).iloc[0]

    main_df = match_df[match_df['seq'] == 1]
    if not main_df.empty:
        alt_match = main_df.sort_values(by='similarity',
                                        ascending=False).iloc[0]
        if alt_match['similarity'] > 0.85:
            match = alt_match

    return pd.Series({
        'name'      : match['name'],
        'match_id'  : match['match_id'],
        'match_name': match['match_name'],
        'similarity': match['similarity']
    })


def name_link(base_df, match_df, override={}, threshold=0.6):
    matches_df = name_matches(base_df, match_df)
    matches_df = matches_df.groupby(['id']).apply(choose_match)

    matches = copy.deepcopy(override)
    for id, match in matches_df.iterrows():
        if id not in matches and match['similarity'] >= threshold:
            matches[id] = match['match_id']

    return matches


def peak_list(hdb_peaks, himals, osm_peaks, motca_peaks):
    peaks = [[
        'peak_id',
        'peak_name',
        'alt_names',
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

        name = hdb_peak['PKNAME']

        location = hdb_peak['LOCATION']

        # Get all variations of the name
        alt_names = set()
        for peak, cols in [(osm_peak  , ['peak_name', 'alt_names']),
                           (motca_peak, ['peak_name', 'alt_names']),
                           (hdb_peak  , ['PKNAME2'               ])]:
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

        for peak, approx, cite in [(osm_peak  , False, 'OSM'),
                                   (motca_peak, True,  'MoTCA')]:
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
        himal = None
        if lon is not None and lat is not None:
            peak_coord = Point(lon, lat)
            for himal_id, himal_poly in himals.items():
                if himal_poly.contains(peak_coord):
                    himal = himal_id
                    break

        # Append the records
        peaks.append([
            peak_id,
            name,
            alt_names,
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


def main():
    logger = logging.getLogger(__name__)

    # Read peaks as {id: record} dictionary
    hdb_peaks   = read_peaks(HDB_PATH  , id_col='PEAKID'     )
    osm_peaks   = read_peaks(OSM_PATH  , id_col='peak_id'    )
    motca_peaks = read_peaks(MOTCA_PATH, id_col='peak_number')

    # Read himal geometry
    himals = read_himals(HIMAL_PATH)

    # Create a dataframe of names with header [id, seq, name]
    hdb_names_df   = peak_names(hdb_peaks,
                                name1='PKNAME',
                                name2='PKNAME2')
    osm_names_df   = peak_names(osm_peaks,
                                name1='peak_name',
                                name2='alt_names')
    motca_names_df = peak_names(motca_peaks,
                                name1='peak_name',
                                name2='alt_names')

    # Link the various datasets by choosing best match
    logger.info('matching HDB peaks to OSM peaks...')
    osm_link   = name_link(hdb_names_df,
                           osm_names_df,
                           threshold=0.9)
    logger.info('matching HDB peaks to MoTCA peaks...')
    motca_link = name_link(hdb_names_df,
                           motca_names_df,
                           override=MOTCA_OVERRIDE,
                           threshold=0.7)

    osm_peaks_linked   = {hdb_pk: osm_peaks[osm_pk]
                          for hdb_pk, osm_pk in osm_link.items()}

    motca_peaks_linked = {hdb_pk: motca_peaks[motca_pk]
                          for hdb_pk, motca_pk in motca_link.items()}

    # Combine into a table
    peaks = peak_list(hdb_peaks, himals, osm_peaks_linked, motca_peaks_linked)

    utils.write_delimited(peaks, PEAK_PATH)

    return PEAK_PATH


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    main()

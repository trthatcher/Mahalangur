# -*- coding: utf-8 -*-
import copy
import csv
import logging
import numpy as np
import pandas as pd
import re
from .. import utils, LOG_FORMAT, DATASETS_DIR
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

#import sys
# Add the ptdraft folder path to the sys.path list
#sys.path.append('/home/tim/Projects/Mahalangur/mahalangur/')
#import utils


### Globals

MOTCA_PATH = (DATASETS_DIR / 'static' / 'motca_peak.txt').resolve() 
HDB_PATH   = (DATASETS_DIR / 'processed' / 'hdb_peaks.txt').resolve() 
OSM_PATH   = (DATASETS_DIR / 'static' / 'osm_peak.txt').resolve() 
PEAK_PATH  = (DATASETS_DIR / 'processed' / 'feat_peak.txt').resolve()

IGNORE_NAMES = {
    'TENT PEAK',     # Two alt names 
    'TWINS',         # HDB contains two peaks that have this name
    'JUNCTION PEAK', # Two HDB alt names, one primary
    'FLUTED PEAK',   # Two HDB alt names
    'DOMO',          # One primary HDB, one alt
    'SHARPHU IV',    # HDB primary and alt - not sure why this exists
    'NUPCHU',        # HDB primary and alt
    'PYRAMID PEAK',
    'GANESH VI',
    'KANGTEGA',
    'CHAMAR'
}

COMMON_WORDS = {'NORTH', 'WEST', 'EAST', 'SOUTH', 'CENTRAL', 'HIMAL', 'I',
                'II', 'III', 'IV', 'V', 'VI', 'VII', 'PEAK'} #, 'TSE', 'RE'}

SUBSTITUTIONS = {
    r'\wKANG': ' KHANG',
    r'\wSE'  : ' SOUTH EAST',
    r'\wNE'  : ' NORTH EAST',
    r'\wTSE' : ' TSE'
}

OVERRIDE = {
    'KGUR': 154,   # Naurgaon Pk is Kang Guru
    'URKM': 400,   # Slight spelling variation of Urkenmang
    'PIMU': None,  # Errors
    'GHYM': None,
    'CTSE': None,
    'TONG': None
}


### Logic

def name_ngrams(name, n=3):
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


def peak_names(peak_dict, name1, name2):
    peaks = []
    for peak_id, peak in peak_dict.items():
        name_string = peak.get(name1,'') + ',' + peak.get(name2,'')

        names = [nm.strip() for nm in name_string.split(',')
                 if nm.strip() != '']

        for i, name in enumerate(names):
            peaks.append([peak_id, i+1, name])

    return pd.DataFrame(data=peaks, columns=['id', 'seq', 'name'])


def name_matches(base_df, match_df, threshold=0.4):
    corpus = list(set(base_df['name']) | set(match_df['name']))

    vectorizer = TfidfVectorizer(min_df=1, analyzer=name_ngrams)
    vectorizer.fit(corpus)

    base_X = vectorizer.transform(base_df['name'])
    match_X = vectorizer.transform(match_df['name'])

    similarity_matrix = cosine_similarity(base_X, match_X)

    matches = []
    for i, j in zip(*similarity_matrix.nonzero()):
        similarity = similarity_matrix[i, j]
        if similarity > threshold:
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

    #main_df = match_df[match_df['seq'] == 1]
    #if not main_df.empty:
    #    alt = main_df.sort_values(by='similarity', ascending=False).iloc[0]
    #    if alt['similarity'] > 0.9:
    #        match = alt

    return pd.Series({
        'name'      : match['name'],
        'match_id'  : match['match_id'],
        'match_name': match['match_name'],
        'similarity': match['similarity']
    })


def get_name_link(base_df, match_df, override={}, threshold=0.6):
    matches_df = name_matches(base_df, match_df)
    matches_df = matches_df.groupby(['id']).apply(choose_match)

    matches = copy.deepcopy(override)
    for id, match in matches_df.iterrows():
        if id not in override and match['similarity'] >= threshold:
            matches[id] = match['match_id']

    return matches


def make_linkage(hdb_peaks, osm_peaks, motca_peaks, osm_override={},
                 motca_override={}):
    hdb_names = peak_names(hdb_peaks, name1='PKNAME', name2='PKNAME2')
    osm_names = peak_names(osm_peaks, name1='peak_name', name2='alt_names')
    motca_names = peak_names(motca_peaks, name1='peak_name', name2='alt_names')

    osm_link = get_name_link(hdb_names, osm_names, override=osm_override)
    motca_link = get_name_link(hdb_names, motca_names, override=motca_override)

    peaks = [['peak_id', 'peak_name', 'alt_names', 'approximate_coordinates',
              'longitude', 'latitude', 'dms_longitude', 'dms_latitude']]
    for peak_id, hdb_peak in hdb_peaks.items():
        osm_peak   =   osm_peaks.get(  osm_link.get(peak_id, None), {})
        motca_peak = motca_peaks.get(motca_link.get(peak_id, None), {})

        name = hdb_peak['PKNAME']

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

        for peak, approx in [(osm_peak, False), (motca_peak, True)]:
            if peak.get('longitude', None) is not None:
                if lon is None:
                    is_approx = 'Y' if approx else 'N'
                    lon       = peak.get('longitude')
                    lat       = peak.get('latitude')
                    dms_lon   = peak.get('dms_longitude')
                    dms_lat   = peak.get('dms_latitude')

        peaks.append([
            peak_id,
            name,
            alt_names,
            is_approx,
            lon,
            lat,
            dms_lon,
            dms_lat
        ])

    return peaks


def main():
    hdb_peaks   = read_peaks(HDB_PATH, id_col='PEAKID')
    osm_peaks   = read_peaks(OSM_PATH, id_col='peak_id')
    motca_peaks = read_peaks(MOTCA_PATH, id_col='peak_number')

    hdb_names = peak_names(hdb_peaks, name1='PKNAME', name2='PKNAME2')
    osm_names = peak_names(osm_peaks, name1='peak_name', name2='alt_names')
    motca_names = peak_names(motca_peaks, name1='peak_name', name2='alt_names')

    matches_df = name_matches(hdb_names, osm_names)
    matches_df = matches_df.groupby(['id']).apply(choose_match)
    matches_df.to_csv((DATASETS_DIR / 'processed' / 'osm_matches.txt').resolve(), sep='|')

    matches_df = name_matches(hdb_names, motca_names)
    matches_df = matches_df.groupby(['id']).apply(choose_match)
    matches_df.to_csv((DATASETS_DIR / 'processed' / 'motca_matches.txt').resolve(), sep='|')


    links = make_linkage(hdb_peaks, osm_peaks, motca_peaks)

    utils.write_delimited(links, PEAK_PATH)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    main()



#def make_peak_table(hdb_peaks, osm_link, osm_peaks, motca_link, motca_peaks):
#    peaks = []
#
#    for peak_id, hdb_data in hdb_peaks.items():




#MOTCA_PATH = Path('/home/tim/Projects/Mahalangur/mahalangur/datasets/static/motca_peak.txt')
#HDB_PATH = Path('/home/tim/Projects/Mahalangur/mahalangur/datasets/processed/hdb_peaks.txt')
#OSM_PATH = Path('/home/tim/Projects/Mahalangur/mahalangur/datasets/static/osm_peak.txt')
#
#hdb_peaks = read_peaks(HDB_PATH, id_col='PEAKID')
#osm_peaks = read_peaks(OSM_PATH, id_col='peak_id')
#
#
#
#
#
#hdb_df = read_peaks(HDB_PATH, id_col=0, name_col=1, alt_names_col=2)
#motca_df = read_peaks(MOTCA_PATH, id_col=0, name_col=1, alt_names_col=2)
#osm_df = read_peaks(OSM_PATH, id_col=0, name_col=1, alt_names_col=2)
#
#sim_df = match_peak_names(hdb_df, motca_df)
#sim_df.to_csv('/home/tim/Projects/Mahalangur/mahalangur/datasets/processed/similarities.csv', sep='|', index=False)
#
#match_df = sim_df.groupby(['id']).apply(choose_match)
#match_df.to_csv('/home/tim/Projects/Mahalangur/mahalangur/datasets/processed/matches.csv', sep='|', index=True)
#
#sim_df = match_peak_names(hdb_df, osm_df)
#match_df = sim_df.groupby(['id']).apply(choose_match)
#
#match_df.to_csv('/home/tim/Projects/Mahalangur/mahalangur/datasets/processed/osm_matches.csv', sep='|', index=True)


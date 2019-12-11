# -*- coding: utf-8 -*-
import csv
import json
import logging
import math
import re
from ..      import DATASETS_DIR, LOG_FORMAT
from .utils  import download_file
from shapely import ops, geometry as geom
from urllib  import parse

#import matplotlib
#matplotlib.use('Agg')
#import matplotlib.pyplot as plt


### Globals
OSM_RAW_DIR = (DATASETS_DIR / 'raw' / 'osm').resolve()
HIMAL_JSON_PATH = (OSM_RAW_DIR / 'himal.json').resolve()

OSM_PROCESSED_DIR  = (DATASETS_DIR / 'processed').resolve()
HIMAL_DSV_PATH     = (OSM_PROCESSED_DIR / 'osm_himal.txt').resolve()
HIMAL_GEOJSON_PATH = (OSM_PROCESSED_DIR / 'osm_himal.geojson').resolve()

OVERPASS_URL = 'https://overpass-api.de/api/interpreter?data={}'
HIMAL_QUERY = '''
[out:json];
rel
["region:type"="mountain_area"]
["name"~"subsection|himal",i]
["name"!~"jugal.*and.*langtang",i]
(27,81,30,89);
out body;
>;
out skel qt;
'''.replace('\n', '')




### Logic

def dms_string(value, is_lon):
    '''Convert a longitude or latitude value into a DMS formatted string''' 
    if value is None:
        return None

    neg = True if value < 0 else False
    value = int(round(abs(value) * 10**7, 0))

    deg, r1 = divmod(value, 10**7)
    min, r2 = divmod(60*r1, 10**7)
    sec = (r2*60)/(10**7)

    direction = (('N','S') if is_lon else ('E','W'))[neg]

    dms = '{:d}° {:02d}′ {:08.5f}″{}'

    return dms.format(deg, min, sec, direction)


def query_himals(himal_path=HIMAL_JSON_PATH):
    '''Retrieve himal geometry from overpass API. The target file path can be
    specified to override the default location'''
    logger = logging.getLogger(__name__)

    url = OVERPASS_URL.format(parse.quote(HIMAL_QUERY))

    if not OSM_RAW_DIR.exists():
        OSM_RAW_DIR.mkdir()

    logger.info('querying Overpass API for himal geometry')

    return download_file(url, HIMAL_JSON_PATH, timeout=45, retries=2)


def get_himal_polygons(himal_path=HIMAL_JSON_PATH, tol=0.005):
    '''Read the overpass JSON query and return a list of dictionaries
    where each dictionary corresponds to a himal with a name field, optional
    alt_name field and a polygon field'''
    with open(himal_path, 'r') as json_file:
        himal_json = json.load(json_file)

    elements = himal_json['elements']

    # Scan through the returned JSON and create a dictionary of nodes
    nodes = {e['id']: (e['lon'], e['lat']) for e in elements
             if e['type'] == 'node'}

    # Scan through the JSON and construct a LineString for each way. If a
    # tolerance has been specified, it will be used to simplify the ways
    ways = {}
    for way in elements:
        if way['type'] != 'way': continue

        segment = geom.LineString(nodes[n] for n in way['nodes'])

        ways[way['id']] = segment if tol is None else segment.simplify(tol)

    # Create the himal polygons by scanning the JSON for any relations and
    # constructing them from the specified ways (LineStrings)
    himals = []
    for rel in elements:
        if rel['type'] != 'relation': continue

        himal = {tag: rel['tags'][tag] for tag in ('name','alt_name') 
                 if tag in rel['tags']}

        segments = []
        for way in rel['members']:
            if way['type'] == 'way' and way['role'] == 'outer':
                segments.append(ways[way['ref']])

        polygons = list(ops.polygonize(segments))

        if len(polygons) != 1:
            err_msg = ('ways for relation \'{}\' ({}) do not form a single '
                       'valid polygon')
            raise ValueError(err_msg.format(rel['name'], rel['id']))

        himal['polygon'] = polygons[0]

        himals.append(himal)

    return himals


def make_himal_geojson(himals):
    '''Construct a geojson using the list of himals returned by the function
    get_himal_polygons'''
    features = []
    polygons = {}
    for himal in himals:
        id = re.sub('([^A-Z]+)|HIMAL|SUBSECTION', '', himal['name'].upper())

        properties = {tag: himal[tag] for tag in ('name', 'alt_name')
                      if tag in himal}

        himal_poly = himal['polygon']

        polygons[id] = himal_poly

        c_lon, c_lat = himal_poly.centroid.coords[0]
        properties['centroid'] = (round(c_lon,7), round(c_lat,7))

        feature = {
            'id'        : id,
            'type'      : 'Feature',
            'bbox'      : himal_poly.bounds,
            'properties': properties,
            'geometry'  : geom.mapping(himal_poly)
        }

        features.append(feature)

    # Find parent regions
    for himal in features:
        himal_id = himal['id']
        himal_poly = polygons[himal['id']]

        for parent_id, parent_poly in polygons.items():
            if himal_id == parent_id or parent_poly.area <= himal_poly.area:
                continue

            overlap = himal_poly.intersection(parent_poly)
            if overlap.area/himal_poly.area > 0.99:
                himal['properties']['parent'] = parent_id

    # Final geojson format
    polygon_list = list(polygons.values())
    himalayas_poly = geom.Polygon(ops.unary_union(polygon_list).exterior)

    return {
        'type'    : 'FeatureCollection',
        'bbox'    : himalayas_poly.bounds,
        'features': sorted(features, key=lambda feat: feat['id'])
    }


def write_himal_files(himal_geojson, geojson_path=HIMAL_GEOJSON_PATH,
                      dsv_path=HIMAL_DSV_PATH):
    
    logger = logging.getLogger(__name__)

    logger.info('writing himal geojson \'{}\''.format(geojson_path.name))
    with open(geojson_path, 'w') as geojson_file:
        json.dump(himal_geojson, geojson_file)

    logger.info('writing himal text file \'{}\''.format(dsv_path.name))
    with open(dsv_path, 'w', newline='', encoding='utf-8') as dsv_file:
        dsv_writer = csv.writer(dsv_file, delimiter='|')
        dsv_writer.writerow([
            'himal_id',
            'himal_name',
            'himal_alt_name',
            'parent_himal_id',
            'longitude',
            'dms_longitude',
            'latitude',
            'dms_latitude'
        ])

        for feature in himal_geojson['features']:
            properties = feature.get('properties', {})

            lon, lat = properties.get('centroid', (None, None))

            row = [
                feature['id'],
                properties['name'],
                properties.get('alt_name', None),
                properties.get('parent'  , None),
                lon,
                dms_string(lon, is_lon=True),
                lat,
                dms_string(lat, is_lon=False)
            ]

            dsv_writer.writerow(row)

    return (geojson_path, dsv_path)

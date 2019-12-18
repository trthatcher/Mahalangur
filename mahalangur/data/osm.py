# -*- coding: utf-8 -*-
import csv
import json
import logging
import math
import re
from ..      import utils, DATASETS_DIR, LOG_FORMAT
from pathlib import Path
from shapely import ops, geometry as geom
from urllib  import parse


### Globals
OSM_RAW_DIR    = (DATASETS_DIR / 'raw' / 'osm').resolve()
OSM_STATIC_DIR = (DATASETS_DIR / 'static').resolve()

HIMAL_JSON_PATH    = (OSM_RAW_DIR    / 'himal.json'       ).resolve()
HIMAL_DSV_PATH     = (OSM_STATIC_DIR / 'osm_himal.txt'    ).resolve()
HIMAL_GEOJSON_PATH = (OSM_STATIC_DIR / 'osm_himal.geojson').resolve()
PEAK_JSON_PATH     = (OSM_RAW_DIR    / 'peak.json'        ).resolve()
PEAK_DSV_PATH      = (OSM_STATIC_DIR / 'osm_peak.txt'     ).resolve()

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

PEAK_QUERY = '''
[out:json];
node
["natural"="peak"]
["name"]
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

    direction = (('E','W') if is_lon else ('N','S'))[neg]

    dms = '{:d}° {:02d}′ {:08.5f}″ {}'

    return dms.format(deg, min, sec, direction)


def query_overpass(query, file_path, force_download=False,
                   logger=logging.getLogger(__name__)):
    '''Retrieve geometry from overpass API'''
    if isinstance(file_path, str):
        file_path = Path(file_path)

    file_dir = file_path.parents[0]
    if not file_dir.exists():
        file_dir.mkdir(parents=True)

    if file_path.exists() and not force_download:
        log_msg = 'file \'{}\' already exists - skipping Overpass query'
        logger.info(log_msg.format(file_path.name))
        return file_path
    else:
        logger.info('querying Overpass API')
        url = OVERPASS_URL.format(parse.quote(query))
        return utils.download_file(url, file_path, timeout=45, retries=2)


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


def get_himal_geojson(himals):
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

        lon, lat = himal_poly.centroid.coords[0]
        properties['centroid'] = (round(lon,7), round(lat,7))

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


def get_himal_list(himal_geojson):
    himal_list = [[
            'himal_id',
            'himal_name',
            'alt_names',
            'longitude',
            'latitude',
            'dms_longitude',
            'dms_latitude',
            'parent_himal_id'
    ]]

    for feature in himal_geojson['features']:
        properties = feature.get('properties', {})

        lon, lat = properties.get('centroid', (None, None))

        record = [
            feature['id'],
            properties['name'],
            properties.get('alt_name', None),
            lon,
            lat,
            dms_string(lon, is_lon=True),
            dms_string(lat, is_lon=False),
            properties.get('parent'  , None)
        ]

        himal_list.append(record)

    return himal_list


def get_peak_list(json_path=PEAK_JSON_PATH):
    with open(json_path, 'r') as json_file:
        peaks = json.load(json_file)

    records = [[
        'peak_id',
        'peak_name',
        'alt_names',
        'longitude',
        'latitude',
        'dms_longitude',
        'dms_latitude'
    ]]
    for node in peaks['elements']:
        tags = node['tags']
        name_tags = [tag for tag in tags if tag in {'name', 'int_name',
                     'name:en', 'alt_name', 'alt_name:en'}]

        # Use a dictionary to maintain order
        names = {}
        for tag in name_tags:
            for name in re.split(r'[,;\(\)]', tags[tag]):
                if not name.isascii() or name == '' or name.isdigit():
                    continue

                numerals = {num.title(): num for num in {'I', 'II', 'III',
                            'IV', 'V', 'VI', 'VII'}}

                name = ' '.join([numerals.get(word, word)
                                 for word in name.strip().title().split()])

                names[name] = True

        names = list(names.keys())

        if not names:
            continue

        name = names.pop(0)
        names = set(names)

        lon = node['lon']
        lat = node['lat']

        records.append([
            node['id'],
            name,
            ','.join(names),
            lon,
            lat,
            dms_string(lon, is_lon=True),
            dms_string(lat, is_lon=False)
        ])

    return records


def main():
    logger = logging.getLogger('mahalangur.data.osm')

    # Create Himal metadata
    query_overpass(HIMAL_QUERY, HIMAL_JSON_PATH, force_download=False,
                   logger=logger)
    himal_polys = get_himal_polygons(himal_path=HIMAL_JSON_PATH, tol=0.005)

    himal_geojson = get_himal_geojson(himal_polys)

    logger.info('writing geojson \'{}\''.format(HIMAL_GEOJSON_PATH.name))
    with open(HIMAL_GEOJSON_PATH, 'w') as geojson_file:
        json.dump(himal_geojson, geojson_file)

    himal_list = get_himal_list(himal_geojson)
    utils.write_delimited(himal_list, dsv_path=HIMAL_DSV_PATH)

    # Create peak metadata
    query_overpass(PEAK_QUERY, PEAK_JSON_PATH, force_download=False,
                   logger=logger)

    peak_list = get_peak_list(json_path=PEAK_JSON_PATH)

    utils.write_delimited(peak_list, dsv_path=PEAK_DSV_PATH)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    main()

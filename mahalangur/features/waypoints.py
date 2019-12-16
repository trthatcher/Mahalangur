# -*- coding: utf-8 -*-
import re
import sqlite3
from pathlib import Path
#from .. import DATABASE_PATH
DATABASE_PATH = Path('/home/tim/Projects/Mahalangur/mahalangur/datasets/mahalangur.db')

### Globals
SQL = '''
SELECT
EXPID
,"YEAR"
,BCDATE
,SMTDATE
,TERMDATE
,HIGHPOINT
,CAMPSITES
FROM hdb_expedition;
'''.strip('\n')


### Logic

def query_camps(db_path=DATABASE_PATH):
    db_conn = sqlite3.connect(db_path)
    db_conn.row_factory = sqlite3.Row

    db_csr = db_conn.cursor()
    db_csr.execute(SQL)

    records = db_csr.fetchall()

    db_conn.close()

    return {record['EXPID']: dict(record) for record in records}


#def parse_camp(camp_string):


def parse_expedition(expeds):
    year = int(expeds['YEAR'])

    camp_strings = re.findall(r'[^,(]+(?:\(.+?\))?', expeds['CAMPSITES'])

    waypoints = []
    for i, camp_string in enumerate(camp_strings):
        camp_name = re.findall(r'^[^(]+', camp_string)
        if not camp_name:
            camp_name = None
        else:
            camp_name = camp_name[0]

        arrival_date = None
        elevation    = None

        camp_details = re.findall(r'\(.+?\)', camp_string)
        if camp_details:
            camp_details = camp_details[0][1:-1].split(',')

            if len(camp_details) == 2:
                camp_date, camp_ele = camp_details

                if re.fullmatch(r'\d\d/\d\d', camp_date):
                    date_str = '{yyyy:04d}-{mm:02d}-{dd:02d}'
                    arrival_date = date_str.format(yyyy=year,
                                                   mm=int(camp_date[-2:]),
                                                   dd=int(camp_date[:2]))

                if re.fullmatch(r'\d{4}m', camp_ele):
                    elevation = int(camp_ele[:-1])

        waypoint = {
            'waypoint_seq': i,
            'waypoint_name': camp_name,
            'arrival_date': arrival_date,
            'elevation': elevation,
            'waypoint_note': camp_string
        }

        waypoints.append(waypoint)

    return waypoints



test = query_camps()

exp1 = test['YARA18301']
parse_expedition(exp1)



exp1['CAMPSITES']
re.findall(r'[^,(]+(?:\(.+?\))?', exp1['CAMPSITES'])

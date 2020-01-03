import pandas as pd
import numpy as np

### Globals

DATA_SCHEMA = {
    'expedition_year': {'column': 'expedition_year'},
    'season': {
        'type': 'categorical',
        'column': 'season',
        'values': [
            'Spring',
            'Summer',
            #'Autumn',  Ignore, default
            'Winter'
        ]
    },
    'commercial_route': {
        'type': 'indicator',
        'column': 'expedition_year',
        'value': 'Y'
    },
    'total_members': {'column': 'total_members'},
    'total_hired': {'column': 'total_hired'},
    'age': {'column': 'age'},
    'female': {
        'type': 'indicator',
        'column': 'sex',
        'value': 'F'
    },
    'o2_used': {
        'type': 'indicator',
        'column': 'o2_used',
        'value': 'Y'
    },
    'height': {'column': 'height'},
    'himal': {
        'type': 'categorical',
        'column': 'himal',
        'values': [
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
    }
}


### Logic

def set_df_column(model_df, data_df, column, column_schema):
    source_column = column_schema['column']
    column_type   = column_schema.get('type', 'continuous')

    if column_type == 'continuous':
        column_value = data_df[source_column]

        model_df[column] = column_value.astype(dtype=np.float, copy=True)

    elif column_type == 'indicator':
        indicator_value = column_schema['value']
        column_value = data_df[source_column] == indicator_value

        model_df[column] = column_value.astype(dtype=np.uint8, copy=True)

    elif column_type == 'categorical':
        category_values = column_schema['values']
        for category_value in category_values:
            subcolumn = column + '_' + category_value.lower()
            subcolumn_value = data_df[source_column] == category_value

            model_df[subcolumn] = subcolumn_value.astype(dtype=np.uint8,
                                                         copy=True)
    
    return model_df


def set_dict_column(model_df, data, column, column_schema):
    source_column = column_schema['column']
    column_type   = column_schema.get('type', 'continuous')

    if column_type == 'continuous':
        model_df[column] = np.float(data[source_column])

    elif column_type == 'indicator':
        indicator_value = column_schema['value']
        model_df[column] = np.uint8(data[source_column] == indicator_value)

    elif column_type == 'categorical':
        category_values = column_schema['values']
        for category_value in category_values:
            subcolumn = column + '_' + category_value.lower()
            subcolumn_value = data[source_column] == category_value
            model_df[subcolumn] = np.uint8(subcolumn_value)
    
    return model_df


def update_data_matrix(model_df, data, schema=DATA_SCHEMA, ignore_cols=set()):
    set_column = set_dict_column if type(data) == dict else set_df_column

    for column, column_schema in schema.items():
        set_column(model_df, data, column, column_schema)

    return model_df


def make_data_matrix(data_df, schema=DATA_SCHEMA, ignore_cols=set()):
    model_df = data_df.index.copy(deep=True)
    return update_data_matrix(model_df, data_df)


test_df = pd.DataFrame(
    data = {
        'num': [1, 2, 3, 4, 5],
        'alpha': ['A', 'B', 'C', 'D', 'E']
    },
    index = ['X1', 'X2', 'X3', 'X4', 'X5']
)




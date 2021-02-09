# Import data from dst, wrangle it and load it into postgres

# Packages
import pandas as pd
import matplotlib.pyplot as plt
import requests
from pyjstat import pyjstat

# Import data from dst

## URL til tabel med folketal
url_dst = 'https://api.statbank.dk/v1/data'

## Parameters for the API
query_indkomst_kommuner = {
   "table": "IFOR32",
   "format": "JSONSTAT",
   "valuePresentation": "CodeAndValue",
   "variables": [
      {
         "code": "DECILGEN",
         "values": [
            "*"
         ]
      },
      {
         "code": "KOMMUNEDK",
         "values": [
            "*"
         ]
      },
      {
         "code": "Tid",
         "values": [
            "(-n+10)"
         ]
      }
   ]
}

query_pct_lavindkomst_kommuner = {
   "table": "IFOR12P",
   "format": "JSONSTAT",
   "valuePresentation": "CodeAndValue",
   "variables": [
      {
         "code": "KOMMUNEDK",
         "values": [
            "*"
         ]
      },
      {
         "code": "INDKN",
         "values": [
            "50"
         ]
      },
      {
         "code": "Tid",
         "values": [
            "(-n+10)"
         ]
      }
   ]
}

query_n_lavindkomst_kommuner = {
   "table": "IFOR12A",
   "format": "JSONSTAT",
   "valuePresentation": "CodeAndValue",
   "variables": [
      {
         "code": "KOMMUNEDK",
         "values": [
            "*"
         ]
      },
      {
         "code": "INDKN",
         "values": [
            "50"
         ]
      },
      {
         "code": "Tid",
         "values": [
            "(-n+10)"
         ]
      }
   ]
}

query_folketal = {
   "table": "FOLK1A",
   "format": "JSONSTAT",
   "valuePresentation": "CodeAndValue",
   "variables": [
      {
         "code": "OMRÅDE",
         "values": [
            "*"
         ]
      },
      {
         "code": "Tid",
         "values": [
            "*K1"
         ]
      },
      {
         "code": "Tid",
         "values": [
            "(-n+10)"
         ]
      }
   ]
}

## Post query
r_indkomst_kommuner = requests.post(url_dst, json = query_indkomst_kommuner)

r_pct_lavindkomst_kommuner = requests.post(url_dst, json = query_pct_lavindkomst_kommuner)

r_n_lavindkomst_kommuner = requests.post(url_dst, json = query_n_lavindkomst_kommuner)

r_folketal = requests.post(url_dst, json = query_folketal)

## Read JSON-stat result
ds_indkomst_kommuner = pyjstat.Dataset.read(r_indkomst_kommuner.text)

ds_pct_lavindkomst_kommuner = pyjstat.Dataset.read(r_pct_lavindkomst_kommuner.text)

ds_n_lavindkomst_kommuner = pyjstat.Dataset.read(r_n_lavindkomst_kommuner.text)

ds_folketal = pyjstat.Dataset.read(r_folketal.text)

## Write to pandas dataframe
df_indkomst_kommuner = ds_indkomst_kommuner.write('dataframe', naming = 'id')

df_pct_lavindkomst_kommuner = ds_pct_lavindkomst_kommuner.write('dataframe', naming = 'id')

df_n_lavindkomst_kommuner = ds_n_lavindkomst_kommuner.write('dataframe', naming = 'id')

df_folketal_tekst = ds_folketal.write('dataframe', naming = 'label')
df_folketal_kode = ds_folketal.write('dataframe', naming = 'id')
df_folketal_tekst['id'] = df_folketal_kode['OMRÅDE']

# Data cleaning and wrangling

kun_kommuner = df_folketal_tekst["område"] != "Hele landet"
regioner = df_folketal_tekst["område"].map(lambda x: x.startswith('Region'))

df_kommuner = (df_folketal_tekst
   .loc[(kun_kommuner) & (~regioner), ["område", "id"]]
   .drop_duplicates()
   .rename(columns = {'område': 'kommune'})
)

df_kommuner_folketal = (df_folketal_tekst
   .loc[(kun_kommuner) & (~regioner), ["tid", "value", "id"]]
   .assign(år = lambda x: x.tid.str.slice(stop = 4),
           kvartal = lambda x: x.tid.str.slice(start = 4))
   .query('kvartal not in ["K2", "K3", "K4"]')
   .loc[:, ["id", "år", "kvartal", "value"]]
   .rename(columns = {'value': 'folketal',
                      'id': 'kommune_id'})
)

df_kommuner_g_indkomst = (df_indkomst_kommuner
   .rename(columns = {'KOMMUNEDK': 'kommune_id',
                      'Tid': 'år',
                      'DECILGEN': 'decil_gruppe',
                      'value': 'g_indkomst'})
   .loc[:, ["kommune_id", "år", "decil_gruppe", "g_indkomst"]]
)

df_kommuner_g_indkomst = (pd.merge(df_kommuner_g_indkomst, df_kommuner, 
        left_on = 'kommune_id', right_on = 'id')
       .loc[:, ["kommune_id", "år", "decil_gruppe", "g_indkomst"]]
)

kommuner_g_lavindkomst = (df_n_lavindkomst_kommuner
   .loc[:, ["KOMMUNEDK", "Tid", "value"]]
   .merge(df_pct_lavindkomst_kommuner, on = ['KOMMUNEDK', 'Tid'])
   .merge(df_kommuner, left_on = 'KOMMUNEDK', right_on = 'id')
   .loc[:, ["id", "Tid", "INDKN", "value_x", "value_y"]]
   .rename(columns = {'id': 'kommune_id',
                      'Tid': 'år',
                      'INDKN': 'lavindkomst_niveau',
                      'value_x': 'n_lavindkomst',
                      'value_y': 'p_lavindkomst'})
)

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
df_folketal_tekst['kommune_id'] = df_folketal_kode['OMRÅDE']

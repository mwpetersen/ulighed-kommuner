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
res_folketal = requests.post(url_dst, json = query_folketal)

## Read JSON-stat result
ds_folketal = pyjstat.Dataset.read(res_folketal.text)

## Write to pandas dataframe
df_folketal = ds_folketal.write('dataframe')



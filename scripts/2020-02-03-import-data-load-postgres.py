# Import data from dst, wrangle it and load it into postgres

# Modules
import pandas as pd
import requests
from pyjstat import pyjstat
import os
from  sqlalchemy import (create_engine, MetaData, Table, Column, String, Integer, 
                         SmallInteger, Float, insert, delete, select, ForeignKey)

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
   .rename(columns = {'område': 'kommune_navn'})
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
   .merge(df_kommuner, left_on = 'KOMMUNEDK', right_on = 'id')
   .rename(columns = {'KOMMUNEDK': 'kommune_id',
                      'Tid': 'år',
                      'DECILGEN': 'decil_gruppe',
                      'value': 'g_indkomst'})
   .loc[:, ["kommune_id", "år", "decil_gruppe", "g_indkomst"]]
)

df_kommuner_g_lavindkomst = (df_n_lavindkomst_kommuner
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

# create tables in the ulighed_kommuner database

engine = create_engine(os.environ['DATABASE_URI'])

connection = engine.connect()

metadata = MetaData()

kommuner = Table('kommuner', metadata,
      Column('id', Integer(), primary_key = True, nullable = False),
      Column('kommune_navn', String(64), nullable = False, unique = True))

kommuner_folketal = Table('kommuner_folketal', metadata,
      Column('kommune_id', Integer(), ForeignKey("kommuner.id"), primary_key = True),
      Column('år', Integer(), primary_key = True),
      Column('kvartal', String(32), nullable = False),
      Column('folketal', Float(), nullable = False))
      
kommuner_g_indkomst = Table('kommuner_g_indkomst', metadata,
      Column('kommune_id', Integer(), ForeignKey("kommuner.id"), primary_key = True),
      Column('år', Integer(), primary_key = True),
      Column('decil_gruppe', String(32), primary_key = True),
      Column('g_indkomst', Float(), nullable = False))

kommuner_g_lavindkomst = Table('kommuner_g_lavindkomst', metadata,
      Column('kommune_id', Integer(), ForeignKey("kommuner.id"), primary_key = True),
      Column('år', Integer(), primary_key = True),
      Column('lavindkomst_niveau', String(32), nullable = False),
      Column('n_lavindkomst', Float(), nullable = False),
      Column('p_lavindkomst', Float(), nullable = False))

metadata.create_all(engine)

# delete all the rows in the tables (if this script has already been run)
delete_kommuner = connection.execute(delete(kommuner))
delete_kommuner_folketal = connection.execute(delete(kommuner_folketal))
delete_kommuner_g_indkomst = connection.execute(delete(kommuner_g_indkomst))
delete_kommuner_g_lavindkomst = connection.execute(delete(kommuner_g_lavindkomst))

# Load data to tables in postgres
df_kommuner.to_sql(name="kommuner", con=connection, if_exists="append", index=False)
df_kommuner_folketal.to_sql(name="kommuner_folketal", con=connection, if_exists="append", index=False)
df_kommuner_g_indkomst.to_sql(name="kommuner_g_indkomst", con=connection, if_exists="append", index=False)
df_kommuner_g_lavindkomst.to_sql(name="kommuner_g_lavindkomst", con=connection, if_exists="append", index=False)

connection.close() 

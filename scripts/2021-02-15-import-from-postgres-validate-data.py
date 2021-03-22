# Import data from postgres, perform data validation and EDA, and create visualizations

# Modules
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
from sqlalchemy import (create_engine, MetaData, Table, select)
import pandera as pa

# Import data from postgres

## create connection to postgres and create metadata object
engine = create_engine(os.environ['DATABASE_URI'])

connection = engine.connect()

metadata = MetaData()

## create sqlalchemy table objects
kommuner = Table('kommuner', metadata, autoload = True, autoload_with = engine)

kommuner_folketal = Table('kommuner_folketal', metadata, autoload = True, autoload_with = engine)

kommuner_g_indkomst = Table('kommuner_g_indkomst', metadata, autoload = True, autoload_with = engine)

kommuner_g_lavindkomst = Table('kommuner_g_lavindkomst', metadata, autoload = True, autoload_with = engine)

## fetch data from postgres

def fetch_data(table_name):
  fetch_table = connection.execute(select([table_name])).fetchall()
  df = pd.DataFrame(fetch_table)
  df.columns = fetch_table[0].keys()
  return df

df_kommuner = fetch_data(kommuner)

df_kommuner_folketal = fetch_data(kommuner_folketal)

df_kommuner_g_indkomst = fetch_data(kommuner_g_indkomst)

df_kommuner_g_lavindkomst = fetch_data(kommuner_g_lavindkomst)

connection.close()

# Data validation
schema_df_kommuner = pa.DataFrameSchema({
  'id' : pa.Column(pa.Int, nullable = False, required = True),
  'kommune_navn' : pa.Column(pa.String, nullable = False, required = True)
})

schema_df_kommuner.validate(df_kommuner)

schema_df_kommuner_folketal = pa.DataFrameSchema({
  'kommune_id' : pa.Column(pa.Int, nullable = False, required = True),
  'år' : pa.Column(pa.Int, nullable = False, required = True),
  'kvartal' : pa.Column(pa.String, nullable = False, required = True),
  'folketal' : pa.Column(pa.Float, nullable = False, required = True)
})

schema_df_kommuner_folketal.validate(df_kommuner_folketal)

schema_df_kommuner_g_indkomst = pa.DataFrameSchema({
  'kommune_id' : pa.Column(pa.Int, nullable = False, required = True),
  'år' : pa.Column(pa.Int, nullable = False, required = True),
  'decil_gruppe' : pa.Column(pa.String, nullable = False, required = True),
  'g_indkomst' : pa.Column(pa.Float, nullable = False, required = True)
})

schema_df_kommuner_g_indkomst.validate(df_kommuner_g_indkomst)

schema_df_kommuner_g_lavindkomst = pa.DataFrameSchema({
  'kommune_id' : pa.Column(pa.Int, nullable = False, required = True),
  'år' : pa.Column(pa.Int, nullable = False, required = True),
  'lavindkomst_niveau' : pa.Column(pa.String, nullable = False, required = True),
  'n_lavindkomst' : pa.Column(pa.Float, nullable = False, required = True),
  'p_lavindkomst' : pa.Column(pa.Float, nullable = False, required = True)
})

schema_df_kommuner_g_lavindkomst.validate(df_kommuner_g_lavindkomst)

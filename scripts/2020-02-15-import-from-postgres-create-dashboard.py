# Import data from postgres, perform data validation and EDA, and create dashboard

# Packages
import pandas as pd
import matplotlib.pyplot as plt
import requests
from pyjstat import pyjstat
import os
from sqlalchemy import (create_engine, MetaData, Table, select)

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

## fetch data

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


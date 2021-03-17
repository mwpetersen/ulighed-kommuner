# Create streamlit dashboard with data about inequality and relative poverty

# Modules
import pandas as pd
import requests
from pyjstat import pyjstat
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Import data from dst

## URL to DST's API
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
df_indkomst_kommuner = ds_indkomst_kommuner.write('dataframe', naming = 'label')

df_pct_lavindkomst_kommuner = ds_pct_lavindkomst_kommuner.write('dataframe', naming = 'id')

df_n_lavindkomst_kommuner = ds_n_lavindkomst_kommuner.write('dataframe', naming = 'id')

df_folketal_tekst = ds_folketal.write('dataframe', naming = 'label')
df_folketal_kode = ds_folketal.write('dataframe', naming = 'id')
df_folketal_tekst['id'] = df_folketal_kode['OMRÅDE']

# Data cleaning and wrangling
kun_kommuner = df_indkomst_kommuner["kommune"] != "Hele landet"
regioner = df_indkomst_kommuner["kommune"].map(lambda x: x.startswith('Region'))

df_kommuner_g_indkomst = (df_indkomst_kommuner
   .loc[(kun_kommuner) & (~regioner), ["decil gennemsnit", "kommune", "tid", "value"]]
   .rename(columns = {'tid': 'år',
                      'decil gennemsnit': 'decil_gruppe',
                      'value': 'g_indkomst',
                      'kommune': 'kommune_navn'})
)

df_kommuner_g_indkomst["år"] = pd.to_numeric(df_kommuner_g_indkomst["år"])

# Dashboard title
st.title('Economic inequality and relative poverty in Danish municipalities')

# Create drop down box where the user can select municipality
municipality_category = st.selectbox(
    'Choose municipality:',
     df_kommuner_g_indkomst['kommune_navn'].unique()
    )

# Create line plot with average income grouped by decile
chosen_filter = df_kommuner_g_indkomst['kommune_navn'] == municipality_category

df_g_indkomst_filtered = df_kommuner_g_indkomst[(chosen_filter)]

fig_indkomst = px.line(
  df_g_indkomst_filtered,
  x = "år",
  y = "g_indkomst",
  color = "decil_gruppe",
  custom_data=["decil_gruppe", "år", "g_indkomst", "kommune_navn"])

# The same as above, but with the go method
#fig_indkomst = go.Figure()
#for dg, gruppe in df_g_indkomst_kbh.groupby("decil_gruppe"):
#    fig_indkomst.add_trace(go.Scatter(
#      x=gruppe["år"], 
#      y=gruppe["g_indkomst"], 
#      name = dg, 
#      mode='lines',
#      line=dict(color='rgb(39,112,214)', width=2)
#      ))

# style line plot
x = np.sort(df_g_indkomst_filtered['år'].unique()).tolist()

## values to get x axis length - used in range argument in .update_layout
x_min = df_g_indkomst_filtered['år'].min() - 0.1
x_max = df_g_indkomst_filtered['år'].max() + 0.1

fig_indkomst.update_layout(
    xaxis=dict(
        showline=True,
        showgrid=False,
        showticklabels=True,
        tickvals=x,
        range = [x_min,x_max],
        linecolor='rgb(204, 204, 204)',
        linewidth=2,
        ticks='outside',
        tickfont=dict(
            family='Arial',
            size=12,
            color='rgb(82, 82, 82)',
        ),
    ),
    yaxis=dict(
        showline=True,
        showgrid=False,
        showticklabels=True,
        tickformat=',.d',
        linecolor='rgb(204, 204, 204)',
        linewidth=2,
        ticks='outside',
        tickfont=dict(
            family='Arial',
            size=12,
            color='rgb(82, 82, 82)',
        ),
    ),
    showlegend=False,
    xaxis_title=None,
    yaxis_title=None,
    plot_bgcolor='white',
    separators=",.",
    hoverlabel=dict(
        bgcolor="white",
        font_size=12,
        font_family='Arial'
    )
)

# Set line color and width, and set information in tooltip
fig_indkomst.update_traces(
  line=dict(color='rgb(39,112,214)', width=2),
  hovertemplate=("</br><b>%{customdata[3]}</b></br>" +
                "Gruppe: %{customdata[0]}<br>" +
                "År: %{customdata[1]}</br>" +
                "Indkomst: %{customdata[2]}"))
  
# Adding labels next to lines
annotations = []
for dg, gruppe in df_g_indkomst_filtered.groupby("decil_gruppe"):
    # labeling the right side of the plot
    annotations.append(dict(xref='paper', x=1, y=gruppe["g_indkomst"].iloc[-1],
                                  xanchor='left', yanchor='middle',
                                  text=dg,
                                  font=dict(family='Arial',
                                            size=12),
                                  showarrow=False))

# Add title
annotations.append(dict(xref='paper', yref='paper', x=0.0, y=1.05,
                              xanchor='left', yanchor='bottom',
                              text='Gns. disponibel indkomst de seneste 10 år, fordelt på decil',
                              font=dict(family='Arial',
                                        size=18,
                                        color='rgb(37,37,37)'),
                              showarrow=False))

# Add source
annotations.append(dict(xref='paper', yref='paper', x=1.0, y=-0.1,
                              xanchor='right', yanchor='top',
                              text='Kilde: Danmarks Statistik',
                              font=dict(family='Arial',
                                        size=12,
                                        color='rgb(150,150,150)'),
                              showarrow=False))

fig_indkomst.update_layout(
  annotations=annotations)

## Show plot
st.plotly_chart(fig_indkomst)

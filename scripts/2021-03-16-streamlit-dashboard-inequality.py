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

df_pct_lavindkomst_kommuner = ds_pct_lavindkomst_kommuner.write('dataframe', naming = 'label')

df_n_lavindkomst_kommuner = ds_n_lavindkomst_kommuner.write('dataframe', naming = 'label')

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

df_kommuner_g_lavindkomst = (df_n_lavindkomst_kommuner
   .loc[(kun_kommuner) & (~regioner), ["kommune", "tid", "value"]]
   .merge(df_pct_lavindkomst_kommuner, on = ['kommune', 'tid'])
   .rename(columns = {'kommune': 'kommune_navn',
                      'tid': 'år',
                      'indkomstniveau ': 'lavindkomst_niveau',
                      'value_x': 'n_lavindkomst',
                      'value_y': 'p_lavindkomst'})
   .drop(labels ="Indhold", axis = 1)
)

df_kommuner_g_lavindkomst["år"] = pd.to_numeric(df_kommuner_g_lavindkomst["år"])

# Dashboard title
st.title('Economic inequality and relative poverty in Danish municipalities')

municipalities = df_kommuner_g_indkomst['kommune_navn'].drop_duplicates().tolist()

# Create drop down box where the user can select municipality
municipality_category = st.selectbox(
    'Choose municipality:', 
    municipalities 
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

## style line plot
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

## Set line color and width, and set information in tooltip
fig_indkomst.update_traces(
  line=dict(color='rgb(39,112,214)', width=2),
  hovertemplate=("</br><b>%{customdata[3]}</b></br>" +
                "Group: %{customdata[0]}<br>" +
                "Year: %{customdata[1]}</br>" +
                "Income: %{customdata[2]}"))
  
## Adding labels next to lines
annotations = []
for dg, gruppe in df_g_indkomst_filtered.groupby("decil_gruppe"):
    # labeling the right side of the plot
    annotations.append(dict(xref='paper', x=1, y=gruppe["g_indkomst"].iloc[-1],
                                  xanchor='left', yanchor='middle',
                                  text=dg,
                                  font=dict(family='Arial',
                                            size=12),
                                  showarrow=False))

## Add title
annotations.append(dict(xref='paper', yref='paper', x=0.0, y=1.05,
                              xanchor='left', yanchor='bottom',
                              text='Figure 1: Average income the last 10 years, grouped by decil',
                              font=dict(family='Arial',
                                        size=18,
                                        color='rgb(37,37,37)'),
                              showarrow=False))

## Add source
annotations.append(dict(xref='paper', yref='paper', x=1.0, y=-0.1,
                              xanchor='right', yanchor='top',
                              text='Source: Statistics Denmark',
                              font=dict(family='Arial',
                                        size=12,
                                        color='rgb(150,150,150)'),
                              showarrow=False))

fig_indkomst.update_layout(
  annotations=annotations)

## Show plot
st.plotly_chart(fig_indkomst)

# Create line plot with share of people living in low income families

chosen_filter_lav = df_kommuner_g_lavindkomst['kommune_navn'] == municipality_category

df_g_lavindkomst_filtered = df_kommuner_g_lavindkomst[(chosen_filter_lav)]

fig_lavindkomst = px.line(
  df_g_lavindkomst_filtered,
  x = "år",
  y = "p_lavindkomst",
  custom_data=["lavindkomst_niveau", "år", "p_lavindkomst", "n_lavindkomst", "kommune_navn"],
  height=400
  )

fig_lavindkomst.update_layout(
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
        range = [0, 23],
        showline=True,
        showgrid=False,
        showticklabels=True,
        showticksuffix='all',
        ticksuffix='%', # https://plotly.com/javascript/tick-formatting/
        linecolor='rgb(204, 204, 204)',
        linewidth=2,
        ticks='outside',
        tickfont=dict(
            family='Arial',
            size=12,
            color='rgb(82, 82, 82)',
        ),
    ),
    xaxis_title=None,
    yaxis_title=None,
    plot_bgcolor='white',
    hoverlabel=dict(
        bgcolor="white",
        font_size=12,
        font_family='Arial'
    )
)

fig_lavindkomst.update_traces(
  line=dict(color='rgb(39,112,214)', width=4),
  hovertemplate=("</br><b>%{customdata[4]}</b></br>" +
                 "Year: %{customdata[1]}</br>" + 
                 "percentage: %{customdata[2]} procent</br>" +
                 "Count: %{customdata[3]}</br>" +
                 "income level: %{customdata[0]} percent of median income"))


annotations_low = []

# Add title
annotations_low.append(dict(xref='paper', yref='paper', x=0.0, y=1.05,
                              xanchor='left', yanchor='bottom',
                              text='Figure 2: Persons living in low income families (% of the population)',
                              font=dict(family='Arial',
                                        size=18,
                                        color='rgb(37,37,37)'),
                              showarrow=False))

# Add source
annotations_low.append(dict(xref='paper', yref='paper', x=1.0, y=-0.15,
                              xanchor='right', yanchor='top',
                              text='Source: Statistics Denmark',
                              font=dict(family='Arial',
                                        size=12,
                                        color='rgb(150,150,150)'),
                              showarrow=False))

fig_lavindkomst.update_layout(
  annotations=annotations_low)

st.plotly_chart(fig_lavindkomst)

# Bar plot with municipalities with the highest percentage of their population
# living in low income families

seneste_år = df_kommuner_g_lavindkomst['år'].max()

lavindkomst_top5 = (df_kommuner_g_lavindkomst
  .loc[df_kommuner_g_lavindkomst['år'] == seneste_år]
  .nlargest(5, 'p_lavindkomst', keep = 'all')
)

fig_top5 = px.bar(
  lavindkomst_top5,
  x = 'p_lavindkomst',
  y = 'kommune_navn',
  text='p_lavindkomst',
  orientation = 'h',
  custom_data=["lavindkomst_niveau", "år", "p_lavindkomst", "n_lavindkomst", "kommune_navn"],
  height=350
)

fig_top5.update_traces(marker_color='rgb(39,112,214)')

fig_top5.update_layout(
    xaxis=dict(
        showline=False,
        showgrid=False,
        showticklabels=False
    ),
    yaxis=dict(
      autorange="reversed",
      tickfont=dict(
            family='Arial',
            size=12,
            color='rgb(82, 82, 82)',
        ),
    ),
    margin=dict(
        pad=10 # https://stackoverflow.com/questions/52391451/how-do-i-add-space-between-the-tick-labels-and-the-graph-in-plotly-python
    ),
    xaxis_title=None,
    yaxis_title=None,
    plot_bgcolor='white',
    hoverlabel=dict(
        bgcolor="white",
        font_size=12,
        font_family='Arial'
    )
)

annotations_top5 = []

# Add title
annotations_top5.append(dict(xref='paper', yref='paper', x=0.0, y=1.05,
                              xanchor='left', yanchor='bottom',
                              text='Figure 3: Municipalities with the largest share living in low income families',
                              font=dict(family='Arial',
                                        size=18,
                                        color='rgb(37,37,37)'),
                              showarrow=False))

# Add source
annotations_top5.append(dict(xref='paper', yref='paper', x=1.0, y=-0.05,
                              xanchor='right', yanchor='top',
                              text='Source: Statistics Denmark',
                              font=dict(family='Arial',
                                        size=12,
                                        color='rgb(150,150,150)'),
                              showarrow=False))

fig_top5.update_layout(
  annotations=annotations_top5)

fig_top5.update_traces(
  texttemplate='%{text} %',
  hovertemplate=("</br><b>%{customdata[4]}</b></br>" +
                 "Year: %{customdata[1]}</br>" + 
                 "Percentage: %{customdata[2]} procent</br>" +
                 "Count: %{customdata[3]}</br>" +
                 "Income level: %{customdata[0]} percent of median income"))

st.plotly_chart(fig_top5)

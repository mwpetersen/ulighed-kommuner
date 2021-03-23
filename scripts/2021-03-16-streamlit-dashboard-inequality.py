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
   .rename(columns = {'tid': 'year',
                      'decil gennemsnit': 'decile_group',
                      'value': 'avg_income',
                      'kommune': 'municipality_name'})
)

df_kommuner_g_indkomst["year"] = pd.to_numeric(df_kommuner_g_indkomst["year"])

df_kommuner_g_indkomst['decile_group'] = df_kommuner_g_indkomst['decile_group'].astype(str) + 'e'

df_kommuner_g_lavindkomst = (df_n_lavindkomst_kommuner
   .loc[(kun_kommuner) & (~regioner), ["kommune", "tid", "value"]]
   .merge(df_pct_lavindkomst_kommuner, on = ['kommune', 'tid'])
   .rename(columns = {'kommune': 'municipality_name',
                      'tid': 'year',
                      'indkomstniveau ': 'income_level',
                      'value_x': 'n_lowincome',
                      'value_y': 'p_lowincome'})
   .drop(labels ="Indhold", axis = 1)
)

df_kommuner_g_lavindkomst["year"] = pd.to_numeric(df_kommuner_g_lavindkomst["year"])

df_kommuner_g_lavindkomst["income_level"] = 50

# Dashboard title
st.title('Economic inequality in Danish municipalities')

st.markdown("""
Denmark is one of the most economically equal countries in the world. However, there is still
significant inequality, and the inequality varies a great deal between municipalities. 
The interactive graphs on this page let you see the income inequality and share of people living in 
low-income families in each municipality in Denmark.
""")

# Create drop down box where the user can select municipality
municipalities = df_kommuner_g_indkomst['municipality_name'].drop_duplicates().tolist()

municipality_category = st.selectbox(
    'Choose municipality:', 
    municipalities 
    )

st.header("Income inequality")

st.markdown("""
Figure 1 shows the change in equivalent disposable income over time for each income group. 
The income groups are created by dividing the population of each municipality into 10 equally 
sized groups according to the equivalent disposable income for each household. Persons in 
households with the lowest equivalent disposable income are in the 1. decile, while those 
with the highest income are in the 10. decile.
""")

# Create line plot with average income grouped by decile
chosen_filter = df_kommuner_g_indkomst['municipality_name'] == municipality_category

df_g_indkomst_filtered = df_kommuner_g_indkomst[(chosen_filter)]

fig_indkomst = px.line(
  df_g_indkomst_filtered,
  x = "year",
  y = "avg_income",
  color = "decile_group",
  custom_data=["decile_group", "year", "avg_income", "municipality_name"])

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
x = np.sort(df_g_indkomst_filtered['year'].unique()).tolist()

## values to get x axis length - used in range argument in .update_layout
x_min = df_g_indkomst_filtered['year'].min() - 0.1
x_max = df_g_indkomst_filtered['year'].max() + 0.1

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
    ),
    margin=dict(
        #l=0,
        t=90,
        b=50,
        pad=1
    )
)

## Set line color and width, and set information in tooltip
fig_indkomst.update_traces(
  line=dict(color='rgb(39,112,214)', width=2),
  hovertemplate=("</br><b>%{customdata[3]}</b></br>" +
                "Group: %{customdata[0]}<br>" +
                "Year: %{customdata[1]}</br>" +
                "Income: %{customdata[2]} kr."))
  
## Adding labels next to lines
annotations = []
for dg, gruppe in df_g_indkomst_filtered.groupby("decile_group"):
    # labeling the right side of the plot
    annotations.append(dict(xref='paper', x=1, y=gruppe["avg_income"].iloc[-1],
                                  xanchor='left', yanchor='middle',
                                  text=dg,
                                  font=dict(family='Arial',
                                            size=12),
                                  showarrow=False))

## Add title and subtitle
annotations.append(dict(xref='paper', yref='paper', x=0.0, y=1.15,
                              xanchor='left', yanchor='bottom',
                              text='Figure 1: Average disposable income, grouped by decile' ,
                              font=dict(family='Arial',
                                        size=18,
                                        color='rgb(37,37,37)'),
                              showarrow=False))

annotations.append(dict(xref='paper', yref='paper', x=0.0, y=1.05,
                              xanchor='left', yanchor='bottom',
                              text='Income is in Danish kroner' ,
                              font=dict(family='Arial',
                                        size=14,
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

st.header("Share of people living in low-income families")

st.markdown("""
Figure 2 shows the change over time in the share of the population of the municipality who 
live in a low-income family. Those living in a low-income family are people in households with 
a total income lower than 50 percent of the median income for households in Denmark.
""")

# Create line plot with share of people living in low income families

chosen_filter_lav = df_kommuner_g_lavindkomst['municipality_name'] == municipality_category

df_g_lavindkomst_filtered = df_kommuner_g_lavindkomst[(chosen_filter_lav)]

fig_lavindkomst = px.line(
  df_g_lavindkomst_filtered,
  x = "year",
  y = "p_lowincome",
  custom_data=["income_level", "year", "p_lowincome", "n_lowincome", "municipality_name"],
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
    ),
    margin=dict(
        #l=0,
        t=60,
        pad=1
    )
)

fig_lavindkomst.update_traces(
  line=dict(color='rgb(39,112,214)', width=4),
  hovertemplate=("</br><b>%{customdata[4]}</b></br>" +
                 "Year: %{customdata[1]}</br>" + 
                 "Share of population: %{customdata[2]} %</br>" +
                 "Number of people: %{customdata[3]}</br>" +
                 "income level: %{customdata[0]} % of median income"))


annotations_low = []

# Add title
annotations_low.append(dict(xref='paper', yref='paper', x=0.0, y=1.05,
                              xanchor='left', yanchor='bottom',
                              text='Figure 2: Share of the population living in a low-income family',
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

st.header("Municipalities with the largest share of their population living in a low-income family")

st.markdown("""
Figure 3 shows the five municipalities with the largest share living in a low-income family. 
Use the slider below to choose the year for which data is shown.
""")

# Bar plot with municipalities with the highest percentage of their population
# living in low income families

max_year = int(df_kommuner_g_lavindkomst['year'].max())
min_year = int(df_kommuner_g_lavindkomst['year'].min())

year_filter = st.slider('Choose year:', min_year, max_year, max_year)

lavindkomst_top5 = (df_kommuner_g_lavindkomst
  .loc[df_kommuner_g_lavindkomst['year'] == year_filter]
  .nlargest(5, 'p_lowincome', keep = 'all')
)

fig_top5 = px.bar(
  lavindkomst_top5,
  x = 'p_lowincome',
  y = 'municipality_name',
  text='p_lowincome',
  orientation = 'h',
  custom_data=["income_level", "year", "p_lowincome", "n_lowincome", "municipality_name"],
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
        t=60,
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
                              text='Figure 3: Municipalities with largest share living in a low-income family',
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
                 "Share of population: %{customdata[2]} %</br>" +
                 "Number of people: %{customdata[3]}</br>" +
                 "Income level: %{customdata[0]} % of median income"))

st.plotly_chart(fig_top5)

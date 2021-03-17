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

# Visualizations

## linjegraf med gennemsnitlig disponibel indkomst for befolkningen de sidste 10 år, 
## fordelt på decil.

df_kommuner_g_indkomst = (df_kommuner_g_indkomst
  .merge(df_kommuner, left_on = 'kommune_id', right_on = 'id', how = 'left')
  .drop(['kommune_id', 'id'], axis = 1)
  )

kbh = df_kommuner_g_indkomst['kommune_navn'] == 'København'

df_g_indkomst_kbh = df_kommuner_g_indkomst[(kbh)]

## create line plot

fig_indkomst = px.line(
  df_g_indkomst_kbh,
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
x = np.sort(df_g_indkomst_kbh['år'].unique()).tolist()

## values to get x axis length - used in range argument in .update_layout
x_min = df_g_indkomst_kbh['år'].min() - 0.1
x_max = df_g_indkomst_kbh['år'].max() + 0.1

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
    autosize=False,
    margin=dict(
        autoexpand=False,
        l=100,
        r=50,
        t=110,
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
for dg, gruppe in df_g_indkomst_kbh.groupby("decil_gruppe"):
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
fig_indkomst.show()


## linjegraf med andel af befolkningen de sidste 10 år, der lever i lavindkomstfamilier 
## (antal mennesker i tooltip)

df_kommuner_g_lavindkomst = (df_kommuner_g_lavindkomst
  .merge(df_kommuner, left_on = 'kommune_id', right_on = 'id', how = 'left')
  .drop(['kommune_id', 'id'], axis = 1)
  )

kbh = df_kommuner_g_lavindkomst['kommune_navn'] == 'København'

df_g_lavindkomst_kbh = df_kommuner_g_lavindkomst[(kbh)]

## Create plot

fig_lavindkomst = px.line(
  df_g_lavindkomst_kbh,
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
    autosize=False,
    margin=dict(
        autoexpand=False,
        l=100,
        r=50,
        t=110,
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
                 "År: %{customdata[1]}</br>" + 
                 "Andel: %{customdata[2]} procent</br>" +
                 "Antal: %{customdata[3]}</br>" +
                 "Lavindkomstniveau: %{customdata[0]} procent af medianen"))


annotations_low = []

# Add title
annotations_low.append(dict(xref='paper', yref='paper', x=0.0, y=1.05,
                              xanchor='left', yanchor='bottom',
                              text='Andel (i %) af befolkningen de sidste 10 år, der lever i en lavindkomstfamilie',
                              font=dict(family='Arial',
                                        size=16,
                                        color='rgb(37,37,37)'),
                              showarrow=False))

# Add source
annotations_low.append(dict(xref='paper', yref='paper', x=1.0, y=-0.15,
                              xanchor='right', yanchor='top',
                              text='Kilde: Danmarks Statistik',
                              font=dict(family='Arial',
                                        size=12,
                                        color='rgb(150,150,150)'),
                              showarrow=False))

fig_lavindkomst.update_layout(
  annotations=annotations_low)

fig_lavindkomst.show()

## søjlegraf med top fem kommuner det seneste opgørelsesår med den største andel af 
## deres befolkning der lever i lavindkomstfamilier

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
    autosize=False,
    margin=dict(
        autoexpand=False,
        l=100,
        r=50,
        t=110,
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
                              text='De 5 kommuner med den største andel der lever i en lavindkomstfamilie',
                              font=dict(family='Arial',
                                        size=16,
                                        color='rgb(37,37,37)'),
                              showarrow=False))

# Add source
annotations_top5.append(dict(xref='paper', yref='paper', x=1.0, y=-0.05,
                              xanchor='right', yanchor='top',
                              text='Kilde: Danmarks Statistik',
                              font=dict(family='Arial',
                                        size=12,
                                        color='rgb(150,150,150)'),
                              showarrow=False))

fig_top5.update_layout(
  annotations=annotations_top5)

fig_top5.update_traces(
  texttemplate='%{text} %',
  hovertemplate=("</br><b>%{customdata[4]}</b></br>" +
                 "År: %{customdata[1]}</br>" + 
                 "Andel: %{customdata[2]} procent</br>" +
                 "Antal: %{customdata[3]}</br>" +
                 "Lavindkomstniveau: %{customdata[0]} procent af medianen"))

fig_top5.show()

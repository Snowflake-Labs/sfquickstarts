'''
Snowflake Inc. Code Disclaimer:

The code provided by Snowflake is for demostration purposes only and is provided "as is," without any warranties. Use at your own risk. We do not provide technical support. You may modify the code but do not distribute it without proper attribution. Comply with all applicable laws. By using the code, you agree to this disclaimer.

Snowflake, Inc.
Last updated: 8/7/2023
'''
import requests,json,numpy as np,sys
import pandas as pd
import streamlit as st
import snowflake.connector
import time as time
import toml
import pydeck as pdk
import plotly.express as px
import folium
from streamlit_folium import folium_static
import altair as alt
from datetime import datetime, timedelta
import os, json

# Connect to Consumer Account
def init_connection():
 return snowflake.connector.connect(**st.secrets["snowcat"], client_session_keep_alive=True)

def run_query(query):
   with conn.cursor() as cur:
      cur.execute(query)
      # Return a Pandas DataFrame containing all of the results.
      #df = cur.fetch_pandas_all()
      return cur.fetchall();

def is_dst(zonename):
  from datetime import datetime, timedelta
  import pytz
  tz = pytz.timezone(zonename)
  now = pytz.utc.localize(datetime.utcnow())
  return now.astimezone(tz).dst() != timedelta(0)

def update_query_params():
    hour_selected = st.session_state["pickup_hour"]
    st.experimental_set_query_params(pickup_hour=hour_selected)

# Main
# SETTING PAGE CONFIG TO WIDE MODE AND ADDING A TITLE AND FAVICON
conn = init_connection()
st.set_page_config(layout="wide", page_title="Flight Tracking Demo", page_icon=":airplane:")
headers = {'Content-type': 'application/json'}

hour_selected = st.slider(
        "Select X hours into the past", 1, 24, key="pickup_hour", value=4, on_change=update_query_params
)

role=os.getenv('role')
wh=os.getenv('warehouse')
db=os.getenv('db')
schema=os.getenv('schema')
table=os.getenv('table')
view=".".join([db,schema,table])

run_query("use role " + role + " ;")
run_query("use warehouse " +  wh + " ;")

#daylight saving time is utc-7, so current_time(pacific time) + 4 is past 3 hour data
#standard time is utc-8
past_x_hrs=int(hour_selected)

if is_dst("America/Los_Angeles"):
   tdiff=7
else:
   tdiff=8

delta=int(tdiff)-int(past_x_hrs)
col1, col2, col3 = st.columns(3)
#bar chart
results=run_query("select dest,count(distinct(id)) as arrivals from " + view + " WHERE ts_utc >= DATEADD(hour, " +  str(delta) + ", convert_timezone('UTC','America/Los_Angeles',CURRENT_TIMESTAMP())) group by dest;")

df=pd.DataFrame(results,columns=['airport','arrivals'])

fig = px.bar(
        df,
        x = "airport",
        y = "arrivals",
        title = "Arrivals by Airports in the last " + str(abs(past_x_hrs)) +" hours"
    )
col1.plotly_chart(fig)

#Pie chart
fig = px.pie(
        df,
        names = 'airport',
        values = 'arrivals',
        title = "Arrivals by Airports in the last " + str(abs(past_x_hrs)) +" hours"
    )
col2.plotly_chart(fig)

#Stacked bar chart for arrival flights
results=run_query("select hour(dateadd(hour, -" + str(tdiff) + ", ts_utc)) as hhr,dest,count(distinct(id)) as flights from " + view + " WHERE ts_utc >= DATEADD(hour, " +  str(delta) + ", convert_timezone('UTC','America/Los_Angeles',CURRENT_TIMESTAMP())) and (dest='KSFO' or dest='KOAK' or dest='KSJC') group by hhr,dest order by hhr;")

df=pd.DataFrame(results,columns=['hour','airport','flights'])
df_ksfo=df[df['airport']=='KSFO']
df_ksjc=df[df['airport']=='KSJC']
df_koak=df[df['airport']=='KOAK']
df_ksfo.columns=['hour','airport','KSFO']
f_ksfo=df_ksfo.iloc[:,[0,2]]
df_ksjc.columns=['hour','airport','KSJC']
f_ksjc=df_ksjc.iloc[:,[0,2]]
df_koak.columns=['hour','airport','KOAK']
f_koak=df_koak.iloc[:,[0,2]]
all=pd.merge(f_ksfo, f_ksjc, how='outer', on = 'hour')
all=pd.merge(all, f_koak,  how='outer', on = 'hour')
fig = px.bar(
        all, #Data Frame
        x = "hour", #Columns from the data frame
        y = ['KSFO','KSJC','KOAK'],
        title = "Number of SFO,SJC,OAK arrivals in the last " + str(abs(past_x_hrs)) + " hours"
    )
fig.update_yaxes(title=' ')
col3.plotly_chart(fig)

col21, col22 = st.columns(2)
#map plotting 2D, alt mono color
col21.write("2D arrival flight paths over the bay")
results=run_query("select * from " + view + " WHERE ts_utc >= DATEADD(hour, " +  str(delta) + ", convert_timezone('UTC','America/Los_Angeles',CURRENT_TIMESTAMP())) and (dest='KSFO' or dest='KOAK' or dest='KSJC') order by ts_pt desc;")

df=pd.DataFrame(results)
of=df.iloc[:,1:14]
of.columns=['pt','alt','dest','orig','id','icao','lat','lon','geohash','yr','mo','dd','hr']
mdf = pd.DataFrame(of,columns=['lat', 'lon', 'alt']).dropna()

#Folium map plotting 2D, alt color coded

m = folium.Map(location=[37.6213129,-122.3811494], zoom_start=11, tiles='OpenStreetMap')
ceiling=10000 # don't plot over ceiling
radius=300
mdf=mdf[mdf['alt'] < ceiling]
mdf1=mdf[mdf['alt'].between(0,2000)]
mdf2=mdf[mdf['alt'].between(2000,4000)]
mdf3=mdf[mdf['alt'].between(4000,6000)]
mdf4=mdf[mdf['alt'] > 6000]

for idx, eq in mdf1.iterrows():
  folium.Circle(location=(eq['lat'], eq['lon']), color='red', fill_color='red', fill_opacity=1.0, radius=radius).add_to(m)

for idx, eq in mdf2.iterrows():
  folium.Circle(location=(eq['lat'], eq['lon']), color='purple', fill_color='purple', fill_opacity=1.0, radius=radius ).add_to(m)

for idx, eq in mdf3.iterrows():
  folium.Circle(location=(eq['lat'], eq['lon']), color='blue', fill_color='blue', fill_opacity=1.0, radius=radius).add_to(m)

for idx, eq in mdf4.iterrows():
  folium.Circle(location=(eq['lat'], eq['lon']), color='green', fill_color='green', fill_opacity=1.0, radius=radius).add_to(m)

with col21:
  st.write("Red: below 2k ft, Purple: 2k-4k ft, Blue: 4k-6k ft, Green: above 6k ft")
  folium_static(m, width=700, height=400)
  #folium_static(m)

#map plotting 3D
col22.write("3D arrival flight paths over the bay, altitude color-coded")

radius=300 #control the radius of the columns
escale=15 #control height of the columns

col22.write("Red: below 2k ft, Purple: 2k-4k ft, Blue: 4k-6k ft, Green: above 6k ft")
col22.pydeck_chart(pdk.Deck(
     map_style='mapbox://styles/mapbox/streets-v11',
     initial_view_state=pdk.ViewState(
         latitude=37.6213129,
         longitude=-122.3789554,
         zoom=9,
         pitch=50,
         height=400,
         width=700
     ),
     layers=[
         pdk.Layer(
           #'HexagonLayer', #HexagonLayer counts the dot in same coord and plot as height
            'ColumnLayer', #ColumnLayer uses the get_elevation column as height
            data=mdf1,
            get_position='[lon, lat]',
            get_elevation='[alt]/25',
            get_fill_color=[255, 0, 0 , 150],
            radius=radius,
            elevation_scale=escale,
            elevation_range=[1, 1000],
            pickable=True,
            extruded=True,
            auto_highlight=True,
         ),
         pdk.Layer(
            'ColumnLayer', #ColumnLayer uses the get_elevation column as height
            data=mdf2,
            get_position='[lon, lat]',
            get_elevation='[alt]/25',
            get_fill_color=[148, 0, 211, 160],
            radius=radius,
            elevation_scale=escale,
            elevation_range=[1, 1000],
            pickable=True,
            extruded=True,
            auto_highlight=True,
         ),
         pdk.Layer(
            'ColumnLayer', #ColumnLayer uses the get_elevation column as height
            data=mdf3,
            get_position='[lon, lat]',
            get_elevation='[alt]/25',
            get_fill_color=[100, 149, 237 ,255],
            radius=radius,
            elevation_scale=escale,
            elevation_range=[1, 1000],
            pickable=True,
            extruded=True,
            auto_highlight=True,
         ),
         pdk.Layer(
            'ColumnLayer', #ColumnLayer uses the get_elevation column as height
            data=mdf4,
            get_position='[lon, lat]',
            get_elevation='[alt]/25',
            get_fill_color=[127,255,0,120],
            radius=radius,
            elevation_scale=escale,
            elevation_range=[1, 2000],
            pickable=True,
            extruded=True,
            auto_highlight=True,
         ),
     ],
 ))


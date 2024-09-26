import requests
import pprint
import json
from bs4 import BeautifulSoup

# TODO weather api request
# TODO work the response

# 'all_day.geojson'

ur = 'https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&eventtype=earthquake&orderby=time&limit=1&minmag=6'

earth_quakes = requests.get(ur).json()
coords = earth_quakes['features'][0]['geometry']['coordinates'][:-1]
quake_time = str(earth_quakes['features'][0]['properties']['time'])[:-3]
coord_lat = coords[0]
coord_lon = coords[1]

# '1590094153'
# '1592063483'
# '1592082510'
# '1592082510798'
print(quake_time, coord_lat, coord_lon)
# pprint.pprint(earth_quakes['features'][0]['properties']['time'])


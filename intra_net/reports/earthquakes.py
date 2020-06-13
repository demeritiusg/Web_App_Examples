import requests
from bs4 import BeautifulSoup

# TODO weather api request
# TODO work the response

'all_day.geojson'

ur = 'https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&eventtype=earthquake&orderby=time&limit=10&minmag=6'

earth_quakes = requests.get(ur)

print(earth_quakes.status_code)


import requests
from settings import config
import pprint
import time
import json

key = config['weather_rapid_api_key']
host = config['weather_rapid_api_host']
# payload = {'Token': tok}

headers = {
    'x-rapidapi-host': host,
    'x-rapidapi-key': key
}

query = {}

url = "https://community-open-weather-map.p.rapidapi.com/onecall/timemachine"

# ur = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/data?datasetid=GHCND&locationid=ZIP:28801&startdate=2019-05-01&enddate=2019-05-01'

weather = requests.get(url, headers=headers)

pprint.pprint(weather.json())

# print(json.dumps(payload))

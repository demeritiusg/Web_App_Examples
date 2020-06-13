import requests
from settings import config
import pprint
import time
import json

tok = config['weather_token']
payload = {'Token': tok}

ur = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/data?datasetid=GHCND&locationid=ZIP:28801&startdate=2019-05-01&enddate=2019-05-01'

weather = requests.get(ur, headers=payload)

pprint.pprint(weather.json())

# print(json.dumps(payload))

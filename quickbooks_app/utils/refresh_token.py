from configparser import ConfigParser
import settings
import requests 
import base64
from urllib.parse import parse_qs
from urllib.parse import urlparse
import json
from models import Bearer


# NEEDS TO RECIEVE USERS INPUT ON WHICH COMPANY TO LOGIN FROM APP... MAYBE A DIFFERENT FILE

company = ['FOOT', 'LLC', 'LTD', 'MILL', 'RCP', 'RSM', 'SHR', 'SUN', 'WIRC', 'CYPT']

def refresh_token(company):

    c = company

    redirect_uri = "url"

    tokens_file = 'tokens.cfg'
    token_config = ConfigParser()
    token_config.read(tokens_file)

    QBO_CLIENT_ID = token_config[c]['QBO_CLIENT_ID']

    auth_client = AuthClient(
        client_id=token_config[c]['QBO_CLIENT_ID'],
        client_secret=token_config[c]['client_secret'],
        redirect_uri=redirect_uri,
        environment=token_config[c]['environment'],  # “sandbox” or “production”
    )

    refresh_tok = token_config[c]['refresh_token']

    try:
        auth_client.refresh(refresh_token=refresh_tok)
        rtoken = auth_client.refresh_token
        stoken = auth_client.access_token
        token_config.set(c, 'refresh_token', rtoken)
        token_config.set(c, 'access_token', stoken)
        with open(tokens_file, 'w+') as tokenfile:
            token_config.write(tokenfile)
        print(rtoken)
        print(stoken)
    except AuthClientError as e:
        print(e.status_code)
        print(e.content)
        print(e.intuit_tid)
		
		
for company in company:
    refresh_token(company)
def update_resources(qbo_base_url, realm_id, oauth, resource_name, resources, QBO_TOKEN_URL, company, config, token_config):

    url = "{}/company/{}/batch".format(qbo_base_url, realm_id)
    headers = {
        'Accept': 'application/json',
        'content-type': 'application/json; charset=utf-8',
        'User-Agent': 'RC_QBO_Reporting'
    }

    batch_item_response = []
    
    c = companay
    exception = None
    resource_idx = 0
    chunk_start = 0
    chunk_end = chunk_start + CONFIG['batch_item_limit']
    num_resources = len(resources)
    while chunk_start <= num_resources:
        try:
            batch_item_request = []
            for resource in resources[chunk_start:chunk_end]:
                batch_item = {}
                batch_item["bId"] = "%s" % resource_idx
                batch_item["operation"] = "update"
                batch_item[resource_name] = resource
                batch_item_request.append(batch_item)

                resource_idx += 1

            payload = {}
            payload["BatchItemRequest"] = batch_item_request

            chunk_start += CONFIG['batch_item_limit']
            chunk_end = chunk_start + CONFIG['batch_item_limit']
            
            response = requests.post(
                url=url,
                auth=oauth,
                headers=headers,
                data=json_dumps(payload)
            )
            
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                while e = 401:
                    oauth.refresh(c)
        
                    refresh_token = oauth.refresh_token
                    access_token = oauth.access_token
        
                    token_config.set(c, 'refresh_token', refresh_token)
                    token_config.set(c, 'access_token', access_token)
                
                    with open(TOKENS_FILE, 'w+') as tokenfile:
                        token_config.write(tokenfile)
                
                    response = requests.post(
                        url=url,
                        auth=oauth,
                        headers=headers,
                        data=json_dumps(payload)
                    )
			
                return "Error: " + str(e)

            response_json = response.json()['BatchItemResponse']
        except Exception as e:
            exception = e
            break

        batch_item_response.extend(response_json)

    return exception, batch_item_response, resources

def create_resources(qbo_base_url, realm_id, oauth, resource_name, resources, QBO_TOKEN_URL, config, token_config):

    url = "{}/company/{}/batch".format(qbo_base_url, realm_id)
    headers = {
        'Accept': 'application/json',
        'content-type': 'application/json; charset=utf-8',
        'User-Agent': 'RC_QBO_Reporting'
    }

    batch_item_response = []

    exception = None
    resource_idx = 0
    chunk_start = 0
    chunk_end = chunk_start + CONFIG['batch_item_limit']
    num_resources = len(resources)
    while chunk_start <= num_resources:
        try:
            batch_item_request = []
            for resource in resources[chunk_start:chunk_end]:
                batch_item = {}
                batch_item["bId"] = "%s" % resource_idx
                batch_item["operation"] = "create"
                batch_item[resource_name] = resource
                batch_item_request.append(batch_item)

                resource_idx += 1

            payload = {}
            payload["BatchItemRequest"] = batch_item_request

            chunk_start += CONFIG['batch_item_limit']
            chunk_end = chunk_start + CONFIG['batch_item_limit']
            
            response = requests.post(
                url=url,
                auth=oauth,
				# token_url=token_url,
                headers=headers,
                data=json_dumps(payload)
            )
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                while e = 401:
                    oauth.refresh(c)
        
                    refresh_token = oauth.refresh_token
                    access_token = oauth.access_token
        
                    token_config.set(c, 'refresh_token', refresh_token)
                    token_config.set(c, 'access_token', access_token)
                
                    with open(TOKENS_FILE, 'w+') as tokenfile:
                        token_config.write(tokenfile)
                
                    response = requests.post(
                        url=url,
                        auth=oauth,
                        headers=headers,
                        data=json_dumps(payload)
                    )
			
                return "Error: " + str(e)

            response_json = response.json()['BatchItemResponse']
        except Exception as e:
            exception = e
            break

        batch_item_response.extend(response_json)

    return exception, batch_item_response, resources

def create_resource(qbo_base_url, realm_id, oauth, resource_url, resource, QBO_TOKEN_URL, token_config, dry_run=False, **kwargs):

    # url = fr"{qbo_base_url}/company/{realm_id}/{resource_url}"
    url = "{}/company/{}/{}".format(qbo_base_url, realm_id, resource_url)
    headers = {'Accept': 'application/json', 'content-type': 'application/json; charset=utf-8',
               'User-Agent': 'RC_QBO_Reporting'}
    if dry_run:
        print(f"URL:")
        print("HEADERS")
        print("-------")
        pprint(headers)
        print("RESOURCE")
        print("--------")
        pprint(resource)
        return {
            'url': url,
            'headers': headers,
            'resource': resource
        }
    else:
        response = requests.post(
                url=url,
                auth=oauth,
                # token_url=token_url,
                headers=headers,
                data=json_dumps(payload)
            )
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                while e = 401:
                    oauth.refresh(c)
      
                    refresh_token = oauth.refresh_token
                    access_token = oauth.access_token
        
                    token_config.set(c, 'refresh_token', refresh_token)
                    token_config.set(c, 'access_token', access_token)
                
                    with open(TOKENS_FILE, 'w+') as tokenfile:
                        token_config.write(tokenfile)
                
                    response = requests.post(
                        url=url,
                        auth=oauth,
                        headers=headers,
                        data=json_dumps(payload)
                    )
			
                return "Error: " + str(e)

        return response.json(**kwargs)

def request_resource(qbo_base_url, realm_id, oauth, resource_url, QBO_TOKEN_URL, config, floats_as_decimals=False, debug=False):

    # url = fr"{qbo_base_url}/company/{realm_id}/{resource_url}"
    url = "{}/company/{}/{}".format(qbo_base_url, realm_id, resource_url)
    if debug:
        print('[DEBUG] Requesting: %s' % url)

    response = requests.get(
        auth=oauth,
        url=url,
		# token_url=token_url,
        headers={'Accept': 'application/json'}
    )

    if floats_as_decimals:
        response_json = response.json(parse_float=dec.Decimal)
    else:
        response_json = response.json()

    if debug:
        print('[DEBUG] Received: %s' % list(response_json['QueryResponse']))

    return response_json


def get_valid_access_token(company):
    if is_token_expired(company.access_token):
        #refresh the token
        tokens = refresh_access_token(company.refresh_token)
        company.access_token = tokens['access_token']
        company.refresh_token = tokens['refresh_token']
        db.session.commit()

    return company.access_token
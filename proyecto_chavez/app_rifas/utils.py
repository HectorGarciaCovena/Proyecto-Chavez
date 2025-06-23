# app_rifas/utils.py
import requests
from django.conf import settings

def get_paypal_access_token():
    client_id = settings.PAYPAL_CLIENT_ID
    client_secret = settings.PAYPAL_CLIENT_SECRET
    auth = (client_id, client_secret)
    headers = {'Accept': 'application/json', 'Accept-Language': 'en_US'}
    data = {'grant_type': 'client_credentials'}

    response = requests.post(f"{settings.PAYPAL_API_BASE}/v1/oauth2/token", headers=headers, data=data, auth=auth)
    return response.json().get('access_token')

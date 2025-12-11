# app_rifas/utils.py
import requests
from django.conf import settings
from .models import Numero

def get_paypal_access_token():
    client_id = settings.PAYPAL_CLIENT_ID
    client_secret = settings.PAYPAL_CLIENT_SECRET
    auth = (client_id, client_secret)
    headers = {'Accept': 'application/json', 'Accept-Language': 'en_US'}
    data = {'grant_type': 'client_credentials'}

    response = requests.post(f"{settings.PAYPAL_API_BASE}/v1/oauth2/token", headers=headers, data=data, auth=auth)
    return response.json().get('access_token')

def generar_numeros_para_rifa(rifa):
    existentes = set(Numero.objects.filter(rifa=rifa).values_list('numero', flat=True))
    nuevos = []

    for n in range(rifa.numero_inicial, rifa.numero_final + 1):
        if n not in existentes:
            nuevos.append(Numero(rifa=rifa, numero=n))

    Numero.objects.bulk_create(nuevos)
    return len(nuevos)
'''
=> Script para demonstração de ataque
- Um pequeno script que inicia a requisição de certificado mas não termina o fluxo.
- Usado para testar os mecanismos anti-spam do chimera_identity.py
'''

import requests;
import json

number = an_Telegram_user_id;#integer

url = "https://192.168.0.155:8000/registration";

to_send = json.dumps({'number':f"{number}"});

response = requests.post(url, data=to_send, verify="ca_bundle.pem");

print(response.text)

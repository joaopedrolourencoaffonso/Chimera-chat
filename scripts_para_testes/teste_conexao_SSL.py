'''
=> Script para fazer teste de conexão individual. Client_number é o o id do Telegram do "atacante".
'''

import socket, ssl, sys
import time
client_number = "id_do_telegram_do_atacante";
CERT_AU = "ca_bundle.pem"
CERT_1 = f"{client_number}_crt.pem";
KEY = f"{client_number}.pem";
separador = ":*!$+";
sock = socket.socket(socket.AF_INET);
context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH);
context.set_ciphers('EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH')
context.check_hostname = False;
context.load_cert_chain(certfile=CERT_1, keyfile=KEY)
context.load_verify_locations(cafile=CERT_AU);
conn = context.wrap_socket(sock);

conn.connect(('IP_do_alvo_do_teste', 50052));
resposta = conn.recv();
resposta = resposta.decode('UTF-8');
if resposta == "???":
    conn.write(bytes(sys.argv[1],"utf-8"));
    resposta = conn.recv();
    conn.close();

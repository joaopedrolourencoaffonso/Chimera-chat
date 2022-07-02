from multiprocessing import Process, Value, Lock

from random import randint

import asyncio
from telethon import TelegramClient, events, utils
from variables import api_id, api_hash

from time import sleep, time

import datetime

import socket

import sqlite3

import logging
Log_Format = "%(levelname)s ;; %(asctime)s ;; %(message)s ;;"
logging.basicConfig(level=logging.INFO,filename = "IoTpy.log",format=Log_Format);
logger = logging.getLogger();

'''
==========================
== Envio pelo Telegram  ==
==========================
'''
def enviar_telegram(numero):
    try:
        client = TelegramClient('aplicacao', api_id, api_hash)
        mensagem = f'Enviado pelo Telegram - {numero}';
	    
        async def main():
            await client.send_message("me", mensagem);
            print(mensagem)

        with client:
            client.loop.run_until_complete(main())

    except Exception as e:
        print("Mensagem não pode ser enviada")
        print(e)

'''
==========================
==      Módulo P2P      ==
==========================
'''
def receber(lock, my_id):
    port_r = 50050;
  
    try:
        '''Servidor para receber broadcast UDP'''
        receive_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM);
        receive_server.bind(('', port_r));

        while True:
            con = sqlite3.connect('vizinhos.db');
            cur = con.cursor();
    
            data, (IP, port) = receive_server.recvfrom(1024);
        
            data = data.decode("utf8");
            data = data.split(":");

            if data[0] == "1" and data[1] == str(my_id):
                lock.acquire();#controlando escrita na dB
                
                id_telegram = cur.execute("select * from tabela_de_vizinhos where user_id = ? and addr = ?;",(data[1],IP)).fetchall();
                
                if id_telegram == []:
                    query = f"insert into tabela_de_vizinhos values ({data[1]}, '{datetime.datetime.now()}', '{IP}');";
                    
                else:
                    query = f"update tabela_de_vizinhos set last_seen = '{datetime.datetime.now()}' where user_id = {data[1]} and addr = '{IP}';";
                    
                
                cur.execute(query);
                con.commit();
                
                lock.release();#liberando a dB
                
            con.close();

    except socket.error as e:
        logger.error("receber() - " + str(e));

    except Exception as e:
        logger.error("receber() - " + str(e));

    receive_server.close();  

'''
==========================
==  Envio de mensagens  ==
==========================
'''
def enviar_p2p(numero, my_id, addr, lock):
    import socket, ssl
    import time

    try:
        '''Similar ao test_conexao_ssl'''
        client_number = "{my_id}";
        CERT_AU = "ca_bundle.pem"
        CERT_1 = f"{my_id}_crt.pem";
        KEY = f"{my_id}.pem";
        separador = ":*!$+";
        sock = socket.socket(socket.AF_INET);
        sock.settimeout(2);
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH);
        context.set_ciphers('EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH:!SSLv3:!TLSv1')
        context.check_hostname = False;
        context.load_cert_chain(certfile=CERT_1, keyfile=KEY)
        context.load_verify_locations(cafile=CERT_AU);
        conn = context.wrap_socket(sock);
        
        conn.connect((addr, 50052));
        resposta = conn.recv();
        resposta = resposta.decode('UTF-8');
                
        if resposta == "???":
            mensagem = f"Enviado por P2P - {numero}";
            conn.write(bytes(mensagem,"utf-8"));
            print(mensagem);
            resposta = conn.recv();
            conn.close();

    except Exception as e:
        print(e)
        
        lock.acquire();

        con = sqlite3.connect('vizinhos.db');
        cur = con.cursor();
        query = f"delete from tabela_de_vizinhos where addr = '{addr}';";
        cur.execute(query);
        con.commit();
        
        lock.release();
        
        enviar_telegram(numero);

def main():
    '''Lock para controle da base de dados'''
    lock = Lock();
    
    '''Id de usuário do Telegram'''
    my_id = 1836713877;

    receber_ = Process(target=receber, args=(lock, str(my_id)))
    receber_.start();

    con = sqlite3.connect('vizinhos.db');
    cur = con.cursor();
    
    
    try:
        while True:
            sleep(5);
            
            numero = str(randint(1,10));
            
            '''O lock garante que não haja leitura durante edição da DB'''
            lock.acquire();
            
            '''Só há resultado se o last_seen ainda for válido, isto é
               se não for mais antigo que um minuto'''
            address = cur.execute("select addr from tabela_de_vizinhos where user_id = ? and last_seen > ?;",(my_id,datetime.datetime.now() - datetime.timedelta(minutes=1))).fetchall();
            
            lock.release();
            
            if address == []:
                enviar_telegram(numero);

            else:
                enviar_p2p(numero, my_id, address[0][0], lock)

    except Exception as e:
        print(e)
        print("====\nAdeus\n====")

    receber_.kill();


if __name__ == "__main__":
    main();

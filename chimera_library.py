'''
nome: chimera_library.py
data: 10/04/22
Biblioteca com funções que uso ao longo do projeto
'''

'''---------------Meus custom errors---------------'''
class erro_generico(Exception):
    pass

import sys
import asyncio

#Logging
import logging
Log_Format = "%(levelname)s ;; %(asctime)s ;; %(message)s ;;"
logging.basicConfig(level=logging.INFO,filename = "chimera.log",format=Log_Format)
logger = logging.getLogger();
'''
FUNÇÕES ASSÍNCRONAS
'''

'''
Pega o o id de um grupo e devolve os nomes de usuário e o id de cada membro.
'''
async def pega_nome_de_membros(id_, client):
    resultado = [];
    membros = await client.get_participants(id_, aggressive=True);
    for membro in membros:
        if str(membro.first_name) != "None" and str(membro.last_name) != "None":
            resultado.append((membro.id, membro.first_name+" "+membro.last_name));

        elif str(membro.last_name) == "None":
            resultado.append((membro.id, membro.first_name))

        else:
            resultado.append((membro.id, membro.last_name));

    return resultado;

async def telegram_installer(client):
    try:
        #logging
        import logging
        Log_Format = "%(levelname)s ;; %(asctime)s ;; %(message)s ;;"
        logging.basicConfig(level=logging.ERROR,filename = "chimera.log",format=Log_Format)
        logger = logging.getLogger();
        #sqlite
        import sqlite3;
        con = sqlite3.connect('chats.db');
        cur = con.cursor();

        from os.path import abspath

        #Para acertar as horas de recebimento
        from datetime import datetime, timedelta
        from time import timezone
        fuso = timezone/3600;

        '''PEGANDO INFORMAÇÕES SOBRE OS DIALOGOS INDIVIDUAIS'''
        dialogs = await client.get_dialogs();
        for dialog in dialogs:
            '''
            Insere os ids e os nomes dos respectivos diálogos
            '''
            cur.execute("insert into tabela_de_dialogos values (?, ?)", (dialog.id, dialog.name));
            con.commit();

        print("\n-----TABELA DE DIALOGOS INDIVIDUAIS CRIADA--------\n");

        '''
        Populando as tabelas dos dialogos
        '''
        cur.execute("CREATE TABLE tabela_de_mensagens_temp (id_telegram integer, dialog integer, sent_by integer, date text, msg text, sent_ integer)");
        con.commit();
        
        for dialog_id in cur.execute("select dialog_id, name from tabela_de_dialogos").fetchall():
            dialog_name = dialog_id[1];
            dialog_id = dialog_id[0];

            '''
            - Abaixo, usamos um loop async para iterar sobre todas as mensagens dodiálogo
            - Canais ainda estão banidos, mas eu vou aceitar supergrupos'''
            async for message in client.iter_messages(dialog_id, limit=10):
                
                if message.sender is None:
                    sender_id = dialog_id;

                else:
                    sender_id = message.sender.id
                    
                '''Download automatico de documentos é proíbido de supergrupos e canais, mas permitido para grupos e particulares'''
                if not message.is_channel:
                    if message.photo:
                        path = await message.download_media(file="imagens_chimera/");
                        if message.text == "":
                            entrada = abspath(path)
                        else:
                            entrada = f"{abspath(path)} - {message.text}"

                    elif message.document:
                        path = await message.download_media(file="arquivos_chimera/")
                        if message.text == "":
                            entrada = abspath(path)
                        else:
                            entrada = f"{abspath(path)} - {message.text}"

                    else:
                        entrada = message.text;

                else:                    
                    entrada = message.text;

                    if message.document:
                        try:
                            #Ocasionalmente o Telegram não envia o nome do arquivo, causando uma mensagem de erro
                            try:
                                entrada = "arquivo: " + message.media.document.attributes[1].file_name + " - " + entrada;

                            except:
                                entrada = "arquivo:  - " + entrada;

                        except Exception as e:
                            if str(e).find("object has no attribute 'file_name'") > 0:
                                entrada = "aquivo não especificado - " + entrada;

                    if message.photo:
                        entrada = "foto: photo_" + str(message.date) + " - " + entrada;

                data = message.date - timedelta(hours=int(fuso))
                data = str(data)

                cur.execute("INSERT INTO tabela_de_mensagens_temp (id_telegram, dialog, sent_by, date, msg, sent_) VALUES (?,?,?,?,?,?)", (int(message.id), int(dialog_id), int(sender_id), data, entrada, 0));
                con.commit();
            #
            print("\n====Download do diálogo feito com sucesso====\n");

        '''Ageitando a tabela_de_mensagens'''
        cur.execute("insert into tabela_de_mensagens select * from tabela_de_mensagens_temp order by rowid desc");
        con.commit();
        cur.execute("drop table tabela_de_mensagens_temp;");
        con.commit();

        my_id = await client.get_me()
        my_id = my_id.id;

        open("my_id.txt","w").write(str(my_id))
            
        return "Download dos diálogos finalizados com sucesso!"
        

    except Exception as e:
        print("=======Desculpe, mas houve um erro=======\n");
        print(e);
        logger.error(str(e));
        raise erro_generico;

'''
FUNÇÕES SÍNCRONAS
'''
def login_inicial():
    try:
        import logging
        Log_Format = "%(levelname)s ;; %(asctime)s ;; %(message)s ;;"
        logging.basicConfig(level=logging.INFO,filename = "chimera.log",format=Log_Format)
        logger = logging.getLogger();

        from variables import api_id, api_hash
        from telethon import TelegramClient, events, utils
        
        client = TelegramClient('aplicacao', api_id, api_hash)

        async def main():
            temp = await client.get_me();
            return int(temp.id);

        with client:
            my_id = client.loop.run_until_complete(main())

        return my_id;

    except Exception as e:
        print("=======Desculpe, mas houve um erro=======\n");
        print(e);
        logger.error(str(e));
        return "erro";

'''
Update de boot
================================================
'''
async def verifica_dialogos(client, cur, con):
    #listas
    lista_dialogos_telegram = [];
    relacao_nomes = {};

    async for dialog in client.iter_dialogs():
        lista_dialogos_telegram.append((dialog.id,));
        relacao_nomes[dialog.id] = dialog.name;
        '''
        A variável relacao_nomes serve para relacionar os *atuais* diálogos
        com seus respectivos ids, sem a necessidade de constamente checar
        a base de dados
        '''

    lista_dialogos_db = cur.execute("select dialog_id from tabela_de_dialogos").fetchall();

    new_dialogs = list(set(lista_dialogos_telegram) - set(lista_dialogos_db));

    discarded_dialogs = list(set(lista_dialogos_db) - set(lista_dialogos_telegram));

    return new_dialogs, discarded_dialogs, relacao_nomes;

def verifica_certificado(my_id):
    try:
        from os import popen;
        expirar = str(popen(f"openssl x509 -checkend 432000 -noout -in {my_id}_crt.pem").read())
        expirar_2 = str(popen(f"openssl x509 -checkend 100 -noout -in {my_id}_crt.pem").read())

        '''
        Testamos para ver se o certificado tem um prazo inferior a 5 dias.
        Caso positivo, renovamos o certificado utilizando a API /renew, por meio
        da função 'requests' com mTLS, por isso os campos cert = (cert.pem,key.pem)
        '''
        if expirar_2 == 'Certificate will expire\n':
            '''
            criar função para recriar certificado do zero
            '''
            resultado = novo_certificado()
            return resultado;

        elif expirar == 'Certificate will expire\n':#
            import requests, json
            from variables import step_ca_IP
            [IP, Port] = step_ca_IP.split(":")
            
            url = f"https://{IP}:{Port}/1.0/renew";
            
            response = requests.post(url, verify="ca_bundle.pem", cert=(f"{my_id}_crt.pem",f"{my_id}.pem"));
            response = json.loads(response.text);
            open(f"{my_id}_crt.pem", "w").write(response["crt"] + response["ca"]);
            return "\n===certificado renovado===\n" + response["crt"] + "\n" + response["ca"];

        else:
           return "Tudo ok";

    except Exception as e:
        print("=======Desculpe, mas houve um erro=======\n");
        logger.error(str(e));

def boot_updater():
    try:
        #sqlite
        import sqlite3;
        con = sqlite3.connect('chats.db');
        cur = con.cursor();

        # Telethon
        from variables import api_id, api_hash
        from telethon import TelegramClient, events, utils

        client = TelegramClient('aplicacao', api_id, api_hash)

        '''Limpando base de dados'''
        cur.execute("delete from mensagens_para_enviar where rowid > 0");
        con.commit();

        with client:
            new_dialogs, discarded_dialogs, relacao_nomes = client.loop.run_until_complete(verifica_dialogos(client, cur, con))

        if discarded_dialogs != []:
            for dialog in discarded_dialogs:
                cur.execute("delete from tabela_de_dialogos where dialog_id = ?",(dialog[0],));
                cur.execute("delete from tabela_de_mensagens where dialog = ?",(dialog[0],));

        if new_dialogs != []:
            for dialog in new_dialogs:
                cur.execute("insert into tabela_de_dialogos values (?, ?)",(dialog[0],relacao_nomes[dialog[0]]));

        con.commit();

        '''=========================================='''
        with client:
            client.loop.run_until_complete(boot_update_handler(client, cur, con));
        '''=========================================='''
        '''VERIFICANDO O CERTIFICADO'''
        
        my_id = int(open("my_id.txt","r").read())
        resultado = verifica_certificado(my_id);

        return int(my_id);
        

    except Exception as e:
        print("=======Desculpe, mas houve um erro=======\n");
        print(e);
        logger.error(str(e));
        return "erro";

async def boot_update_handler(client,cur,con):
    from multiprocessing import Lock
    lock = Lock()
    
    from telethon import events
    #Para acertar as horas de recebimento
    from datetime import timedelta
    from time import timezone
    fuso = int(timezone/3600);

    from os.path import abspath
    
    '''editando e deletando'''
    client.add_event_handler(delete_and_edit)
    '''PODE SER QUE ALGUMAS EXCLUSÕES DE MENSAGENS NÃO SEJAM RECEBIDAS'''
    await client.catch_up()
    while client._updates_queue:
        await asyncio.wait(client._updates_queue, return_when=asyncio.ALL_COMPLETED)

    '''Novas mensagens'''
    lista_de_dialogos = cur.execute("select dialog_id from tabela_de_dialogos").fetchall();
    
    for dialog_id in lista_de_dialogos:
        dialog_id = int(dialog_id[0]);
        ultimo = cur.execute(f"select id_telegram from tabela_de_mensagens where dialog = ? order by id_telegram desc limit 1",(dialog_id,)).fetchall();

        if ultimo == []:
            ultimo = 0;
        else:
            ultimo = ultimo[0][0]
            
        async for message in client.iter_messages(dialog_id, min_id=ultimo, reverse=True):
            if message.sender is None:
                sender_id = dialog_id;

            else:
                sender_id = message.sender.id

            '''Download automatico de documentos é proíbido de supergrupos e canais, mas permitido para grupos e chats particulares'''
            path = "";
            if not message.is_channel:
                if message.photo:
                    path = await message.download_media(file="imagens_chimera/");
                    if message.text == "":
                        entrada = abspath(path)
                    else:
                        entrada = f"{abspath(path)} - {message.text}"

                elif message.document:
                    path = await message.download_media(file="arquivos_chimera/")
                    if message.text == "":
                        entrada = abspath(path)
                    else:
                        entrada = f"{abspath(path)} - {message.text}"

                else:
                    entrada = message.text;

            else:
                entrada = message.text;

                if message.document:
                    try:
                        #Ocasionalmente o Telegram não envia o nome do arquivo, causando uma mensagem de erro
                        try:
                            entrada = "arquivo: " + message.media.document.attributes[1].file_name + " - " + entrada;

                        except:
                            entrada = "arquivo  - " + entrada;

                    except Exception as e:
                        print("Exception")
                        if str(e).find("object has no attribute 'file_name'") > 0:
                            entrada = "aquivo não especificado - " + entrada;
                        else:
                            raise e

                if message.photo:
                    entrada = "foto: photo_" + str(message.date) + " - " + entrada;


            data = message.date - timedelta(hours=fuso)
            data = str(data)

            cur.execute("INSERT INTO tabela_de_mensagens (id_telegram, dialog, sent_by, date, msg, sent_) VALUES (?,?,?,?,?,?)", (int(message.id), int(dialog_id), int(sender_id), data, entrada, 0));
            con.commit();
    
    

async def delete_and_edit(event):
    from telethon.tl.types import UpdateDeleteMessages, UpdateEditMessage, UpdateNewMessage
    import sqlite3;
    con = sqlite3.connect('chats.db');
    cur = con.cursor();

    #print(event)
    lock.acquire();
    try:
        if isinstance(event, UpdateDeleteMessages):
            for id_telegram in event.messages:
                cur.execute("delete from tabela_de_mensagens where id_telegram = ?",(id_telegram,));
                con.commit()

        if isinstance(event, UpdateEditMessage):
            cur.execute("update tabela_de_mensagens set msg = ? where id_telegram = ?;",(event.message.message, event.message.id))
            con.commit();

    except Exception as e:
        print("===Módulo Telethon===\n===corrotina de receber delete_and_edit===\nErro:",e);
        logger.error("delete_and_edit " + str(e));

    lock.close();
    con.close();

'''================================================'''

def primeira_instalacao():
    try:
        print("Iniciando: primeira_instalacao");

        #base de dados
        import sqlite3;
        # Telethon
        from variables import api_id, api_hash
        from telethon import TelegramClient, events, utils
        #OS
        from os import mkdir, remove
        from os.path import isfile, isdir

        '''
        Criando diretórios e bases de dados para armazenamento de arquivos
        '''
        
        if not isdir("imagens_chimera"):
            mkdir("imagens_chimera");

        if not isdir("arquivos_chimera"):
            mkdir("arquivos_chimera");

        if isfile("chats.db"):
            remove("chats.db");

        if isfile("vizinhos.db"):
            remove("vizinhos.db");

        '''Criando as tabelas na base de dados chats.db'''
        con = sqlite3.connect('chats.db');
        cur = con.cursor();

        cur.execute("CREATE TABLE tabela_de_dialogos (dialog_id integer, name text)");
        cur.execute("CREATE TABLE tabela_de_grupos (group_id integer, user_id integer, name text)");
        cur.execute("CREATE TABLE mensagens_para_enviar (dialog_id integer, marcador integer, msg text)");
        cur.execute("CREATE TABLE tabela_de_mensagens (id_telegram integer, dialog integer, sent_by integer, date text, msg text, sent_ integer)");
        con.commit();
        con.close();

        '''Criando table de vizinhos'''
        con = sqlite3.connect('vizinhos.db');
        cur = con.cursor();
        cur.execute("CREATE TABLE tabela_de_vizinhos (user_id integer, last_seen datetime, addr text)");
        con.commit();
        con.close()

        print("=======Tabelas criadas=======");

        client = TelegramClient('aplicacao', api_id, api_hash);

        with client:
            resultado = client.loop.run_until_complete(telegram_installer(client))
            print("=======",resultado,"=======");

        if resultado == 1:
            sys.exit();

        resultado = novo_certificado()
        print("----",resultado,"----")
        print("fim")
        

    except Exception as e:
        print("=======Desculpe, mas houve um erro=======\n");
        print(e);
        logger.error(str(e));

def novo_certificado():
    try:
        #comunicação
        import requests
        import json
        #Outros módulos
        from time import sleep
        from os import popen

        from variables import registration_IP, step_ca_IP
        [IP, Port] = registration_IP.split(":")

        '''Pegando id do Telegram'''
        try:
            number = int(open("my_id.txt","r").read())

        except:
            number = login_inicial();
            open("my_id.txt","w").write(str(number))
        '''
        ----------------------------------------
        Obtendo certificados da step-ca
        ----------------------------------------
        '''
        
        url = f"https://{IP}:{Port}/registration";

        '''
        We need to convert to json to send for the registration.py
        '''
        to_send = json.dumps({'number':f"{number}"});

        response = requests.post(url, data=to_send, verify="ca_bundle.pem");

        '''
        Eu uso para sincronizar os scripts e detectar erro no lado servidor
        '''

        if str(response.text) == "1111":
            token = input("Escreva o número que você recebeu no Telegram: ");
            to_send = json.dumps({'number':f"{number}",'token':f"{token}"});

            url = f"https://{IP}:{Port}/send_token";

            response = requests.post(url, data=to_send, verify="ca_bundle.pem");

            ca_token = str(response.text);
            ca_token = json.loads(ca_token);
            ca_token = ca_token["msg"];

            if ca_token.find("Error,") == 0:
                return ca_token;

            if ca_token == "Server error":
                return "Server error";

            comand = f"openssl genrsa -out {number}.pem 4096"
            popen(comand);
            '''
            Os sleeps são usados para dar tempo ao openssl de gerar o certificado
            '''
            print("======\nPrivate Key generated\n======");

            sleep(5);

            comand = 'openssl req -new -key {number}.pem -out {number}.csr -subj "/C=BR/ST=RJ/L=Niteroi/O=UFF/OU=TCC/CN={number}"';
            comand = comand.replace("{number}", str(number));
            popen(comand);

            sleep(5);

            file = open(f"{number}.csr", "r");
            csr = file.read();
            file.close();

            print("======\nRequisição de assinatura gerada com sucesso\n======");
            [IP, Port] = step_ca_IP.split(":")
            url = f"https://{IP}:{Port}/1.0/sign";
            sign_request = json.dumps({
                'csr':csr,
                'ott':ca_token,
            });

            print("\n-----\n",sign_request,"\n---------");

            response = requests.post(url, data=sign_request, verify="ca_bundle.pem");

            print("\n-----Resposta------\n",response.text,"\n-----");

            '''
            Escrevendo certificado em arquivo '.pem'
            '''

            response = json.loads(response.text);
            file = open(f"{number}_crt.pem", "w");
                
            file.write(response["crt"] + response["ca"]);
            file.close()
            print("\n----Seu certificado----\n",response["crt"] + response["ca"]);

            open("token.txt","w").write(ca_token);

            logger.info("Got a new certificate");

            return "\n=========Novo certificado baixado com sucesso!==========\n";

        else:
            logger.error(response.text);
            print(response.text)
            return str(response.text);


    except Exception as e:
        print("=======Desculpe, mas houve um erro=======\n");
        print(e);
        logger.error(str(e));
        sys.exit()


def renovar_certificado():
    try:
        #comunicação
        import requests
        import json

        from variables import step_ca_IP
        [IP, Port] = step_ca_IP.split(":")
        
        print("Iniciando: renovar_certificado");
        '''Pegando o id do Telegram'''
        number = int(open("my_id.txt","r").read())

        url = f"https://{IP}:{Port}/1.0/renew";

        response = requests.post(url, verify="ca_bundle.pem", cert=(f"{number}_crt.pem",f"{number}.pem"));
        response = json.loads(response.text);

        open(f"{number}_crt.pem", "w").write(response["crt"] + response["ca"]);

        logger.info("Renewed certificate");

        print("=======\nCertificado renovado com sucesso!\n=======");

    except Exception as e:
        print("=======Desculpe, mas houve um erro=======\n");
        print(e);
        logger.error(str(e));

def revogar_certificado():
    try:
        print("Iniciando: revogar_certificado");
        #Logging
        import logging
        Log_Format = "%(levelname)s ;; %(asctime)s ;; %(message)s ;;"
        logging.basicConfig(level=logging.INFO,filename = "chimera.log",format=Log_Format)
        logger = logging.getLogger();
        #comunicação
        import requests
        import json
        #Outros módulos
        from os import popen

        number = int(open("my_id.txt","r").read())
        #print(number)

        from variables import step_ca_IP, registration_IP

        print('''Qual o motivo?
0 - Unspecified
1 - KeyCompromise
2 - CACompromise
3 - AffiliationChanged
4 - Superseded
5 - CessationOfOperation
6 - CertificateHold
8 - RemoveFromCRL
9 - PrivilegeWithdrawn
10 - AACompromise''');
        reasonCode = int(input("--> "));

        if reasonCode not in [0,1,2,3,4,5,6,8,9,10]:
            logger.error("Erro de input");
            print("Erro de input")
        #
        else:
            reason = input("Observação:\n-->")
            [IP, Port] = registration_IP.split(":")
            url = f"https://{IP}:{Port}/revoke_token";

            to_send = json.dumps({'number':f"{number}"});

            response = requests.post(url, data=to_send, verify="ca_bundle.pem");

            ott = str(response.text);
            ott = json.loads(ott);
            ott = ott["msg"];

            if ott.find("Error,") == 0:
                return ott;

            if ott == "Server error":
                return "Server error";
            
            [IP, Port] = step_ca_IP.split(":")
            url = f"https://{IP}:{Port}/1.0/revoke";

            serial_hex = popen(f"openssl x509 -noout -serial -in {number}_crt.pem").read();
            serial_hex = serial_hex.replace("serial=","").replace("\n","")
            serial_dec = str(int(serial_hex,16));
            
            ott = json.dumps({"serial":serial_dec,"ott":ott,"passive":True,"reasonCode":reasonCode,"reason":reason});
            
            response = requests.post(url, data=ott, verify="ca_bundle.pem", cert=(f"{number}_crt.pem",f"{number}.pem"));

            response = json.loads(response.text);

            print(response);

            logger.info(f"Certificado {serial_dec} foi revogado");

            print("=======\nCertificado revogado com sucesso!\n=======")

    except Exception as e:
        print("=======Desculpe, mas houve um erro=======\n");
        print(e);
        logger.error(str(e));

'''Essa função serve para escapar áspas simples e duplas. Sem ela, isso causa um erro no SQL.
Você pode entender a solução aqui: https://stackoverflow.com/questions/1586560/how-do-i-escape-a-single-quote-in-sql-server
'''
def ajuste_SQL(msg):
    msg = msg.replace("'", "''");
    msg = msg.replace('"', '""');
    return msg;

def write_variables():
    try:
        api_id = input("Digite sua api_id do Telegram:\n-->");
        api_hash = input("Digite sua api_hash do Telegram:\n-->");
        step_ca_IP = input("Digite o endereço da step-ca no formato -- IP:port\n-->")
        registration_IP = input("Digite o endereço do Provedor de Identidade no formato -- IP:port\n-->")
        broadcast_IP = input("Digite o endereço de broadcast\n-->")

        open("variables.py","w").write(f'''api_id = {api_id}\napi_hash = "{api_hash}"\nstep_ca_IP = "{step_ca_IP}"\nregistration_IP = "{registration_IP}"\nbroadcast_IP = "{broadcast_IP}"''')

    except Exception as e:
        logger.error(str(e));

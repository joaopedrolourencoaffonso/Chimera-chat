'''
Chimera Chat! Um cliente de chat híbrido entre o P2P e o cliente-servidor!
'''
from multiprocessing import Process, Value, Lock
import argparse
import chimera_library
import sys

'''---------------Custom errors---------------'''
class false_telegram_id(Exception):
    pass

'''---------------Funções usadas em todo o script---------------'''      
def quart_module(lock, fim):
    '''Conectando as bases de dados'''
    import sqlite3;
    con = sqlite3.connect('chats.db');
    cur = con.cursor();

    con2 = sqlite3.connect('vizinhos.db');
    cur2 = con2.cursor();

    con3 = sqlite3.connect('aplicacao.session');#base de dados do próprio Telethon
    cur3 = con3.cursor();

    '''logging'''
    import logging
    logging.getLogger('quart.serving').setLevel(logging.ERROR)# silencia as notificações na linha de comando. A maioria delas já era inútil e eu uso meu próprio sistema de logging

    '''Quart'''
    from quart import Quart, render_template, url_for, websocket, redirect, request

    '''asyncio'''
    import asyncio

    app = Quart(__name__)
    
    '''enviar mensagens recém adicionadas na base de dados para a interface'''
    async def sending(dialog_id):
        try:
            '''
            O for abaixo é usado para pegar as últimas dez mensagens do chat, as quais são enviadas de uma vez para a página, de forma que o usuário possa
            ver o que está acontecendo no chat nesse momento.
            '''
            for row in reversed(cur.execute("select sent_by, msg, date from tabela_de_mensagens where dialog = ? order by rowid desc limit 10",(dialog_id,)).fetchall()):
                name = cur3.execute(f"select name from entities where id = {row[0]}").fetchall()
                if name:
                    name = name[0][0];
                else:
                    name = int("-100" + str(row[0]))
                    name = cur3.execute(f"select name from entities where id = {name}").fetchall()
                    if name:
                        name = name[0][0];
                    else:
                        name = "desconhecido"
                        
                send_msg = "<p>" + str(name) + ": " + str(row[1]) + "</p><span class='time'>" + str(row[2]) + "</span>"
                
                await websocket.send(f"{send_msg}");

            '''
            O while abaixo efetivamente implementa a entrega de mensagens para a
            página web. Ele faz isso pela leitura das mensagens na respectiva tabela
            que estão marcadas como "sent_ = 1" '''
            while True:
                res = cur.execute("select sent_by, msg, rowid, date from tabela_de_mensagens where dialog = ? and sent_ != 0",(dialog_id,)).fetchall();
                for message in res:
                    name = cur3.execute(f"select name from entities where id = {message[0]}").fetchall();
                    if name:
                        name = name[0][0];
                    else:
                        name = "desconhecido"
                        
                    send_msg = "<p>" + str(name) + ": " + str(message[1]) + "</p><span class='time'>" + str(message[3]) + "</span>"
                        
                    await websocket.send(f"{send_msg}");
                    
                    lock.acquire();
                    cur.execute("update tabela_de_mensagens set sent_ = 0 where rowid = ?;",(message[2],));
                    con.commit();
                    lock.release();

                await asyncio.sleep(1);

        except asyncio.CancelledError as e:
            # Handle disconnection here
            raise

        except Exception as e:
            print(e);
            print("sending websocket")
            raise

    '''Recebe mensagens da página'''
    async def receiving(dialog_id):
        import datetime
        
        try:
            while True:
                data = await websocket.receive();

                '''Esse 'if' é utilizado para permitir o acesso a mensagens mais antigas.
                   Para ver mensagens mais antigas a função olderFunction do javascript da página html envia uma string: "refresh messages123|n"
                   onde n é um número inteiro maior que 10 utilizado para ver quão antiga a mensagem é, por exemplo, 11 significa que o usuário quer ver a décima primeira
                   mensagem mais antiga do diálogo.'''
                if data.find("refresh messages123") > -1:
                    offset = int(data.split("refresh messages123|")[1]);
                    res = cur.execute("select sent_by, msg, rowid, date from tabela_de_mensagens where dialog = ? order by rowid desc limit 1 offset ?",(dialog_id,offset)).fetchall();
                    
                    for message in res:
                        name = cur3.execute(f"select name from entities where id = {message[0]}").fetchall();
                        if name:
                            name = name[0][0];
                        else:
                            name = "desconhecido"
                            
                        send_msg = "<p>" + str(name) + ": " + str(message[1]) + "</p><span class='time'>" + str(message[3]) + "</span>"
                            
                        await websocket.send(f"{send_msg}");

                else:
                    '''Esse else implementa a inserção de mensagens na tabela: mensagens_para_enviar
                   Basicamente, quando uma mensagem a ser enviada é identificada, o script verifica se o destinatário está na rede local.
                   Se a mensagem é de texto e o destinatário não está na rede local a variável 'marcador' recebe 0, indicando que deve ser transferida pelo Telegram
                   Se a mensagem é de texto e o destinatário     está na rede local a variável 'marcador' recebe 1, indicando que deve ser transferida por  P2P
                 Se a mensagem é um arquivo e o destinatário não está na rede local a variável 'marcador' recebe 2, indicando que deve ser transferida pelo Telegram
                 Se a mensagem é um arquivo e o destinatário     está na rede local a variável 'marcador' recebe 3, indicando que deve ser transferida por  P2P'''
                    addr = cur2.execute(f"select addr from tabela_de_vizinhos where user_id = ?",(dialog_id,)).fetchall();
                
                    '''A string *&%$#@! é usada como um marcador indicando que a informação é o path de um arquivo a ser trasferido'''
                    x = data.find("*&%$#@!");
                    if x == 0 and addr == []:
                        data = data.split("*&%$#@!")[1];
                        marcador = 2;
                        
                    elif x != 0 and addr == []:
                        marcador = 0;

                    elif x == 0 and addr != []:
                        marcador = 3;
                    
                    else:
                        marcador = 1;

                    while True:
                        try:
                            '''Efetivamente inserindo na mensagens_para_enviar'''
                            lock.acquire();
                            cur.execute("insert into mensagens_para_enviar values (?,?,?)", (dialog_id, marcador, data))
                            con.commit();
                            lock.release();
                            break;

                        except sqlite3.ProgrammingError:
                            print(e);
                            await asyncio.sleep(0.1);

                        except Exception as e:
                            print(e);#logging aqui
                            break;
                
                ####

        except asyncio.CancelledError:
            # Erro de conexão
            raise

        except Exception as e:
            print(e);
            print("receiving websocket")
            raise

    ''' websocket de enviar mensagens: Cada subrotina recebe o id do diálogo específico e usa como base para atualizar a respectiva tabela da base de dados.'''
    @app.websocket('/ws/<dialog_id>')
    async def ws(dialog_id):
        try:
            producer = asyncio.create_task(sending(dialog_id));
            consumer = asyncio.create_task(receiving(dialog_id));
            await asyncio.gather(producer, consumer);

        except Exception as e:
            print("Erro websocket: ", e);

    '''Desligar: API que muda o valor do recurso compartilhado 'fim', indicando aos demais processos que estes devem ser finalizados'''
    @app.route('/desligar', methods=['GET'])
    async def desligar():
        try:
            fim.value = 1;
            return await render_template('error.html', error_msg="A aplicação será encerrada em instantes.");

        except:
            return await render_template('error.html', error_msg="Houve um erro durante a finalização.");

    '''conversa individual: API responsável por encontrar um usuário do Telegram e estabelecer um diálogo com o mesmo'''
    @app.route('/nova_conversa', methods=['POST'])
    async def nova_conversa():      
        try:
            number = await request.get_data();
            number = number.decode("utf-8")

            number = number[7:];

            if number.isnumeric():
                lock.acquire();
                cur.execute("insert into mensagens_para_enviar values (?,?,?)", (number, 4, ""))
                con.commit();
                lock.release();

                marcador = cur.execute("select marcador from mensagens_para_enviar where dialog_id = ?;",(number,)).fetchall()[0][0];

                while marcador == 4:
                    await asyncio.sleep(0.1);
                    marcador = cur.execute("select marcador from mensagens_para_enviar where dialog_id = ?;",(number,)).fetchall()[0][0];

                lock.acquire();
                cur.execute("delete from mensagens_para_enviar where dialog_id = ?",(number,))
                con.commit();
                lock.release();

                if marcador == 5:#quer dizer que houve um erro no envio
                    return await render_template('error.html', error_msg=f"Desculpe, o número: {number}, não pode ser contactado.");

                elif marcador == 6:#quer dizer que o diálogo já existe
                    return await render_template('error.html', error_msg=f"Desculpe, mas você já tem um diálogo com o número {number}");

                else:
                    return redirect(f"http://localhost:5000/conversa/{marcador}");
            
            else:
                return await render_template('error.html', error_msg=f"Desculpe, o número: {number}. Você digitou letras ao invés de números");

        except asyncio.CancelledError:
            # Handle disconnection here
            return "Erro"
            raise

        except Exception as e:
            print("===Módulo Quart===\n===nova_conversa()===\nErro:",e);
            return await render_template('error.html', error_msg=f"Desculpe, houve um erro no servidor");
            

    '''conversa individual: API responsável por fornecer páginas html capazes de estabelecer comunicação por websocket, as quais permitem comunicação em tempo real'''
    @app.route('/conversa/<dialog_id>', methods=['GET'])
    async def conversa(dialog_id):
        try:            
            '''Pegando o nome do diálogo na base de dados'''
            dialogs = cur.execute("select name from tabela_de_dialogos where dialog_id = ?", (dialog_id,)).fetchall();

            if dialogs == []:
                '''Informando que o diálogo não existe'''
                return await render_template('error.html', error_msg="Perdão, mas esse diálogo não existe");

            else:
                '''Enviando página html dinâmica com o id de usuário do Telegram e nome de usuário do Telegram'''
                return await render_template('conversa.html', dialog_id=dialog_id, dialog_name=dialogs[0][0]);

        except Exception as e:
            print("===Módulo Quart===\n===conversa()===\nErro:",e);
            return await render_template('error.html', error_msg="Erro de servidor. Por favor, checar o log da aplicação para obter mais informações --> " + str(e));

    '''main: Página inicial da aplicação, pode ser acessada por qualquer um dos endpoints abaixo'''
    @app.route('/')
    @app.route('/main')
    @app.route('/index')
    async def main():
        try:
            conversas = [];
            '''Listando os ids de todos os diálogos dos quais o usuário faz parte. Esses ids são armazenados em um vetor sobre o qual o for abaixo itera, id a id'''
            dialogs = cur.execute("select distinct(dialog) from tabela_de_mensagens").fetchall();
            for row in dialogs:
                '''Pegando a última mensagem enviada no diálogo'''
                last_message = cur.execute("select msg from tabela_de_mensagens where dialog = ? order by rowid desc limit 1;",(row[0],)).fetchall();

                if last_message:
                    last_message = last_message[0][0];
                else:
                    last_message = "Sem mensagens"
                
                '''Pegando o nome do diálogo. A primeira opção é sempre ver na 'tabela_de_dialogos'.'''
                name = cur.execute("select name from tabela_de_dialogos where dialog_id = ?",(row[0],)).fetchall();
                if name:
                    name = name[0][0];
                else:
                    '''Nos casos em que o nome do diálogo não estiver na tabela, acessamos a base de dados aplicacao.session implementada pela própia biblioteca
                       Telethon'''
                    con2 = sqlite3.connect("aplicacao.session");
                    cur2 = con2.cursor()
                    name = cur2.execute("select name from entities where id = ?",(row[0],)).fetchall();
                    con2.close();
                    
                    if name:
                        '''Se o nome é encontrado na aplicacao.session, este é adicionado a tabela_de_dialogos'''
                        name = name[0][0];
                        cur.execute("insert into tabela_de_dialogos values (?,?)",(row[0],name))
                        con.commit()

                    else:
                        '''Caso o nome não seja encontrado, significa que a própria biblioteca Telethon ainda não teve tempo de atualizar a base de dados e uma 
                           mensagem de erro é enviada ao usuário.'''
                        name = "Desconhecido (aperte F5)"
                
                temp = [name, row[0], last_message]
                conversas.append(temp); 
                
            return await render_template('main.html', dialogs=conversas);

        except Exception as e:
            print("===Módulo Quart===\n===main()===\nErro:",e);
            return await render_template('error.html', error_msg="Erro de servidor. Por favor, checar o log da aplicação para obter mais informações");

    try:
        app.run();

    except Exception as e:
        print("===Módulo Quart===\n===app.run()===\nErro:",e);

def telethon_module(fim, lock, my_id):
    '''base de dados'''
    import sqlite3;
    con = sqlite3.connect('chats.db');
    cur = con.cursor();

    ###########################
    from telethon import TelegramClient, events, utils
    import asyncio

    from os.path import abspath

    '''Conectando ao Telegram'''
    import sys

    from variables import api_id, api_hash
    from telethon.events import StopPropagation
    from telethon.tl.types import UpdateDeleteMessages, UpdateEditMessage, UpdateNewMessage

    '''Aqui é criado o objeto 'client' utilizado para comunicação com o telegram
       - O campo connection_retries estabelece quantas vezes o Chimera deve tentar se reconectar com o Telegram caso haja problemas de comunicação. Utilizamos sys.maxsize
       para estabelecer o número de tentativas como sendo o maior número possível que o sistema comporta (no caso do ambiente de testes 9223372036854775807).
       - O campo retry_delay se refere ao tempo entre segundos para cada tentativa de reconexão'''
    client = TelegramClient('aplicacao', api_id, api_hash, connection_retries=sys.maxsize, retry_delay=10);
    ###########################
    '''Módulo de horas'''
    from datetime import timedelta
    from time import timezone
    fuso = int(timezone/3600);

    '''criando o loop de eventos para permitir assíncronia'''
    loop = asyncio.get_event_loop();

    '''
    Criada para forçar as edições na base de dados entrarem numa fila.
    '''
    async def database(query,args):
        lock.acquire()
        cur.execute(query,args);
        con.commit();
        lock.release();

    '''Corrotina responsável por monitorar a 'mensagens_para_enviar', é composta por um loop que verifica se há mensages ou arquivos para serem enviados pelo Telegram
       em intervalos de 0.1 segundos'''
    async def enviar():
        while True:
            try:
                '''Colocando as mensagens a serem enviadas em uma lista'''
                mensagens = cur.execute("select rowid, dialog_id, marcador, msg  from mensagens_para_enviar where marcador = 0 or marcador = 2 or marcador = 4").fetchall();

            except(sqlite3.ProgrammingError):#Cannot operate on a closed database
                print("1 - Adeus!\nCannot operate on a closed database")
                print("2 - Dois motivos possíveis:\n 2.1 - A corrotina de receber lançou uma exception e fechou a conexão 'con' ou\n 2.2 - A conexão de dados com a base de dados foi bloqueada por que algum outro processo provocou um erro")
                break;                
            
            except Exception as e:
                print("===Módulo Telethon===\n===corrotina de enviar mensagens, conexão com Base de dados===\nErro:",e);
                if str(e) == "database is locked":#quando esse erro em específico acontece, a solução mais simples é reiniciar o loop
                    continue;
                else:
                    break;
                
            if not mensagens and fim.value == 0:
                await asyncio.sleep(0.1);

            elif fim.value != 0:
                break;

            else:            
                try:
                    '''Iterando sobre cada item na lista e enviado de acordo'''
                    for mensagem in mensagens:
                        if mensagem[2] == 2:
                            '''Verificando se o path de arquivo é válido e efetivamente transferindo para o Telegram'''
                            from os.path import isfile
                            if isfile(mensagem[3]):
                                msg = await client.send_file(mensagem[1], mensagem[3]);
                                
                            else:
                                '''flag utilizada para indicar que o path inserido é inválido'''
                                is_not_file = 0;

                        elif mensagem[2] == 4:
                            '''Quando o marcador é 4, não é uma mensagem a ser enviada, mas sim um pedido para iniciar um diálogo com outro usuário.
                           A mesma tabela (mensagens_para_enviar) é utilizada para ambos os cenários como forma de dispensar a necesidade de monitorar duas tabelas ao mesmo tempo.
                           Basicamente, o usuário fornece o número de celular da pessoa que deseja conectar e o Chimera extrai essas informações do Telegram e as armazena na chats.db
                           de forma que a interface gráfica possa reencaminhar o usuário para o diálogo propriamente dito'''
                            try:
                                '''A função get_entity é utilizada para para extrair as informações do destinatário'''
                                entity = await client.get_entity(str(mensagem[1]));#NOTA: é preciso que o número de celular esteja cadastrado na agenda do seu celular, caso contrário, não irá encontrar.
                                entity_id = entity.id;

                                '''Verificamos se o usuário já tem um diálogo com o destinatário'''
                                query = f"select dialog_id from tabela_de_dialogos where dialog_id = {entity_id}";
                                result = cur.execute(query).fetchall();

                                if result != []:
                                    '''Se o usuário já tem um diálogo com o destinatário, o marcador 6 é usado para indicar a interface gráfica que uma mensagem de erro deve
                                       deve ser enviada ao cliente'''
                                    await database("update mensagens_para_enviar set marcador = 6 where rowid = ?;",(mensagem[0],));
                                    continue;

                                '''Extraindo o nome de usuário do destinatário. Como nem todos usuários tem um username, as vezes é preciso usar os nomes de entidade'''
                                if entity.username == None:
                                    if entity.first_name == None:
                                        entity_name = entity.last_name;

                                    if entity.last_name == None:
                                        entity_name = entity.first_name;

                                    if entity.last_name != None and entity.first_name != None:
                                        entity_name = entity.first_name + " " + entity.last_name;

                                else:
                                    entity_name = entity.username;

                                '''Atualizado tabela de diálogos para evitar repetição do processo'''
                                await database("insert into tabela_de_dialogos values (?,?);",(entity_id, entity_name));

                                '''Enviando informações obtidas a interface gráfica, de forma que esta possa redirecionar o usuário para a API 'conversa' para
                                   efetivamente iniciar o diálogo'''
                                await database("update mensagens_para_enviar set marcador = ? where rowid = ?;",(entity_id,mensagem[0]));

                                '''Inserimos uma 'mensagem de início'. Dessa forma, caso a pessoa iniciei um diálogo, mas não envie uma mensagem, o diálogo será
                                   listado na página principal de toda forma'''
                                await database(f"insert into tabela_de_mensagens values (-1, ?, ?, ?, ?, 1)", (entity_id, my_id, '', 'Início da conversa'));

                            except Exception as e:
                                print(e)
                                '''Mensagem de erro a ser enviada ao cliente caso haja qualquer problema'''
                                await database("update mensagens_para_enviar set marcador = 5 where rowid = ?;",(mensagem[0],));

                            continue;

                        else:
                            '''Enviando mensagem de texto para o cliente'''
                            msg = await client.send_message(mensagem[1], mensagem[3]);

                        '''Atualizando mensagens_para_enviar para evitar o envio da mesma mensagem múltiplas vezes'''
                        await database("delete from mensagens_para_enviar where rowid = ?;",(mensagem[0],))

                        if 'is_not_file' not in locals():
                            data = str(msg.date);
                            mensagem_temp = chimera_library.ajuste_SQL(mensagem[3]);
                            
                            await database("insert into tabela_de_mensagens values (?,?,?,?,?, 1)",(msg.id,mensagem[1],ME,data,mensagem_temp));

                        else:
                            '''Indicando ao usuário que o arquivo não existe'''
                            print("Erro, o arquivo " + str(mensagem[3]) + " não existe")
                            del is_not_file
                        

                except Exception as e:
                        print("===Módulo Telethon===\n===corrotina de enviar mensagens, conexão com Telegram===\nErro:",e);
                        break;

    '''Corrotina por responsável por receber eventos de mensagens do Telegram. O input: events.NewMessage indica ao Telethon que essa rotina só deve processar
       eventos referentes a mensagens trocadas em diálogos dos quais o usuário faz parte'''
    @client.on(events.NewMessage)
    async def receber(event):
        try:
            '''Verificado se o evento é referente a um diálogo com a característica 'is_channel' ou não. Essa distinção é importante pois diálogos
               com essa característica podem ter milhares de usuários, os quais, por sua vez, podem compartilhar arquivos maliciosos.'''
            if not event.is_channel:
                if hasattr(event.message.peer_id, 'chat_id'):
                    dialog = -int(event.message.peer_id.chat_id);

                else:
                    dialog = int(event.message.peer_id.user_id)

                '''Recebendo arquivos do Telegram'''
                path = ""
                if hasattr(event.media, "document"):
                    path = await client.download_media(event.media, file="arquivos_chimera/");
                    path = abspath(path);

                if hasattr(event.media, "photo"):
                    path = await client.download_media(event.media, file="imagens_chimera/")
                    path = abspath(path);

                '''Data que a mensagem foi registrada no Telegram'''
                data = event.message.date - timedelta(hours=fuso)
                data = str(data);

                '''Texto da mensagem a ser guardada na base de dados'''
                temp_message = chimera_library.ajuste_SQL(event.message.message);
                if path != "":
                    temp_message = path + " - " + temp_message;

                '''Quem enviou a mensagem'''
                if event.message.from_id==None:
                    from_ = event.message.peer_id.user_id;

                else:
                    from_ = event.message.from_id.user_id

                cur.execute(f"insert into tabela_de_mensagens values (?, ?, ?, ?, ?, 1);",(event.message.id, dialog, from_, data, temp_message));
                con.commit();

            else:
                '''O Telegram envia mensagens referentes a supergrupos e canais com um channel_id o qual é sempre igual ao id do canal/supergrupo acrescido
                   de '-100' no seu início.'''
                dialog = int("-100" + str(event.message.peer_id.channel_id));
                if event.message.sender is None:
                    from_ = dialog

                else:
                    from_ = event.message.sender.id

                '''Função utilizada para processar mensagens de texto de forma a mitigar injeções SQL'''
                entrada = chimera_library.ajuste_SQL(event.message.text);

                '''Data que a mensagem foi registrada no Telegram'''
                data = event.message.date - timedelta(hours=fuso)
                data = str(data);

                if event.message.document:
                    try:
                        '''Ocasionalmente o Telegram não envia o nome do arquivo, causando uma mensagem de erro'''
                        try:
                            entrada = "arquivo: " + event.message.media.document.attributes[1].file_name + " - " + entrada;

                        except:
                            entrada = "arquivo:  - " + entrada;

                    except Exception as e:
                        if str(e).find("object has no attribute 'file_name'") > 0:
                            entrada = "aquivo não especificado - " + entrada;

                if event.message.photo:
                    entrada = "foto: photo_" + str(event.message.date) + " - " + entrada;

                cur.execute("insert into tabela_de_mensagens values (?, ?, ?, ?, ?, 1);",(event.message.id, dialog, from_, data, entrada));
                con.commit();
                
                
        except Exception as e:
            print("===Módulo Telethon===\n===corrotina de receber mensagens===\nErro:",e);
            con.close();

        finally:
            raise StopPropagation

    '''Corrotina responsável por receber atualizações de deleção ou edição de mensagem, as classes UpdateDeleteMessages e UpdateEditMessage são importadas
       de uma biblioteca específica do Telethon'''
    async def delete_and_edit(event):
        try:
            if isinstance(event, UpdateDeleteMessages):
                for id_telegram in event.messages:
                    cur.execute("delete from tabela_de_mensagens where id_telegram = ?;",(id_telegram,));
                    con.commit();

            if isinstance(event, UpdateEditMessage):
                cur.execute("update tabela_de_mensagens set msg = ? where id_telegram = ?;",(event.message.message, event.message.id))
                con.commit();

        except Exception as e:
            print("===Módulo Telethon===\n===corrotina de receber delete_and_edit===\nErro:",e);
            con.close();
    

    async def main():
        global ME
        
        ME = my_id;

        client.add_event_handler(delete_and_edit)
        
        enviar_var = asyncio.create_task(enviar());

        await enviar_var;
        
            
    with client:
        try:
            client.loop.run_until_complete(main());
            
        except Exception as e:
            print("===Módulo Telethon===\n===client loop===\nErro:",e);
            future = asyncio.Future();
            future.set_result("1");
            con.close();


def p2p_module(fim, lock, my_id):
    '''Importando as bibliotecas necessárias'''
    try:
        import sys
        import socket, ssl
        from threading import Semaphore, Thread, active_count
        import concurrent.futures#
        from _thread import start_new_thread
        import sqlite3;
        from datetime import datetime, timedelta
        from time import sleep
        import os.path

        import logging
        Log_Format = "%(levelname)s ;; %(asctime)s ;; %(message)s ;;"
        logging.basicConfig(level=logging.INFO,filename = "chimera.log",format=Log_Format)
        logger = logging.getLogger();

    except Exception as e:
        print("=======Desculpe, mas houve um erro e o módulo de comunicação pela LAN não pode ser iniciado=======\n");
        print(e);
        sys.exit();

    porta_r = 50050;
    porta_e = 50051;
    port_ssl = 50052;#
    msg_aqui = "1:" + my_id;
    my_cert = f"{my_id}_crt.pem";#
    ca_bundle = "ca_bundle.pem";#
    private_key = f"{my_id}.pem";#

    '''Essa é a thread responsável por "limpar" a base de dados de todas as entradas mais antigas que 1 minuto.
       Ela funciona com base em um loop que verifica o valor da fim.value a cada um segundo de forma a permitir um encerramento rápido'''
    def cleaner(fim):
        try:
            while True:
                con = sqlite3.connect('vizinhos.db');
                cur = con.cursor();

                vizinhos.acquire();
                cur.execute("delete from tabela_de_vizinhos where last_seen < ?",(datetime.now() - timedelta(minutes=1),))
                con.commit()
                vizinhos.release();
                
                con.close();
                
                contador = 0;
                while contador < 60 and fim.value == 0:
                    sleep(1);
                    contador += 1;

                if fim.value != 0:
                    break;

        except Exception as e:
            print("===Módulo P2P===\n===thread cleaner()===\nErro:",e);
            logger.error("Módulo P2P - cleaner() - " + str(e));
            sys.exit();

    def enviar(fim):
        '''Envia uma mensagem UDP (msg_aqui) para o broadcast em intervalos de 5 segundos
           Onde msg_aqui é definida por 1:id_do_usuário'''

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.bind(('', porta_e))

            from variables import broadcast_IP
            
            while True:
                bytesToSend = str.encode(msg_aqui);
                sleep(5);
                s.sendto(bytesToSend,(broadcast_IP, porta_r));
                if fim.value != 0:
                    s.close();
                    break;

        except Exception as e:
            print("===Módulo P2P===\n===thread enviar()===\nErro:",e);
            logger.error("Módulo P2P - receber() - " + str(e));
            sys.exit()

        s.close();

    def receber(fim):
        '''É a thread responsável por receber as mensagens UDP propriamente ditas. Perceba que a 'receber' em si não edita a base de dados invés
           disso, ela lança threads 'base_de_dados' para isso, de forma a desbloquear a função recv, permitindo recebimento contínuo de anúncios'''
        port_r = 50050;
        n = 0
        results = []
        try:
            receive_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM);
            receive_server.bind(('', port_r));
            n = 0;
            results = [];
            '''A concurrent.futures.ThreadPoolExecutor é usada como forma de controlar o número de threads lançadas,
               de forma a mitigar a possibilidade de um ataque DoS.'''
            with concurrent.futures.ThreadPoolExecutor(5) as executor:
                while True:
                    data, (IP, port) = receive_server.recvfrom(1024);
                    
                    if n <= 10:
                        results.append(executor.submit(base_de_dados, data, IP))
                        n += 1;

                    i = 0
                    while i < len(results):
                        if results[i].done():
                            n -= 1;
                            del results[i]
                        i += 1;

                    if fim.value != 0:
                        break;

        except socket.error as e:
            print("===Módulo P2P===\n===thread receber()===\nErro de conexão a porta:",e);
            logger.error("Módulo P2P - receber() - " + str(e));
            sys.exit();

        except Exception as e:
            print("===Módulo P2P===\n===thread receber()===\nErro:",e);
            logger.error("Módulo P2P - receber() - " + str(e));
            sys.exit();

        receive_server.close();

    def base_de_dados(data, IP):
        '''
        É a thread responsável por efetivamente atualizar a vizinhos.db, sendo um lock utilizado para evitar choques entre escrita e leitura
        '''
        try:
            con = sqlite3.connect('vizinhos.db');
            cur = con.cursor();

            data = data.decode("utf8");
            data = data.split(":");

            if data[0] == "1" and data[1].isnumeric():
                id_telegram = cur.execute("select * from tabela_de_vizinhos where user_id = ? and addr = ?;",(data[1],IP)).fetchall();

                if id_telegram == []:
                    query = f"insert into tabela_de_vizinhos values ({data[1]}, '{datetime.now()}', '{IP}');";#inserindo entrada pela primeira vez

                else:
                    query = f"update tabela_de_vizinhos set last_seen = '{datetime.now()}' where user_id = {data[1]} and addr = '{IP}';";#atualizando entradas

                '''escrevendo na base de dados'''
                vizinhos.acquire();
                cur.execute(query);
                con.commit();
                vizinhos.release();
                con.close();
        
        except Exception as e:
            #logging aqui?
            print("===Módulo P2P===\n===thread base_de_dados()===\nErro:",e);
            logger.error("Módulo P2P - recebe_conexao_ssl() - " + str(e));

        sys.exit();
        '''quando essa thread dá erro, o usuário será informado, mas, a info será perdida'''

    '''############################################################################
    Funções referentes a comunicação P2P com SSL
    '''############################################################################

    '''Recebe os pedidos de conexão'''
    def recebe_conexao_ssl(lock,fim):
        try:
            sock = socket.socket();
            sock.bind(('', port_ssl));
            sock.listen(5);
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH);
            context.load_cert_chain(certfile=my_cert, keyfile=private_key);
            '''As próximas 3 linhas são utilizadas para obrigar o cliente a enviar
            seu próprio certificado, o qual o script vai checar para ver se é efetivamente
            válido dado o ca_bundle oferecido. Mais detalhes: https://docs.python.org/3.8/library/ssl.html#ssl.CERT_REQUIRED'''
            context.verify_mode = ssl.CERT_REQUIRED;#
            context.load_verify_locations(cafile=ca_bundle);
            context.check_hostname = False;

            '''Não usamos o check_hostname pq ele é voltado para IP e acaba dando um erro'''
            context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
            context.set_ciphers('EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH:!SSLv3:!TLSv1')

            n = 0;
            results = [];
            
            with concurrent.futures.ThreadPoolExecutor(2) as executor:
                while fim.value == 0:
                    #if n < 10:
                    if n < 5:
                        ssock, addr = sock.accept();
                        results.append(executor.submit(recebimento_individual, ssock, context, lock))
                        n += 1;

                    else:
                        logger.error(f"Possível ataque DoS proveniente de: {addr}");
                        sleep(7);

                    i = 0;
                    while i < len(results):#elimina processos não mais necessários
                        if results[i].done():
                            n -= 1;
                            del results[i]

                        i += 1;

            

        except Exception as e:
            print("===Módulo P2P===\n===thread recebe_conexao_ssl()===\nErro:",e);
            logger.error("Módulo P2P - recebe_conexao_ssl() - " + str(e));


    '''Thread que lida com as conexões para receber mensagens individualmente'''
    def recebimento_individual(ssock, context, lock):
        try:
            ssock.settimeout(2)
            conn = context.wrap_socket(ssock, server_side=True);
            '''
            Abaixo, pegamos o nome no certificado enviado. Esse passo parece bobo,
            já que qualquer um pode pegar o certificado de outra pessoa, mas sem ele,
            nada funciona.
            '''
            cert = conn.getpeercert(binary_form=False);
            cert_name = cert['subjectAltName'][0][1];
            '''
            Essas duas linhas indicam para o remetente que conexão foi aceita e que
            podemos receber a mensagem.
            '''
            conn.write(bytes("???","utf-8"));
            msg_recebida = conn.recv(1024).decode('UTF-8');
            
            if msg_recebida == "klighxfrewsyhkbfa":
                '''Criando um nome para o arquivo'''
                file_name = datetime.now();
                file_name = f"{file_name.year}-{file_name.month}-{file_name.day}-{file_name.hour}-{file_name.minute}-{file_name.second}"
                conn.write(bytes("???","utf-8"));

                '''Recebendo a extensão do arquivo, isto é, o tipo de arquivo: pdf, mp4, png...'''
                extension = conn.recv(32).decode('UTF-8');

                if extension in [".jpg", ".jpeg", ".png", ".gif"]:
                    file_name = os.path.abspath(f"imagens_chimera/{file_name}{extension}")

                else:
                    file_name = os.path.abspath(f"arquivos_chimera/{file_name}{extension}")
                    
                conn.write(bytes("???","utf-8"));

                with open(file_name, "wb") as file:
                    while True:
                        bytes_read = conn.recv(4096);

                        if not bytes_read:
                            break;

                        file.write(bytes_read);

                lock.acquire();
                con = sqlite3.connect('chats.db');
                cur = con.cursor();
                
                cur.execute("insert into tabela_de_mensagens values (-1, ?, ?, ?, ?, 1);",(cert_name, cert_name, str(datetime.now()),file_name));
                con.commit();
                lock.release();
                con.close();

            elif msg_recebida == "":
                '''Caso nenhuma mensagem seja recebida'''
                conn.close();

            else:
                con = sqlite3.connect('chats.db');
                cur = con.cursor();

                '''Filtrando a mensagem contra possíveis injeções SQL'''
                msg_recebida = chimera_library.ajuste_SQL(msg_recebida);

                '''Efetivamente escrevendo na base de dados'''
                lock.acquire();
                cur.execute("insert into tabela_de_mensagens values (-1, ?, ?, ?, ?, 1);",(cert_name, cert_name,str(datetime.now()),msg_recebida));
                con.commit();
                lock.release();
                con.close();

        except ssl.SSLError as e:
            print("===Módulo P2P===\n===thread recebimento_individual()===\nErro:\n==recebimento_individual ssl error==\n");
            print(e);
            logger.error("Módulo P2P - recebimento_individual() - " + str(e));

        except Exception as e:
            print("===Módulo P2P===\n===thread recebimento_individual()\n===\nErro:", e);
            logger.error("Módulo P2P - recebimento_individual() - " + str(e));

        finally:
            conn.close();

    '''Faz o efetivo envio da mensagem'''
    def enviar_msg(lock,fim):
        '''Contém exemplos de teste. Necessário utilizar máquina virtual para teste completo'''
        con = sqlite3.connect('chats.db');
        cur = con.cursor();
        con2 = sqlite3.connect('vizinhos.db');
        cur2 = con2.cursor();

        while fim.value == 0:
            '''Funciona de maneira similar ao telethon_module, lançando uma query na base de dados a cada 0.1 segundo para ver se há uma nova mensagem a ser enviada'''
            try:
                mensagens = cur.execute("select rowid, dialog_id, marcador, msg from mensagens_para_enviar where marcador = 1 or marcador = 3").fetchall();
                
                if not mensagens:
                    sleep(0.1);
                    
                else:
                    '''Criando um objeto contexto para ser utilizado durante a conexão TLS.'''
                    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH);
                    
                    '''A linha abaixo é particulamente relevante, pois ela estabelece quais protocolos serão utilizados.
                       O conjunto de protocolos especificado são considerados seguros ou recomendados pelo site: https://ciphersuite.info/ sendo todos do TLSv1.2 ou TLSv1.3'''
                    context.set_ciphers('EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH:!SSLv3:!TLSv1')
                    context.check_hostname = False;
                    
                    context.load_cert_chain(certfile=my_cert, keyfile=private_key)
                    context.load_verify_locations(cafile=ca_bundle);

                    '''Aqui é iniciado o loop que itera sobre o vetor de mensagens a enviar e estabelece, uma a uma, as conexões para transferência de informação'''
                    from os.path import isfile, splitext
                    for mensagem in mensagens:
                        if mensagem[2] == 3:
                            temp_file_path = mensagem[3].split("*&%$#@!")[1];
                            if isfile(temp_file_path):
                                _, extension = splitext(temp_file_path);
                            else:
                                print("==>Arquivo " + str(temp_file_path) + " não existe<==")
                                lock.acquire();
                                cur.execute("delete from mensagens_para_enviar where rowid = ?",(mensagem[0],));
                                con.commit();
                                lock.release();
                                continue
                        
                        IP_addresses = cur2.execute("select addr from tabela_de_vizinhos where user_id = ?;",(mensagem[1],)).fetchall()

                        '''Esse loop é para o caso de haver mais de uma instâcia da conta do Telegram destinatária conectadas na mesma rede
                           Novamente, o Chimera itera uma a uma, estabelecendo as conexões individualmente'''
                        for temp in IP_addresses:
                            IP_address = temp[0];
                            
                            '''efetivamente cria o socket'''
                            sock = socket.socket(socket.AF_INET);
                            '''envolve o soquete no nosso contexto especial'''
                            conn = context.wrap_socket(sock);
                            '''faz a conexão'''
                            conn.connect((IP_address, 50052));

                            conn.settimeout(2)
                            
                            my_IP_address = conn.getsockname()[0]
                            
                            '''O estabelecimento de conexão confirma que o destinatário detém a chave privada relativa ao certificado apresentado
                            Aqui, realizamos o equivalente ao 'match_hostname', verificando se o id de usuário do certificado é de fato o do destinatário'''
                            cert = conn.getpeercert(binary_form=False);
                            cert_name = cert['subjectAltName'][0][1];
                            
                            if not cert_name == str(mensagem[1]):
                                raise false_telegram_id;
                            
                            resposta = conn.recv(1024);
                            resposta = resposta.decode('UTF-8');

                            if resposta == "???":
                                if mensagem[2] == 3:
                                    conn.write(bytes("klighxfrewsyhkbfa","utf-8"));
                                    resposta = conn.recv(32);

                                    conn.write(bytes(extension,"utf-8"));
                                    resposta = conn.recv(32)

                                    with open(temp_file_path, "rb") as file:
                                        while True:
                                            bytes_read = file.read(4096);
                                            if not bytes_read:
                                                break;

                                            conn.write(bytes_read);

                                    conn.close();
                                    lock.acquire();
                                    cur.execute("delete from mensagens_para_enviar where rowid = ?",(mensagem[0],));
                                    con.commit();
                                    lock.release();
                                    
                                else:   
                                    conn.write(bytes(mensagem[3],"utf-8"))
                                    conn.close();
                                    lock.acquire();
                                    cur.execute("delete from mensagens_para_enviar where rowid = ?",(mensagem[0],));
                                    con.commit();
                                    lock.release();

                                if IP_address != my_IP_address:
                                    data = str(datetime.now()) + "+00:00";

                                    mensagem_temp = mensagem[3].split("*&%$#@!");
                                    if len(mensagem_temp) == 1:
                                        mensagem_temp = mensagem_temp[0];
                                    else:
                                        mensagem_temp = mensagem_temp[1];
                                    
                                    mensagem_temp = chimera_library.ajuste_SQL(mensagem_temp);
                                    
                                    lock.acquire();
                                    cur.execute("insert into tabela_de_mensagens values (-1, ?, ?, ?, ?, 1)",(mensagem[1], my_id, data, mensagem_temp));
                                    con.commit();
                                    lock.release();

                            else:
                                conn.close()

            except(false_telegram_id):
                print("===\nId do telegram diferente do anúnciado, possível ataque!\n===");
                lock.acquire();

                if mensagem[2] == 1:
                    cur.execute("update mensagens_para_enviar set marcador = 0 where dialog_id = ?",(mensagem[1],));

                else:
                    cur.execute("update mensagens_para_enviar set marcador = 2, msg = ? where dialog_id = ?",(temp_file_path,mensagem[1]));

                con.commit();
                lock.release();
                vizinhos.acquire();
                cur2.execute("delete from tabela_de_vizinhos where user_id = ?",(mensagem[1],));
                con2.commit();
                vizinhos.release();
                conn.close()
                logger.error("Módulo P2P - enviar_msg() - Id de usuário do Telegram diferente do anúnciado, possível ataque!");

            except(sqlite3.ProgrammingError):
                print("===Módulo P2P===\n===thread enviar_msg()\n===\nErro:\nCannot operate on a closed database");
                break;

            except Exception as e:
                if str(e).find("Uma tentativa de conexão falhou") > 0:
                    print("Problema de conexão!");

                else:
                    print("===Módulo P2P===\n===thread enviar_msg()\n===\nErro:", e);
                    logger.error("Módulo P2P - enviar_msg() - " + str(e));
                
                if 'mensagem' not in locals():
                    '''ESSE ERRO SÓ OCORRE NA SEÇÃO 1. Se um erro for erguido naquela seção do código, é melhor parar o envio completo mesmo'''
                    print("===Módulo P2P===\n===thread enviar_msg()\n===\nmensagem vazia\n====Erro: ", e);
                    lock.acquire();
                    cur.execute("update mensagens_para_enviar set marcador = 0 where marcador = 1");
                    cur.execute("update mensagens_para_enviar set marcador = 2 where marcador = 3");
                    con.commit();
                    lock.release();
                    conn.close()
                    sys.exit();

                elif mensagem[2] == 1:
                    lock.acquire();
                    cur.execute("update mensagens_para_enviar set marcador = 0 where dialog_id = ?",(mensagem[1],));
                    con.commit();
                    lock.release();

                else:
                    lock.acquire();
                    cur.execute("update mensagens_para_enviar set marcador = 2, msg = ? where dialog_id = ?",(temp_file_path,mensagem[1]));
                    con.commit()
                    lock.release();
                
                conn.close()

    
    def main():
        '''Função responsável por limpar a base de dados a cada 1 minuto.'''
        cleaner_thread = Thread(target=cleaner, args=(fim,))
        cleaner_thread.start();
        
        '''Criando a thread que envia mensagens.
        Ela é *independente* do restante, então não precisa compartilhar nenhum recurso.'''
        enviar_thread = Thread(target=enviar, args=(fim,))
        enviar_thread.start();

        '''criando socket para receber pedidos
           Opera de maneira independente do enviar()'''
        receber_thread = Thread(target=receber, args=(fim,))
        receber_thread.start();

        '''Cria um servidor para receber pedidos de conexão'''
        recebe_conexao_ssl_thread = Thread(target=recebe_conexao_ssl, args=(lock,fim))
        recebe_conexao_ssl_thread.daemon = True;
        recebe_conexao_ssl_thread.start();

        '''Função para receber input do usuário e enviar para o user selecionado'''
        enviar_msg_thread = Thread(target=enviar_msg, args=(lock,fim))
        enviar_msg_thread.start();

        while fim.value == 0:
            '''Sleep é utilizado para simplesmente manter o script vivo'''
            sleep(1);
            '''Verifica se alguma das threads morreu, caso positivo, reinicia a thread'''
            if not enviar_thread.is_alive() and fim.value == 0:
                enviar_thread.join();
                enviar_thread = Thread(target=enviar, args=(fim,))
                enviar_thread.start();

            if not receber_thread.is_alive() and fim.value == 0:
                receber_thread.join();
                receber_thread = Thread(target=receber, args=(fim,))
                receber_thread.start();

            if not cleaner_thread.is_alive() and fim.value == 0:
                cleaner_thread.join();
                cleaner_thread = Thread(target=cleaner, args=(fim,))
                cleaner_thread.start();

            if not recebe_conexao_ssl_thread.is_alive() and fim.value == 0:
                recebe_conexao_ssl_thread.join();
                recebe_conexao_ssl_thread = Thread(target=recebe_conexao_ssl, args=(lock,fim))
                recebe_conexao_ssl_thread.daemon = True;
                recebe_conexao_ssl_thread.start();

            if not enviar_msg_thread.is_alive() and fim.value == 0:
                enviar_msg_thread.join();
                enviar_msg_thread = Thread(target=enviar_msg, args=(lock,fim))
                enviar_msg_thread.start();

        enviar_thread.join();
        receber_thread.join();
        cleaner_thread.join();
        '''recebe_conexao_ssl_thread.join() -> Essa thread é daemon então ela se encerrará quando as demais se encerrarem'''
        enviar_msg_thread.join();
        
        return "Finalização bem sucedida"

    try:
        vizinhos = Semaphore(1);
        resultado = main();
        print("======",resultado,"======\n");

    except Exception as e:
        print("===Módulo P2P===\n===Função main()===\nErro:",e);
        logger.error("Módulo P2P - main() - " + str(e));
        sys.exit();



'''INTERFACE DE LINHA DE COMANDO'''
parser = argparse.ArgumentParser(description='Chimera, software de chat para p2p over LAN e Telegram')
parser.add_argument('--install',action="store_true", help='Primeira Instalação do Chimera');
parser.add_argument('--new', action="store_true",help='Obter novo certificado');
parser.add_argument('--renew', action="store_true",help='Renovar certificado');
parser.add_argument('--revoke', action="store_true", help='Revogar certificado');
parser.add_argument('--variables', action="store_true", help='Criar arquivo com variáveis');

args = parser.parse_args();

if [args.install, args.new, args.renew, args.revoke, args.variables].count(True) > 1:
    print('''\n===Só é possível uma ação por vez===''');
    sys.exit();
    
if __name__ == "__main__":
    '''UTILIDADES'''
    if args.install:
        chimera_library.primeira_instalacao();
        sys.exit();

    if args.new:
        chimera_library.novo_certificado();
        sys.exit();

    if args.renew:
        chimera_library.renovar_certificado();
        sys.exit();

    if args.revoke:
        chimera_library.revogar_certificado();
        sys.exit();

    if args.variables:
        chimera_library.write_variables();
        sys.exit();
    
    if chimera_library.instalacao_correta() == 1:
        print("Verifique se você realizou a instalação corretamente!")
        sys.exit()

    '''Update das bases de dados antes do boot'''
    my_id = chimera_library.boot_updater();
    print('''
Atualizando base de dados, aguarde.''');

    if my_id == "erro":
        print("Ocorreu um erro durante a inicialização")
        sys.exit()

    '''Limpando os logs'''
    open("chimera.log","w").write("")
    
    '''Efetivamente iniciando o cliente'''
    fim = Value('i', 0);
    
    '''Lock para controle da base de dados'''
    lock = Lock();

    '''Módulo da interface gráfica'''
    quart_ = Process(target=quart_module, args=(lock, fim))

    '''Módulo de comunicação com o Telegram'''
    telethon_ = Process(target=telethon_module, args=(fim, lock, my_id))

    '''Módulo de comunicação P2P'''
    p2p_ = Process(target=p2p_module, args=(fim, lock, str(my_id)))

    quart_.start();
    telethon_.start();
    p2p_.start();

    '''Espera o usuário decidir encerrar a aplicação'''
    from time import sleep
    while fim.value == 0:
        sleep(1);
    
    quart_.kill();
    
    quart_.join();
    telethon_.join();
    p2p_.join();

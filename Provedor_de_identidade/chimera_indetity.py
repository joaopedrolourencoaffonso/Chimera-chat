#!/usr/bin/python

'''
This version is capable of supporting server errors and user mistakes, as well as storing them on a log file that can be used as database.
'''

###Path for config file
import sys
sys.path.insert(2, sys.argv[1])

###Path for config file
import chimera_config

##mysql
import mysql.connector

mydb = mysql.connector.connect(
  host=chimera_config.mysql_host,
  user=chimera_config.mysql_user,
  password=chimera_config.mysql_password,
  database=chimera_config.mysql_database
);

cur = mydb.cursor();

###
from quart import Quart, render_template, jsonify, request
import hypercorn.asyncio

from hypercorn.config import Config
config = Config()
config.bind = chimera_config.config_bind
config.certfile = chimera_config.config_certfile
config.keyfile = chimera_config.config_keyfile
config.ciphers = chimera_config.config_ciphers


from datetime import datetime, timedelta
from random import randint
from os import popen
api_id = chimera_config.api_id;
api_hash = chimera_config.api_hash;
from telethon import TelegramClient
import json

#logging
import logging
log_format = "%(levelname)s ;; %(asctime)s ;; %(message)s";
logging.basicConfig(level=logging.INFO,filename="chimera_identity.log",format=log_format);
logger = logging.getLogger();

# 1 - As linhas abaixo são apenas para fazer o login no telegram
client = TelegramClient('chimera_identity', api_id, api_hash)

async def chimera_login():
    await client.send_message('me', 'Starting chimera_identity.py!')
    
with client:
    client.loop.run_until_complete(chimera_login());
########

app = Quart(__name__)
#app.secret_key = 'senha'

@app.route('/registration', methods=['POST'])
async def registration(): 
    try:
        if request.method == 'POST':
            '''
            Processando o post request recebido
            '''
            number = await request.get_data();
            number = json.loads(number);
            number = number['number'];
            
            cur.execute(f"select * from temp_token where number = '{number}';");
            output = cur.fetchall();
            saida = len(output)
            print(output);
            cur.execute("commit;")
            
            if (number.isnumeric()) and saida == 0:
                token = randint(10000, 99999);
                print(token);
                
                temp_number = int(number);
                #prazo = datetime.now() + timedelta(minutes=5);
                prazo = datetime.now();
                
                await client.send_message(temp_number, f"Bem vindo! Seu token é {token}, ele dura apenas 5 minutos.");
                
                query = "insert into temp_token values (%s, %s, %s)";
                values = (number, token, str(prazo));
                cur.execute(query, values);
                cur.execute("commit;");
                
                logger.info(f"Token {token} sent for {number} ;; {request.remote_addr}");
            
                return "1111";
                
            elif saida > 0:
                logger.error(f"chimera_identity Multiple token requests for {number} ;; {request.remote_addr}");
                return "Error, multiple token requests";
            
            else:
                logger.error(f"chimera_identity Invalid number ;; {request.remote_addr}");
                return "Error, invalid number";
            
        else:
            logger.error("chimera_identity User tried to use 'get' request ;; {request.remote_addr}");
            return "2222";
        
    except Exception as e:
        print(e);
        logger.error("chimera_identity " + str(e) + " ;; " + request.remote_addr);
        return "Server Error"
        
@app.route('/send_token', methods=['POST'])
async def send_token():
    try:
        if request.method == 'POST':
            '''
            Processando o post request recebido
            '''
            number = await request.get_data();
            number = json.loads(number);
            token = number['token'];
            number = number['number'];
            
            if (number.isnumeric()) and (token.isnumeric()):
                cinco_minutos_atras = datetime.now() - timedelta(minutes=5);
                token = int(token);
                cur.execute(f"select * from temp_token where number = '{number}' and token = {token} and hour > '{cinco_minutos_atras}';");
                print(f"select * from temp_token where number = '{number}' and token = {token} and hour > '{cinco_minutos_atras}';");
                saida = len(cur.fetchall());
                
                if saida == 1:
                    cur.execute(f"delete from temp_token where number = '{number}' and token = {token};");
                    cur.execute("commit;");

                    step_token = f"step ca token '{number}' --key token.key --password-file pass.txt";
                    stream = popen(step_token);
                    step_token = str(stream.read());
                    
                    logger.info(f"Access token send to {number} ;; " + request.remote_addr);
                    
                    return jsonify(msg=step_token);
                    
                else:
                    logger.error(f"send_token User {number} used wrong Telegram token ;;" + request.remote_addr);
                    return jsonify(msg="Error, wrong Telegram token");
            
            else:
                logger.error(f"send_token Invalid Telegram token or number {token} {number} ;; " + request.remote_addr);
                return jsonify(msg="Error, invalid number or Telegram token");
        
        else:
            logger.error("send_token User tried to use get request ;; " + request.remote_addr);
            return jsonify(msg="Error, only post request");
            
    except Exception as e:
        logger.error("send_token " + str(e));
        return jsonify(msg="Server error");

@app.route('/revoke_token', methods=['POST'])
async def revoke_token():
    try:
        if request.method == 'POST':
            '''
            Processando o post request recebido
            '''
            number = await request.get_data();
            number = json.loads(number);
            number = number['number'];
            
            step_token = f"step ca token {number} --revoke --key token.key --password-file pass.txt";
            stream = popen(step_token);
            step_token = str(stream.read());
            
            logger.info(f"revoke_token {number} got a revoke token ;; " + request.remote_addr);
            
            return jsonify(msg=step_token);
            
        else:
            logger.error("revoke_token User tried to use get request ;; " + request.remote_addr);
            return jsonify(msg="Error, only post request");
        
    except Exception as e:
        logger.error("revoke_token " + str(e));
        return jsonify(msg="Server error");

        
# Connect the client before we start serving with Quart
@app.before_serving
async def startup():
    await client.connect()


# After we're done serving (near shutdown), clean up the client
@app.after_serving
async def cleanup():
    await client.disconnect()

#-------------------
@app.route('/')
@app.route('/index')
@app.route('/main')
async def index():
    return await render_template("index.html")

def cert_updater():
    try:
        import requests, json
        
        url = "https://192.168.0.155:8443/1.0/renew";
        
        response = requests.post(url, verify="ca_bundle.pem", cert=("quart_crt.pem","quart_key.pem"));
        response = json.loads(response.text);
        
        open("quart_crt.pem", "w").write(response["crt"] + response["ca"]);
        
        logger.info("Certificate has been renewd.");
        
        return 0;
        
    except Exception as e:
        logger.error("cert_updater: " + str(e));
        return 1
        
async def main():
    logger.info("Server has started");
    result = cert_updater();
    
    if result == 1:
        print("Error trying to start");
        
    else:
        await hypercorn.asyncio.serve(app, config);
        
    logger.info("Server has finished.");

    
if __name__ == '__main__':
    client.loop.run_until_complete(main())

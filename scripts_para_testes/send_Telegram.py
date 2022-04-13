'''
=> Script para envio de mensagens pelo Telegram em massa.
- Não use esse script para outro usuário que não seja o seu próprio, ou o Telegram pode banir sua conta por SPAM.
- Para fazer um bom teste, é interessante colocar várias cópias desse script funcionando em paralelo, mas se for faze-lo, tome cuidado para colocar nomes de sessão diferentes ("aplicacao_1","aplicacao_2",etc)
- Salve sua api_id e api_hash em um arquivo chamado variables.py localizado no mesmo diretório.
'''

from variables import api_id, api_hash
from telethon import TelegramClient, events, utils
import asyncio

client = TelegramClient('aplicacao', api_id, api_hash)


async def main():
    i = 0;
    while i < 100:
        await client.send_message("me", f'Mensagem {i}')
        i += 1;

with client:
    client.loop.run_until_complete(main())

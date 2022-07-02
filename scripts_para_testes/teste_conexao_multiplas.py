'''
=> Script para teste de saturação de mensagens.
- Esse script trabalha em associação com o teste_conexao_ssl.py.
- Originalmente os dois scripts deveriam ser um só, porém, encontrei em dificuldades em implementar, num único script, um loop capaz de abrir múltiplos sockets ao mesmo tempo, ao usar o
"popen" o sistema é obrigado a usar multithreading.
'''
import time
from os import popen

x1 = time.perf_counter();
for i in range(1,1000):
    time.sleep(0.2);
    txt = 'python teste_conexao_SSL.py "App 2 - ' + str(i) + '"';
    popen(txt)
    
x2 = time.perf_counter();

print(f"O processo durou {x2 - x1} segundos.\n Isso quer dizer poderia ser feito {1000/(x2 - x1)} por segundo")

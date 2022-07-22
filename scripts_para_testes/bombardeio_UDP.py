'''
=> Script para envio de anúncios UDP em massa.
- em essência o script causa um flood de anúncios, simulando uma rede congestionada/ataque DoS.
'''

from time import sleep, perf_counter
import socket
from random import randint
import sys

porta_r = 50050;
porta_e = 50060;
broadcast_IP = "192.168.0.255";

def main():
    try:
        msg_aqui = 0
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)#
        s.bind(('', porta_e))
        x1 = perf_counter()
        while msg_aqui < 10000:
            msg_aqui += 1
            bytesToSend = str.encode("1:" + str(msg_aqui));
            print(msg_aqui)
            s.sendto(bytesToSend,(broadcast_IP, porta_r));

        x2 = perf_counter()
        print(x2 - x1, " segundos")
        print(10000/(x2 - x1)," mensagens por segundo")
                

    except Exception as e:
        print(e)
        sys.exit()

if __name__ == "__main__":
    main();

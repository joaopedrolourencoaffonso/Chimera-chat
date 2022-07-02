# Chimera Chat
<p align="center">
  <img src="https://github.com/joaopedrolourencoaffonso/Chimera-chat/blob/main/figuras_chimera/chimera_chat_3.png?raw=true" alt="Figura 2 - Página principal da Aplicação" style="width:184px;height:192px;">
</p>
<p align="center">
	Figura 1 - Logo do Chimera
</p>
O Chimera chat é uma aplicação de chat híbrida entre os modelos cliente-servidor e P2P, sendo capaz de identificar quando o destinatário de uma mensagem está na mesma rede LAN que o remetente e assim estabelecer comunicação direta e segura com o destinatário, dispensando o apoio de um servidor central. A aplicação conta ainda com uma infraestrutura de chave pública (PKI) para fornecer certificados SSL aos usuários.

## Proposta
A demanda por dados [nunca foi maior](https://www.cisco.com/c/en/us/solutions/executive-perspectives/annual-internet-report/infographic-c82-741491.html) e isso não deve mudar em breve, com empresas de videogame chegando a processar 50 Terabytes por dia e previsões estimando a chegada de [75 bilhões](https://seedscientific.com/how-much-data-is-created-every-day/#:~:text=Right%20now%2C%2031.4%20gigabytes%20is,data%20used%20per%20month%20worldwide) de dispositivos IoT ao mercado nos próximos anos. Com base nessas estatísticas se faz necessário perguntar: A forma como essas informações são transmitidas é realmente eficiente?

É de conhecimento comum que aplicações de chat são uma das maneiras mais populares de transferir arquivos no ambiente [doméstico](https://fossbytes.com/send-file-using-whatsapp/) e [corporativo](https://www.syskit.com/blog/microsoft-teams-essential-guide-to-file-sharing/), porém, mesmo uma análise superficial demonstra a ineficiência dessa operação. Seja o caso, por exemplo, de um trabalhador que deseja transferir um relatório para seu chefe por meio do Whastapp. Se ambos estiverem no mesmo escritório, isso significa que os dados precisarão ser enviados do seu computador para o roteador, que então enviará para outro roteador, que enviará para outro e assim por diante até chegar aos servidores da Meta. Lá, os dados serão processados e reenviados (talvez pelo mesmo caminho) para então chegarem ao computador do chefe.

Isso não é eficiente, e como mencionado anteriormente, só vai piorar, ainda mais quando se considera os, muitas vezes esquecidos, custos [ambiental](https://computer.howstuffworks.com/internet/basics/how-much-energy-does-internet-use.htm#:~:text=Ultimately%2C%20Raghavan%20and%20Ma%20estimated,to%20170%20to%20307%20gigawatts.) e [econômico](https://www.forbes.com/sites/quora/2012/03/14/how-much-does-the-internet-cost-to-run/?sh=184b87671157) da internet.

A esse fato se soma ainda a **exposição** dos dados trafegados na internet, dado que, mesmo com a imposição [quase obrigatória](https://blog.cloudflare.com/today-chrome-takes-another-step-forward-in-addressing-the-design-flaw-that-is-an-unencrypted-web/) de medidas de segurança mínimas, estas nem sempre são [implementadas da maneira correta](https://crypto.stanford.edu/~dabo/pubs/abstracts/ssl-client-bugs.html), podem ser [mal configuradas](https://www.researchgate.net/publication/355117101_Open_for_hire_attack_trends_and_misconfiguration_pitfalls_of_IoT_devices) ou simplesmente ficarem [ultrapassadas](https://en.wikipedia.org/wiki/Data_Encryption_Standard) pelo progresso tecnológico e científico.

Com base nesses príncipios, apresentamos aqui o _Chimera Chat_, uma ferramenta de chat online capaz de agir como Proxy Transparente do Telegram e mensageiro por LAN simultaneamente. Para isso, o Chimera se utiliza de seu próprio protocolo com base em anúncios, de forma a mitigar [ataques de amplificação](https://www.springerprofessional.de/en/ddos-never-dies-an-ixp-perspective-on-ddos-amplification-attacks/19017760), os quais podem ser observados em [outros procolos](https://blog.cloudflare.com/ssdp-100gbps/).

## Filosofia e Limitações
O principal objetivo deste projeto é servir como "proof of concept" da viabilidade de sistemas cliente-servidor híbridos com comunicação ponto-a-ponto sobre LAN sendo o Whatsapp o modelo de referência, dado que é uma das aplicações de chat [mais populares](https://www.statista.com/statistics/258749/most-popular-global-mobile-messenger-apps/) do mundo. Dessa forma, foi empregada uma atitude minimalística em relação ao design das página html utilizadas, assim como das funcionalidades oferecidas. 

As funcionalidades de "canais" e supergrupos, por exemplo, são implementadas de maneira parcial, sendo possível o usuário iteragir com os mesmos, porém, arquivos partilhados por esses meios não são acessíveis, uma vez que são possíves vetores de Malware. Da mesma maneira, por padrão, quando o Chimera é iniciado pela primeira vez, ele faz o download das últimas 10 mensagens trocadas em cada diálogo do Telegram, sendo mensagens anteriores **inacessíveis**, uma vez que isso não apenas tornaria o tempo de instalação desnecessariamente demorado como também tornaria extremamente difícil a iteração com canais e supergrupos, que podem trocar milhares de mensagens por dia. Sendo assim, o Chimera é capaz de:

- enviar mensagens por cloud-chats do Telegram e armazená-las em uma base de dados SQLite.
- receber mensagens pelo cloud-chats do Telegram e armazená-las em uma base de dados SQLite.
- enviar mensagens por conexão em rede local e armazená-las em uma base de dados SQLite.
- receber mensagens por conexão em rede local e armazená-las em uma base de dados SQLite.
- Receber e enviar arquivos por cloud-chats do Telegram, sendo que o caminho absoluto de cada arquivo armazenado na base de dados para acesso pelo usuário.
- Receber e enviar arquivos por conexão em rede local, sendo que o caminho absoluto de cada arquivo armazenado na base de dados para acesso pelo usuário.
- Encontrar outro usuário e começar um diálogo utilizando o número de celular registrado na agenda.
- Fornecer uma interface gráfica para interação natural pelo usuário

## Instalação
Dado que a comunicação ponto a ponto implementada no Chimera se baseia em certificados SSL para criptografia e autenticação, a instalação do sistema como um todo é dívida nas seguintes etapas:

### 1 - Ambiente Virtual
A presente aplicação foi desenvolvida com base no **Python 3.8.5** e não funcionará no seu formato atual para versões do Python que não suportem TLSv_1.3 (```ssl.HAS_TLSv1_3```).

Primeiramente, é recomendável que seja utilizado um ambiente virtual, o que pode ser feito utilizando o módulo [venv](https://docs.python.org/3/library/venv.html) do Python. Para criar um ambiente virtual, basta utilizar o comando:
```python
python3 -m venv /caminho_para_seu_ambiente
```
No caso de haver mais de uma versão do Python no host, é possível utilizar o comando:
```bash
virtualenv teste --python C:\Python38\python.exe
```
Para acessar ou sair do ambiente virtual, basta utilizar os scripts activate.bat e deactivate.bat, conforme abaixo:
```python
#ativação
caminho_para_seu_ambiente\Scripts\activate.bat

#desativação
caminho_para_seu_ambiente\Scripts\deactivate.bat
```

### 2 - Instalando as bibliotecas Python
Para criar a interface gráfica e as APIs de suporte, foi utilizado o [Quart](https://pgjones.gitlab.io/quart/) versão 0.16.3. Para instalar a versão mais recente, basta utilizar o comando:
```python
pip install quart
```
Para melhor interagir com o Quart e com a Autoridade Certificadora, foi utilizada a biblioteca [Requests](https://docs.python-requests.org/en/latest/) versão 2.27.1. Para instalar a versão mais recente, basta utilizar o comando:
```python
pip install requests
#ou
python -m pip install requests
```
Para interagir com o Telegram, foi utilizado o [Telethon](https://telethonn.readthedocs.io/en/latest/) versão 1.24.0, para instalar a versão mais recente, basta utilizar o comando:
```python
pip3 install telethon
```
É recomendável (mas não obrigatório) a instalação da biblioteca [cryptg](https://pypi.org/project/cryptg/) uma vez que ela executa a criptografia em C, sendo muito mais rápida. No presente projeto, foi utilizada a versão 0.2.post4, mas a versão mais recente pode ser obtida utilizando:
```python
pip install cryptg
```
### 3 - Instalando a step-ca
A [step-ca](https://smallstep.com/docs/step-ca) é uma autoridade certificadora de código aberto criada pela [Smallstep](https://smallstep.com/). Ela é a contraparte do lado servidor da [step-cli](https://smallstep.com/docs/step-cli) e sua instalação não é difícil, sendo detalhada [aqui](https://smallstep.com/docs/step-ca/installation).

No Ubuntu, é possível instalar a versão mais recente da step-cli (ou apenas "step") utilizando:
```bash
wget -O step.tar.gz https://dl.step.sm/gh-release/cli/docs-ca-install/v0.18.2/step_linux_0.18.2_amd64.tar.gz
tar -xf step.tar.gz
sudo cp step_0.18.2/bin/step /usr/bin
```
Para instalar a step-ca, basta usar:
```bash
wget -O step-ca.tar.gz https://dl.step.sm/gh-release/certificates/docs-ca-install/v0.18.2/step-ca_linux_0.18.2_amd64.tar.gz
tar -xf step-ca.tar.gz
sudo cp step-ca_0.18.2/bin/step-ca /usr/bin
```

### 4 - Configurando a step-ca
A [documentação da Smallstep](https://smallstep.com/docs/step-ca/installation) é bem completa sobre como realizar a configuração e a própria step-ca conta com um procedimento passo a passo (veja um exemplo [aqui](https://github.com/joaopedrolourencoaffonso/Chimera-chat/blob/main/instalando-step-ca.txt)). Para iniciar esse wizard, basta usar o comando:
```bash
step ca init
```
Basta configurar conforme o exemplo abaixo:
```bash
✔ Deployment Type: Standalone
What would you like to name your new PKI?
✔ (e.g. Smallstep): joaopedro
What DNS names or IP addresses would you like to add to your new CA?
✔ (e.g. ca.smallstep.com[,1.1.1.1,etc.]): 192.168.0.155                            # Nome de domínio da CA, caso não haja um, pode usar o endereço IP
What IP and port will your new CA bind to?
✔ (e.g. :443 or 127.0.0.1:443): 192.168.0.155:8443                                 # Usado para que a step ca utilize o IP público (ou nesse caso local) da máquina
What would you like to name the CA's first provisioner?
✔ (e.g. you@smallstep.com): joaopedro@example.com                                  # email exemplo usado apenas para fins de desenvolvimento
Choose a password for your CA keys and first provisioner.
✔ [leave empty and we'll generate one]: "senha"                                    # senha para encriptar a chave privada da autoridade certificadora e do provedor de identidade
```
_Nota: No caso de a step-ca estar sendo instalada na mesma LAN em que o Chimera será utilizado (como foi o caso durante o desenvolvimento do protótipo) é recomendável que seja atribuído um IP fixo a máquina host._

Feito isso, uma mensagem contendo a localização de vários arquivos relevantes irá aparecer na tela:
```
✔ Root certificate: /home/joao/.step/certs/root_ca.crt
✔ Root private key: /home/joao/.step/secrets/root_ca_key
✔ Root fingerprint: b8d6f9eadd39e5b7f0891c4f00b2e84350fb5ee31514c733a7617435c531b935
✔ Intermediate certificate: /home/joao/.step/certs/intermediate_ca.crt
✔ Intermediate private key: /home/joao/.step/secrets/intermediate_ca_key
✔ Database folder: /home/joao/.step/db
✔ Default configuration: /home/joao/.step/config/defaults.json
✔ Certificate Authority configuration: /home/joao/.step/config/ca.json
```
É recomendável que os resultados sejam anotados em algum lugar seguro de agentes maliciosos.
Com esse passo completo, é preciso fazer mais algumas edições, para isso, é preciso editar o ca.json de forma a adicionar o campo:
```json
"claims": {
			"minTLSCertDuration": "5m",
			"maxTLSCertDuration": "264h",  
			"defaultTLSCertDuration": "240h"
}
```
Esse segmento deve ser inserido dentro do campo "authority" do json, de forma a garantir uma validade de dez dias o que é bem inferior ao [um ano](https://www.encryptionconsulting.com/education-center/renew-expired-ssl-certificates/) recomendado por empresas como Google e Huawei, somado ao fato de que a aplicação é projetada para a operação em LAN provê segurança enquanto mantendo a carga computacional relativamente baixa.

Por fim, é preciso destacar um aspecto do funcionamento da step-ca, a [**exposição da chave privada do provedor de identidade**](https://github.com/smallstep/certificates/discussions/668).

Esse aspecto pode causar confusão, mas, basicamente, quando uma autoridade certificadora é criada, a step-ca já vem com um "provedor de identidade padrão" com uma chave relativamente fraca que fica armazenada **publicamente**, no endpoint: [/provisioners](https://smallstep.com/docs/step-ca/provisioners). Apesar de contraituitivo, essa decisão se justifica pelos seguintes motivos:

 - O provedor de identidade em questão é simplesmente um exemplo criado para permitir a familiarização do usuário com os comandos, não sendo adequado para o ambiente de produção, dentre outros motivos, pelo fato de a chave não ser forte
 - Os desenvolvedores da Smallstep alegam que não há risco para segurança dado que que a chave é armazenada criptografada por [senha](https://github.com/smallstep/certificates/discussions/668#discussioncomment-1860002) sendo assim tão forte quanto a senha.
 - É possível (e recomendável) retirar a chave privada criptografada do endpoint editando o respectivo campo do ca.json (campo: "provisioners" > "encryptedKey") e armazenando a mesma em um arquivo (```token.key```)
 - É possível (e recomendável) o cadastro de novos [provedores de identidade](https://smallstep.com/docs/step-cli/reference/ca/provisioner), dentre as opções, uma das mais intuitivas seria a utilização de certificados X5C a qual é explorada em mais detalhes [aqui](https://github.com/joaopedrolourencoaffonso/python_smallstep/tree/main/7-version).

Durante o desenvolvimento do presente projeto, foi utilizado o provedor de identidade padrão como forma de simplificar os testes, porém, no futuro, pretendemos adaptar o Chimera para utilização dos certificados X5C. As mudanças de um para outro, no entanto, deverão ser mínimas.

### 5 - Provedor de Identidade
Mesmo sendo possível utilizar a step-ca em um [máquina remota](https://smallstep.com/docs/step-cli/reference/ca/bootstrap), é recomendável, e mais simples, que o [chimera_identity.py](https://github.com/joaopedrolourencoaffonso/Chimera-chat/blob/main/Provedor_de_identidade/chimera_indetity.py) seja instalado na mesma, tomando o cuidado, é claro, para se escolher uma porta disponível. É possível encontrar uma explicação completa [aqui](https://github.com/joaopedrolourencoaffonso/Chimera-chat/tree/main/Provedor_de_identidade) assim como visitar o [diretório](https://github.com/joaopedrolourencoaffonso/python_smallstep) de desenvolvimento original. Como o processo de instalação do chimera_identity.py involve alguns conceitos próprios ele foi colocado em um arquivo diferente deste README, podendo ser encontrado [aqui](https://github.com/joaopedrolourencoaffonso/Chimera-chat/blob/main/Provedor_de_identidade/README.md#instala%C3%A7%C3%A3o).

Também é preciso destacar que o Provedor de Identidade não é **extritamente necessário** sendo recomendado apenas para situações em que renovar manualmente os certificados seja impraticável. Para situações em que tal demanda não exista (como pequenas empresas ou equipes) é possível delegar a tarefa de gerar/renovar os certificados para uma pessoa específica ou aos próprios funcionários, porém, nesse caso, é necessário tomar os seguintes cuidados:

- Os certificados devem todos ser assinados pela mesma autoridade certificadora, é recomendado o uso da step-ca, mas a utilização da OpenSSL ou um script baseado em alguma linguagem de programação também é plausível.
- Os certificados devem ser armazenados em arquivos no formato: {id_do_Telegram_do_usuário}\_crt.pem. Do mesmo modo, o "Common Name" também deve ser o id de usuário do Telegram
- As chaves privadas devem ser armazenadas em arquivos no formato: {id_do_Telegram_do_usuário}.pem
- Os certificados e as chaves privadas devem ser armazenados no mesmo diretório que os scripts: ```chimera.py``` e ```chimera_library.py```.

### 6 - OpenSSL
O OpenSSL é utilizado para geração de chave privada e requisições de assinatura de certificado do lado cliente. Durante o desenvolvimento do projeto foi utilizada a [versão 3.0](https://www.openssl.org/source/), a qual tem suporte até 2026. É possível também utilizar a versão 1.1.1, sendo que esta tem suporte até 2023, versões mais antigas devem ser evitadas.

De um modo geral, o OpenSSL já vem imbutido em vários sistemas operacionais baseados no unix (como o Ubuntu) assim como em algumas aplicações (como o ```git```), mas no caso desse não estar instalado no sistema, pode-se fazer donwload diretamente na página do [github](https://github.com/openssl/openssl) ou baixar os [binários](https://wiki.openssl.org/index.php/Binaries).

### 7 - Os Arquivos
Com a [infraestrutura de chave pública](https://smallstep.com/blog/everything-pki/) em posição, basta agora copiar os arquivos deste diretório para um diretório da máquina de teste. Feito isso, basta pegar o bundle de certificados SSL da step-ca e salvar neste mesmo diretório com o nome de: "ca_bundle.pem" e aplicação estará ponta para operar.

## O Código
### Interação entre os Módulos
O código do Chimera é dividido em duas partes, o [chimera.py](https://github.com/joaopedrolourencoaffonso/Chimera-chat/blob/main/chimera.py) o qual efetivamente implementa o cliente e a biblioteca [chimera_library.py](https://github.com/joaopedrolourencoaffonso/Chimera-chat/blob/main/chimera_library.py), a qual armazena várias funções úteis utilizadas ao longo do projeto. 

Quando um usuário inicia o ```chimera.py```, o mesmo utiliza o pacote ```multiprocessing``` do Python para iniciar outros três processos:
```python
'''Módulo da interface gráfica'''
quart_ = Process(target=quart_module, args=("1", controle, lock))

'''Módulo de comunicação com o Telegram'''
telethon_ = Process(target=telethon_module, args=("2",fim, controle, lock, my_id))

'''Módulo de comunicação P2P'''
p2p_ = Process(target=p2p_module, args=("3",fim, lock, str(my_id)))

quart_.start();
telethon_.start();
p2p_.start();

'''Espera o usuário decidir encerrar a aplicação'''
input("=============\nAperte enter para encerrar:\n=============");
print("=============\nEncerrando aplicação, por favor, aguarde\n=============")

quart_.kill();
fim.value = 1;

quart_.join();
telethon_.join();
p2p_.join();
```
É importante notar que esses módulos não trocam informações diretamente, mas sim, por intermédio de duas bases de dados: ```vizinhos.db``` e ```chats.db```, conforme a figura 2:

<p align="center">
  <img width="600" height="300" src="https://github.com/joaopedrolourencoaffonso/Chimera-chat/blob/main/figuras_chimera/funcionamento-geral.png?raw=true" alt="Figura 2 - Esquema de interação entre os diferentes processos e bases de dados.">
</p>
<p align="center">
	Figura 2 - Esquema de interação entre os diferentes processos e bases de dados.
</p>

### Interface Gráfica
Conforme explicado anteriormente, o objetivo do presente projeto é criar uma "prova de conceito" e não uma aplicação comercial, sendo assim, foi empregada uma abordagem minimalista para a implementação da mesma, conforme exposto nas figura 3 e 4:
<p align="center">
  <img width="600" height="300" src="https://github.com/joaopedrolourencoaffonso/Chimera-chat/blob/main/figuras_chimera/tela-de-inicio.png?raw=true" alt="Figura 3 - Página principal da Aplicação">
</p>
<p align="center">
	Figura 3 - Página principal da Aplicação
</p>
<p align="center">
  <img width="600" height="300" src="https://github.com/joaopedrolourencoaffonso/Chimera-chat/blob/main/figuras_chimera/exemplo-de-dialogo.png?raw=true" alt="Figura 4 - Página de diálogo">
</p>
<p align="center">
	Figura 4 - Página de diálogo
</p>

Quando um usuário escreve uma mensagem e clica em: "enviar" ou "enviar arquivo", o texto escrito por ele é enviado por [websocket](https://datatracker.ietf.org/doc/html/rfc6455) para o módulo da interface gráfica. O módulo então busca o id de usuário do destinatário da mensagem na ```tabela_de_vizinhos``` da base de dados ```vizinhos.db``` e dependendo do resultado, a mensagem é salva na tabela: ```mensagens_para_enviar``` da base de dados ```chats.db``` com o valor de "marcador" igual à:
- "0" caso o destinatário não esteja na rede e a mensagem seja de texto
- "1 "caso o destinatário esteja na rede e a mensagem seja de texto
- "2" caso o destinatário não esteja na rede e a mensagem seja um arquivo
- "3" caso o destinatário esteja na rede e a mensagem seja um arquivo

Ao mesmo tempo, no caso de uma mensagem marcada como "não lida" (sent_ == 1) for adicionada a "tabela_de_mensagens" da "chats.db", a mesma será enviada por websocket para o navegador web e a "tabela_de_mensagens" da "chats.db" será editada para que a mensagem seja marcada como "lida" (sent_ == 0).

### Comunicação Ponto a Ponto
#### O Protocolo de Anúncio/Descoberta
O principal objetivo do Chimera é servir como uma aplicação de chat capaz de decidir quando entrar em contato por meio do P2P e quando utilizar o servidor do Telegram. Para isso, foi implementado um protocolo conforme o descrito a seguir:
- Ao iniciar a aplicação, três threads são lançadas "enviar", "receber" e "cleaner".
- A thread ```enviar``` se conecta a porta 50051 e envia mensagens UDP para o endereço de broadcast da rede local em intervalos de 5 segundos com a porta de destino sendo a 50050. Essas mensagens são formadas pela concatenação da string: "1:" com o id do Telegram do usuário.
- A thread ```cleaner``` se conecta a base de dados ```vizinhos.db``` e a cada 1 minuto lança uma query para eliminar da mesma qualquer entrada mais antiga que 1 minuto.
- A thread ```receber``` se conecta a porta 50050 e escuta pacotes de anúncio. No caso de recebimento de um anúncio, a thread ```receber``` lança a thread ```base_de_dados``` a qual verifica se a mensagem é válida e caso positivo, armazena a hora de recebimento, o endereço IP de origem e o ID do Telegram anúnciado na ```vizinhos.db```.

#### Protocolo de Transferência de Informações
Quando a aplicação é iniciada, duas threads são lançadas pelo módulo de comunicação ponto a ponto. A thread ```enviar_msg```, a qual age do lado cliente/remetente, e a thread ```recebe_conexao_ssl```, a qual age do lado servidor/destinatário. 

A thread ```enviar_msg``` passa maior parte do tempo "dormindo" e verificando a tabela ```mensagens_para_enviar``` da base de dados ```chats.db``` em busca de mensagens marcadas como "1" (mensagem de texto) ou "3" (transferência de arquivo). Caso uma ou mais mensagens seja(m) encontrada(s), estas são armazenadas em um vetor sobre o qual a thread itera efetivando o procedimento de conexão, conforme descrito abaixo:
- **Do lado remetente**, a thread ```enviar_msg``` busca o endereço IP correspondente a um determinado ID do Telegram na tabela "tabela_de_vizinhos" da base de dados ```vizinhos.db``` e o(s) resultado(s) é(são) armazenado(s) em um vetor.
- **Do lado remetente**, a thread ```enviar_msg``` itera sobre o vetor e estabelece conexão com cada endereço IP na porta 50052.
- **Do lado destinatário**, a thread ```recebe_conexao_ssl``` a qual está conectada à porta 50052, recebe a requisião de conexão e autentica o certificado do remetente. Caso este seja inválido, uma exceção é levantada, caso contrário, a thread ```recebimento_individual``` é iniciada e recebe o enlace, enquanto a thread ```recebe_conexao_ssl``` volta  a escutar a porta 50052.
- **Do lado remetente**, a thread ```enviar_msg``` autentica o certificado do destinatário e verifica se seu common name é o mesmo que o anúnciado (i.e. o valor armazenado na base de dados ```vizinhos.db```). Caso positivo, a conexão persiste, caso negativo, a conexão é encerrada e uma mensagem de erro é enviada ao usuário remetente.
- **Do lado destinatário**, a thread ```recebimento_individual``` verifica o "common name" do certificado do remetente da conexão e armazena o mesmo em uma variável a qual é usada para registrar o nome do remetente da mensagem na tabela:  ```tabela_de_mensagens``` da base de dados: ```vizinhos.db``` e verifica-se se a conexão é do tipo "1" ou "3", com procedimentos especiais para cada caso.
- **Do lado destinatário**, uma vez terminada a transferência de informações, a conexão e a thread ```recebimento_individual``` são encerradas.
- **Do lado remetente**, uma vez terminada a transferência de informações, a thread segue para o próximo elemento do vetor de destinatários, caso não haja mais elementos, a thread segue para o próximo elemento do vetor de mensagens, caso este também tenha se encerrado, a thread volta para o início.

Nota: Caso alguma exceção seja levantada ao longo do processo (seja por problemas de comunicação ou não) a conexão é encerrada e a base de dados do lado remetente é editada para que o marcador da mensagem em questão seja editado para "0" (mensagem de texto) ou "2" (arquivo), os quais indicam que a mensagem deve ser enviada pelo Telegram.

### Telegram
O módulo de interação com o Telegram se utiliza da biblioteca [Telethon](https://telethonn.readthedocs.io/en/latest/), sendo baseada em uma corrotina assíncrona e dois "event_handler":

- **enviar**: Corrotina responsável por checar a tabela: ```mensagens_para_enviar``` na base de dados ```chats.db``` em intervalos de 0.1 segundos e no caso de encontrar uma mensagem marcada como "0" ou "2", inicia o processo de envio para o Telegram.
- **receber**: É o "event_handler" responsável por filtrar as atualizações recebidas do Telegram em busca de eventos do tipo "novas mensagens" (```UpdateNewMessage```), salvando mensagens de texto diretamente na ```tabela_de_mensagens``` da ```chats.db``` enquanto que, no caso de arquivos, estes serão salvos no diretório correspondente ("imagens_chimera" ou "arquivos_chimera") e o caminho absoluto para o mesmo será salvo na ```tabela_de_mensagens``` da ```chats.db```.
- **delete_and_edit**: É o "event_handler" ligado a editar a base de dados retroativamente, sendo capaz de editar e deletar mensagens da "tabela_de_mensagens" da "chats.db", porém, não é capaz de excluir os arquivos em si.

## Usando a Aplicação
### Help
Uma vez dentro do ambiente virtual, podemos obter informações sobre qualquer comando usando o comando ```--help```, conforme abaixo:
```bash
C:\seu_path\diretorio> chimera.py --help
usage: chimera.py [-h] [--install] [--new] [--renew] [--revoke] [--variables]

Chimera, software de chat para p2p over LAN e Telegram

optional arguments:
  -h, --help   show this help message and exit
  --install    Primeira Instalação do Chimera
  --new        Obter novo certificado
  --renew      Renovar certificado
  --revoke     Revogar certificado
  --variables  Criar arquivo com variáveis
```

### Cadastrando variáveis
Para o Chimera funcionar tanto como mensageiro sobre LAN quanto como proxy transparente do Telegram, se faz necessário que o client introduza as variáveis arbitrárias, são estas:

- ```api_id``` e ```api_hash```: Para criar uma aplicação do Telegram, é necessário um id e um hash de usuário que podem ser obtidos na [página oficial](https://my.telegram.org/auth) do Telegram. O Telegram dá o direito de uma aplicação por conta, sendo assim, basta acessar a página, cadastrar uma aplicação e o próprio site já fornecerá os valores necessários
- IP e Porta da step-ca: Corresponde ao IP e a porta no qual a step-ca está operando.
- IP e Porta do Provedor de Identidade: Corresponde ao IP e a porta no qual o provedor de identidade ([chimera_identity.py](https://github.com/joaopedrolourencoaffonso/Chimera-chat/tree/main/Provedor_de_identidade)) está operando.
- Endereço de Broadcast da rede: Autoexplicativo.

Para o cadastro, basta executar o comando conforme o exemplo abaixo:

```bash
C:\seu_path\diretorio> chimera.py --variables
Digite sua api_id do Telegram:
-->12345678
Digite sua api_hash do Telegram:
-->suahashdotelegramvaiaqui
Digite o endereço da step-ca no formato -- IP:port
-->192.168.0.155:8443
Digite o endereço do registration no formato -- IP:port
-->192.168.0.155:8000
Digite o endereço de broadcast
-->192.168.0.255
```

### Instalação
Para efetivamente fazer download dos diálogos e obter um certificado assinado, basta usar o comando ```--install``` e seguir as instruções conforme o exemplo abaixo:
```bash
C:\seu_path\diretorio> chimera.py --install
Iniciando: primeira_instalacao
=======Tabelas criadas=======
Please enter your phone (or bot token): 5502199999999
Please enter the code you received: 83389
Signed in successfully as (seu nome)

-----TABELA DE DIALOGOS INDIVIDUAIS CRIADA--------

====Download de diálogo feito com sucesso====

====Download de diálogo feito com sucesso====
...
======= Download dos diálogos finalizados com sucesso! =======
Escreva o número que você recebeu no Telegram: 12426
======
Private Key generated
======
======
Requisição de assinatura gerada com sucesso
======

-----
 {"csr": "-----BEGIN CERTIFICATE REQUEST-----\nMIIEoj...j73WL/k=\n-----END CERTIFICATE REQUEST-----\n", "ott": "eyJhbGciOi....zkCBei1STEpA\n"}
 
-----Resposta------
 {"crt":"-----BEGIN CERTIFICATE-----\nMIID+z..."minVersion":1.2,"maxVersion":1.3,"renegotiation":false}}
 
----Seu certificado----
 -----BEGIN CERTIFICATE-----
MIID+zCCA6GgAwIBAgIQFaxCwvkRB5XsF8Q875x4EzAKBggqhkjOPQQDAjA4MRIw
EAYDVQQKEwlqb2FvcGVkcm8xIjAgBgNVBAMTGWpvYW9wZWRybyBJbnRlcm1lZGlh
...
xKFGmVcyJsUtyI9mx6kmLpvEFsP0cEqGrcEKUk20pOM=
-----END CERTIFICATE-----

----
=========Novo certificado baixado com sucesso!==========
 ----
fim
```

### Renovando Certificado
O ```chimera.py``` é capaz de atualizar seu certificado sozinho antes de iniciar a operar, no entanto, as vezes pode ser conveniente atualizar o certificado manualmente, para isso, basta utilizar a função ```--renew```:
```bash
C:\seu_path\diretorio> chimera.py --renew
Iniciando: renovar_certificado
=======
Certificado renovado com sucesso!
=======
```

### Revogando Certificado
Apesar do Chimera ser voltado para conexões em LANs, ainda é possível que um usuário maliciosa, sendo assim necessário cadastrar um novo certificado. Para esse cenário, é preciso, primeiramente revogar o certificado antigo, o que pode ser atingido utilizando a ```--revoke```:
```bash
C:\seu_path\diretorio> chimera.py --revoke
Iniciando: revogar_certificado
1836713877
Qual o motivo?
0 - Unspecified
1 - KeyCompromise
2 - CACompromise
3 - AffiliationChanged
4 - Superseded
5 - CessationOfOperation
6 - CertificateHold
8 - RemoveFromCRL
9 - PrivilegeWithdrawn
10 - AACompromise
--> 1
Observação:
-->Laptop foi roubado
{'status': 'ok'}
=======
Certificado revogado com sucesso!
=======
```
Se você tentar renovar o mesmo certificado novamente, obterá:
```bash
chimera.py --renew
Iniciando: renovar_certificado
=======Desculpe, mas houve um erro=======

'crt'
```
### Obtendo Novo Certificado
Seja por descuido do usuário ou ação maliciosa, as vezes pode ser necessário obter um novo certificado do zero. Para isso, basta usar a função ```--new```:
```bash
C:\seu_path\diretorio> chimera.py --new
Escreva o número que você recebeu no Telegram: 43852
======
Private Key generated
======
======
Requisição de assinatura gerada com sucesso
======

-----
 {"csr": "-----BEGIN CERTIFICATE REQUEST-----\nMIIEojCC...
 ................kmLpvEFsP0cEqGrcEKUk20pOM=
-----END CERTIFICATE-----
```
### Inicializando
Finalmente, para iniciar a aplicação, basta usar o comando:
```bash
C:\seu_path\diretorio> chimera.py

Atualizando base de dados, aguarde.
=============
Aperte enter para encerrar:
============= * Serving Quart app '__mp_main__'
 * Environment: production
 * Please use an ASGI server (e.g. Hypercorn) directly in production
 * Debug mode: False
 * Running on http://127.0.0.1:5000 (CTRL + C to quit)
 ```
 Basta agora acessar o endereço: http://localhost:5000/ para utilizar a aplicação.
 Conforme descrito acima, para encerrar a aplicação a qualquer momento, basta voltar a linha de comando e apertar "Enter" que a aplicação se encerrará sozinha.

## Próximos Passos
O chimera em sua forma atual é capaz de fazer download de exportar conversas para o formato de base de dados SQLite, trocar mensagens localmente e transferir arquivos de maneira segura e nossos testes mostram que a utilização do chimera leva a economia do uso de dados, velocidades de transferência mais rápida e maior controle sobre os dados, no entanto, o sistema não é perfeito e ainda existem certos objetivos a serem alcançados. No curto prazo, visamos os seguintes objetivos:

- **Resistência a falhas**: Apesar da versão atual já ser capaz de se recuperar dos problemas de rede e execução mais comuns, ainda há muitas variáveis e vulnerabilidades no script atual. 
-  **API do Telegram**: Apesar do Chimera ser capaz de receber atualizações e editar a "chats.db" de acordo, existem certas limitações relacionadas ao fato de que a API do Telegram foi projetada para o armazenamento dos dados em nuvem, não em bases de dados locais. Um deles inclui o fato de que mensagens são deletadas com base em seu id, não no diálogo, como resultado, quando um usuário deleta um diálogo de suas conversas o Chimera irá deletar as mensagens da ```tabela_de_mensagens``` mas não irá deletar o id do diálogo da ```tabela_de_dialogos```, sendo necessário reiniciar a aplicação para registrar a mudança. Outra falha inclui o fato de que, em seu formato atual, o Chimera ainda não é capaz de suportar as "**Sponsored Messages**", recentemente implementadas, sendo o suporte a estas uma das nossas principais prioridades no momento.
-  **Interface gráfica melhorada**: Atualmente a interface gráfica empregada é muito limitada, não sendo capaz de oferer opções como edição de mensagem, deleção de mensagem ou pré-visualização de arquivos, o principal motivo disso é a dificuldade no uso de websockets combinado com múltiplos processos paralelos que se comunicam apenas pela base de dados. Uma alternativa seria a utilização de pipes e do Tkinter para oferecer uma UI mais maleável e atraente ao usuário enquanto que facilitando a implementação de novas funcionalidades.
-  **Mensagens mais antigas**: Pelos mesmos motivos que enumerados acima, o Chimera não é capaz de expor mensagens anteriores a sua instalação (com exceção das dez últimas mensagens trocadas em cada diálogo do Telegram imediatamente antes da instalação). A óbvia inconveniência gerada é um dos principais problemas que objetivamos resolver.
-  **Provedor de Identidade Aperfeiçoado**: Conforme comentado anteriormente, o provedor de identidade aqui proposto é voltado para um público com conhecimento técnico, porém, isso não é inteiramente necessário, sendo assim possível e preferível a construção de aplicações para facilitar a utilização do ```registration.py``` por usuários leigos.
-  **Modo 'insecure'**: Nem todas as pessoas tem interesse ou necessidade do nível de segurança aqui proposto, por isso, seria interessante a implementação de um modo 'inseguro' a comunicação por LAN fosse feita sem a necessidade de certificados SSL, o que pode ser útil em dadas situações.
-  **Multiusuário**: Em seu modelo atual, o Chimera só pode ser utilizado por um único usuário por instalação. É claro, é possível criar dois diretórios, copiar e colar dois scripts em cada um deles e usar duas instâncias diferentes, mas isso não é prático nem amigável ao usuário, sendo assim, mais recomendável a criação da opção de múltiplos usuários usarem a mesma instância do Chimera, oferecendo a opção de logar o usuário ao iniciar.
-  **Servidor Chimera**: Apesar do Telegram oferecer uma API simples e eficiente, seria interessante o desenvolvimento de um servidor específico para as necessidades do Chimera, de tal forma 

## Conclusões
Apesar de não serem tão famosos quanto os aplicativos convencionáis, aplicações de chat em LAN são mais [comuns](https://www.thewindowsclub.com/lan-messengers-free-download-windows) e mais [demandadas](https://www.reddit.com/r/Telegram/comments/mfiwqz/if_telegram_enables_lan_chat_and_file_sharing/) do que muitos podem imaginar. Também é preciso imaginar os usos alternativos para um protocolo de comunicação por LAN sem a necessidade de servidores, como comunicação em caso de [emergêcia](https://ieeexplore.ieee.org/document/8690351) ou [descoberta de serviços](https://ieeexplore.ieee.org/document/8436832).

Dessa forma, as vantagens da adoção de um sistema de mensageiro híbrido entre a comunicação ponto a ponto e o cliente-servidor se tornam autoevidentes, sendo uma forma simples porém eficaz de reduzir o consumo de dados, aumentar a privacidade da comunicação, oferecer comunicação de emergência e fornecer aos usuários e organizações maior controle sobre suas comunicações sem as desvantagens de protocolos baseados em querys ou ter que confiar em organizações externas.

Agradecemos a atenção.


### Observações

O Chimera é uma aplicação *protótipo* ainda em *desenvolvimento* com o propósito de ilustrar os benefícios de uma arquitetura híbrida entre os modelos cliente-servidor e P2P. Sendo assim, apesar de termos o objetivo de deixar o código o mais próximo de uma aplicação real possível, nem todas as funcionalidades do Telegram serão disponibilizadas. Caso o leitor deseje utilizar o Chimera como base para sua própria aplicação, é recomendável que o mesmo se atenha aos [termos de serviço](https://core.telegram.org/api/terms), a [política de privacidade](https://telegram.org/privacy/br) e a [guia da API](https://core.telegram.org/api) do Telegram.

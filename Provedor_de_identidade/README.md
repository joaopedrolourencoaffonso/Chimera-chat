# Provedor de Identidade
Apesar da praticidade do uso de certificados digitais, estes, por si só, somente são capazes de prover criptografia, uma vez que um certificado é tão seguro quanto a autoridade que o emitiu. Sendo assim, faz-se necessário a utilização de **provedores de identidade**, formas de verificar que a pessoa requisitando um dado certificado é quem diz ser. Na internet, o teste mais comum é a verificação de controle sobre um dado domínio, porém, como o presente projeto é baseado em endereços IPs dinâmicos, tal solução não é praticável. 

Para solucionar tal problema foi desenvolvido o ```chimera_identity.py```, um sistema baseado no framework [Quart](https://pgjones.gitlab.io/quart/), [Telethon](https://telethonn.readthedocs.io/en/latest/) e o cliente step-ca [step-cli](https://smallstep.com/docs/step-cli) capaz de verificar se o autor de uma determinada requisição tem controle sobre a conta Telegram para a qual está requisitando o certificado.

## Casos de Uso
É interessante destacar que um provedor de identidade automatizado nem sempre é necessário. Para o caso de equipes relativamente pequenas, é possível  delegar a função a um funcionário (do TI por exemplo) que apenas teria que renovar os certificados de dias em dias. O procedimento em si poderia ser facilmente automatizado por SSH, e-mail ou script. Sendo assim, o uso de um provedor de identidade é apenas recomendável para situações em que o número de usuários seja relativamente elevado.

## Instalação
### Requisições
Para funcionar corretamente, o ```chimera_identity.py``` precisa ter o seguintes softwares instalados no sistema:
- Quart 0.16.3
- Telethon 1.24.0
- step-cli 0.17.5
- mySQL 8.0.28-0ubuntu0.20.04.3

Chama-se para o fato de que apesar de ser possível utilizar o step-cli em uma [máquina diferente](https://smallstep.com/docs/step-cli/reference/ca) da máquina que o ```chimera_identity.py``` está operando, é recomendável que os dois estejam na mesma máquina, como forma de aumentar a velocidade do processo.

### SSL
Para a correta operação do ```chimera_identity.py``` são necessários pelo menos outros três arquivos:

- ```ca_bundle.pem```: Bundle de certificados da autoridade certificadora. Pode ser obtido copiando e colando os certificados da intermediate_ca e root_ca da step-ca.
- ```quart_key.pem```: Chave privada da API do provedor de identidade, **diferente** da chave utilizada para assinar os certificados, sendo utilizada para prover criptografia para as APIs. Pode ser obtida através do próprio comando ```step``` ou pelo OpenSSL.
- ```quart_cert.pem```: Certificado SSL assinado pela step-ca e obtido a partir de CSR gerado a partir da ```quart_key.pem```.

### mySQL
Para configurar a base de dados, é primeiramente necessário criar um usuário chamado "registration":
```SQL
CREATE USER 'registration'@'localhost' IDENTIFIED BY 'senha';

GRANT ALL PRIVILEGES ON * . * TO 'registration'@'localhost';

FLUSH privileges;

commit;
```
Assim como uma base de dados homônima:
```SQL
create database registration;
```
Acessando a base de dados, basta agora criar uma table chamada de "temp_token":
```SQL
create table temp_token (number text, token int, hour datetime);
```
### variables.py
Em um diretório arbitrário, crie um arquivo denominado: ```variables.py``` e salve nele a ```api_id``` e ```api_hash``` obtidas do [Telegram](https://my.telegram.org/auth).

### Configurando o chimera_identity.py

Finalizados os passos anteriores, basta agora acessar o arquivo ```chimera_identity.py``` e editar os seguintes campos:

```python
sys.path.insert(2, "/path_to_your_variables")#coloque o path para o diretório no qual foi salvo o arquivo variables.py
...
mydb = mysql.connector.connect(
  host="localhost",       # endereço IP da base de dados
  user="registration",    # nome do usuário criado
  password="senha",       # senha para acesso à base de dados 
  database="registration" # nome da base de dados a ser acessada
);
...
config.bind = ["0.0.0.0:8000"]                   # endereço IP e porta na qual se deseja que a API opere
config.certfile = "/path_to_yourt_quart_crt.pem" # path para o certificado SSL "quart_crt.pem"
config.keyfile = "/path_to_yourt_quart_key.pem"  # path para chave privada da API, "quart_key.pem"
config.ciphers = "ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256" # edição opcional, caso se deseje aumentar ou diminuir o nível de segurança
```
### cleaner.py
O ```cleaner.py``` é o script de suporte responsável por acessar a base de dados e excluir todas as entradas mais antigas que cinco minutos (tempo de vida máximo de um token). É recomendável que o mesmo seja salvo no mesmo diretório que o chimera_identity.py e que sua execução seja agendada na crontab com intervalos de 1 à 4 minutos.

### Inicialização

Quando ```chimera_identity.py``` é iniciado, o script imediatamente renova o ```quart_crt.pem``` lançando uma exceção e encerrando sua própria execução caso não funcione, caso funcione o módulo referente ao Quart é iniciado e as APIs ficam disponíveis.

## Funcionamento

O ```chimera_identity.py``` é baseado em três APIs que não interagem diretamente entre si, mas agem como um "portão" para o acesso a step-ca.

###  /registration

Requisições para esse endpoint devem ser enviadas no formato json: ```{'number':"id_da_conta_do_telegram"}``` com o método "POST", em caso contrário, um mensagem de erro é retornada ao usuário.

Caso a requisição seja válida, a aplicação checa a tabela ```temp_token``` da base de dados ```registration``` e verifica se já há um token associado ao id do Telegram, caso positivo, uma mensagem de erro é retornada ao usuário, caso negativo, um token aleatório de cinco dígitos é gerado e enviado ao usuário através do Telegram. Feito isso, o token é então armazenado na tabela ```temp_token``` juntamente com o id do Telegram da conta para qual foi enviado e o prazo de validade, cinco minutos a frente do momento atual.

###  /send_token

Requisições para esse endpoint devem ser enviadas no formato: ```{'number':"id_da_conta_do_telegram",'token':"token_de_cinco_digitos_enviado_pelo_telegram"}```, com o método POST.

Caso a requisição seja válida, a aplicação verifica se existe uma entrada na base de dados contendo o token e o número de conta enviados que ainda esteja dentro do prazo de validade. Caso alguma dessas condições não seja atendida, uma mensagem de erro é enviado ao usuário e este precisa esperar alguns minutos antes de pedir outro token. Caso haja uma entrada que atenda a todas essas condições, a entrada é excluída da tabela e um token jwt é gerado com base na chave privada do provedor de identidade e enviado para o usuário.

###  /revoke_token

Par os casos em que o usuário decida revogar um certificado, basta fazer uma requisição para esse endpoint no formato: ```{'number':"id_da_conta_do_telegram"}``` que o endpoint automaticamente irá gerar um jwt para revogação de certificado e enviará para o usuário. 

O motivo para ausência de outros mecanismos de checagem é que a step-ca já implementa o mTLS, significando que, mesmo com um token jwt, o usuário não será capaz de revogar um certificado sem ter a chave privada referente ao mesmo.

## Fluxos

O fluxo bem sucedido para obtenção de um certificado SSL novo pode ser melhor compreendido na figura 1.
<p align="center">
  <img width="600" height="420" src="https://github.com/joaopedrolourencoaffonso/Chimera-chat/blob/main/figuras_chimera/obtencao-de-certificado.png?raw=true" alt="Figura 1 - Fluxo para obtenção de um novo certificado">
</p>
<p align="center">
	Figura 1 - Fluxo para obtenção de um novo certificado
</p>
Caso haja uma falha por erro do usuário, ação maliciosa ou problemas do servidor, o fluxo acima é interrompido e uma mensagem de erro é enviada para o usuário.

Já o fluxo de renovação de certificado é relativamente mais simples, sendo apenas necessário que o usuário esteja de posse da chave privada do seu certificado e este não esteja expirado (revogação passiva):
<p align="center">
<img width="600" height="420" src="https://github.com/joaopedrolourencoaffonso/Chimera-chat/blob/main/figuras_chimera/fluxo-renovacao-certificado.png?raw=true" alt="Figura 2 - Fluxo para renvação do certificado">
</p>
<p align="center">
	Figura 2 - Fluxo para renovação do certificado
</p>

Por fim, para revogar um certificado, o usuário precisa primeiro obter um token jwt para revogação e então realizar uma requisição POST com mTLS para a step-ca conforme a figura abaixo:

<p align="center">
<img width="600" height="420" src="https://github.com/joaopedrolourencoaffonso/Chimera-chat/blob/main/figuras_chimera/revogacao-de-certificado.png?raw=true" alt="Figura 3 - Fluxo para revogação do certificado">
</p>
<p align="center">
	Figura 3 - Fluxo para revogação do certificado
</p>

## A Smallstep

É necessário destacar que esse projeto não seria possível sem o [apoio](https://github.com/smallstep/certificates/discussions/734) da equipe da [Smallstep](https://smallstep.com/about/) companhia criadora da step-ca e step-cli. A ajuda deles foi fundamental para construção da aplicação assim como melhor compreensão de vários conceitos nem tão simples. Sendo assim, não seria possível encerrar uma discussão sobre o chimera_indentity sem citar a alta qualidade dos produtos e serviços da Smallstep sendo extremamente recomendável para projetos que busquem criar um ambiente de PKI saudável e organizado.

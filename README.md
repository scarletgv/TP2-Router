# TP2-Router
Implementação de um protocolo de roteamento por vetor de distâncias.

## Execução

Para cada roteador, nos endereços 127.0.1.1 a 127.0.1.16:

```
./router.py <Endereço IP> <Tempo de update> [Arquivo de Inicialização]
```
Arquivo de inicialização opcional, com comandos para criar a topologia da rede. Tempo de update é o tempo em segundos para cada envio de mensagem de update do roteador para seus vizinhos.

# Uptime Notifier — Notificações Profissionais para Uptime Kuma

Serviço intermediário que recebe webhooks do Uptime Kuma e envia mensagens formatadas para o Telegram.

---

## Por que usar?

O Uptime Kuma envia notificações com o output técnico bruto do ping:

```
[RB - VILLEFIBRA] [🔴 Down] PING 168.181.111.128 56(84) bytes of data.
10 packets transmitted, 0 received, 100% packet loss
```

Com o Uptime Notifier, a mensagem chega assim:

```
🔴 ALERTA DE QUEDA

📍 Monitor: RB - VILLEFIBRA
🌐 Host: 168.181.111.128
📊 Status: OFFLINE
📅 19/04/2026 às 18:05

━━━━━━━━━━━━━━━
⚡ Monitoramento Automático
```

---

## Estrutura de arquivos

```
uptime-notifier/
├── app.py              # Aplicação Flask (webhook receiver)
├── channels.json       # Configuração dos canais Telegram
├── requirements.txt    # Dependências Python
├── Dockerfile          # Imagem Docker
└── docker-compose.yml  # Orquestração
```

---

## Como instalar em um novo host

### Pré-requisitos

- Docker e Docker Compose instalados
- Uptime Kuma já rodando em Docker
- Bot(s) do Telegram criados via @BotFather

### Passo 1 — Copiar os arquivos

Copie a pasta `uptime-notifier/` para o servidor:

```bash
scp -r uptime-notifier/ usuario@IP_DO_SERVIDOR:/home/usuario/
```

Ou clone direto no servidor se estiver em um repositório Git:

```bash
git clone <repo> uptime-notifier
```

### Passo 2 — Configurar os canais

Edite o arquivo `channels.json` com os dados de cada cliente:

```json
{
  "nome-do-canal": {
    "bot_token": "TOKEN_DO_BOT",
    "chat_id": "ID_DO_GRUPO",
    "protect_content": true
  }
}
```

| Campo            | Descrição                                      |
|------------------|------------------------------------------------|
| `nome-do-canal`  | Nome usado na URL do webhook (sem espaços)     |
| `bot_token`      | Token do bot obtido no @BotFather              |
| `chat_id`        | ID do grupo/canal (negativo para grupos)       |
| `protect_content`| `true` impede encaminhar a mensagem no Telegram|

**Como obter o chat_id de um grupo:**
1. Adicione o bot ao grupo
2. Envie uma mensagem no grupo
3. Acesse: `https://api.telegram.org/bot<TOKEN>/getUpdates`
4. Procure o campo `"chat": {"id": ...}`

### Passo 3 — Criar a rede Docker compartilhada

```bash
docker network create uptime-net
```

Conecte o container do Uptime Kuma à rede:

```bash
docker network connect uptime-net uptime-kuma
```

> Se o container do Uptime Kuma tiver outro nome, substitua `uptime-kuma` pelo nome correto.

### Passo 4 — Subir o serviço

```bash
cd uptime-notifier
docker compose up -d --build
```

Verifique se está rodando:

```bash
docker ps | grep uptime-notifier
curl http://localhost:5000/health
```

Resposta esperada: `{"status": "ok"}`

---

## Configurar o Uptime Kuma

Para cada monitor, você vai adicionar uma notificação do tipo **Webhook**:

1. No Uptime Kuma, vá em **Settings → Notifications → Add Notification**
2. Tipo: **Webhook**
3. URL: `http://uptime-notifier:5000/webhook/<nome-do-canal>`
4. Method: **POST**
5. Salve e associe ao monitor desejado

### Exemplos de URLs

| Canal             | URL do Webhook                                      |
|-------------------|-----------------------------------------------------|
| tellenet          | `http://uptime-notifier:5000/webhook/tellenet`      |
| def-telecom       | `http://uptime-notifier:5000/webhook/def-telecom`   |
| buritinet         | `http://uptime-notifier:5000/webhook/buritinet`     |
| ville-jao         | `http://uptime-notifier:5000/webhook/ville-jao`     |

> A URL usa o nome do container `uptime-notifier` porque ambos estão na mesma rede Docker (`uptime-net`).

---

## Testar manualmente

Simule um alerta de queda:

```bash
curl -X POST http://localhost:5000/webhook/<nome-do-canal> \
  -H "Content-Type: application/json" \
  -d '{
    "heartbeat": {
      "status": 0,
      "time": "2026-04-19T21:00:00.000Z",
      "ping": -1,
      "important": true
    },
    "monitor": {
      "name": "NOME DO MONITOR",
      "hostname": "IP_OU_HOST",
      "type": "ping"
    }
  }'
```

Simule recuperação (status `1`):

```bash
curl -X POST http://localhost:5000/webhook/<nome-do-canal> \
  -H "Content-Type: application/json" \
  -d '{
    "heartbeat": {
      "status": 1,
      "time": "2026-04-19T21:10:00.000Z",
      "ping": 15,
      "important": true
    },
    "monitor": {
      "name": "NOME DO MONITOR",
      "hostname": "IP_OU_HOST",
      "type": "ping"
    }
  }'
```

---

## Adicionar um novo canal

1. Edite o `channels.json` e adicione a entrada
2. Reinicie o serviço:

```bash
docker restart uptime-notifier
```

Não é necessário rebuildar a imagem — o `channels.json` é montado como volume.

---

## Ver logs

```bash
docker logs uptime-notifier -f
```

---

## Atualizar o serviço

Após alterar o `app.py`:

```bash
cd uptime-notifier
docker compose up -d --build
```

---

## Formato das mensagens

### Queda (status = 0)

```
🔴 ALERTA DE QUEDA

📍 Monitor: <nome>
🌐 Host: <hostname>
📊 Status: OFFLINE
📅 <data> às <hora>

━━━━━━━━━━━━━━━
⚡ Monitoramento Automático
```

### Recuperação (status = 1)

```
✅ SERVIÇO RECUPERADO

📍 Monitor: <nome>
🌐 Host: <hostname>
📊 Status: ONLINE
⏱ Latência: <ping>ms
📅 <data> às <hora>

━━━━━━━━━━━━━━━
⚡ Monitoramento Automático
```

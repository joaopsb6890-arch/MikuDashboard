# 🎤 Miku-Dashboard

Painel web para controlar o **Hatsune Miku Bot** no teu servidor do Discord:
boas-vindas, verificação, contadores, anúncios, lembretes, moderação, rankings e logs.

> ✨ **Novidade:** o bot agora **reconhece-se sozinho**. Não precisas de escrever
> a "URL da API" nem o "token do painel". Basta preencher as informações do
> **Discord Developer Portal** no ficheiro `.env` e correr o bot. O painel abre
> já ligado.

---

## 🧠 Como funciona (a ideia)

Antes, o painel era só o *frontend* e precisavas de o "ativar" escrevendo a URL
e o token do bot. Agora o próprio bot faz tudo:

```
        ┌─────────────────────────────────────────────┐
        │            python -m bot.main               │
        │                                             │
        │   ┌───────────────┐     ┌────────────────┐   │
        │   │  Bot Discord  │     │  Servidor Web  │   │
        │   │ (discord.py)  │◄───►│  (aiohttp)     │   │
        │   └───────┬───────┘     └───────┬────────┘   │
        └───────────┼─────────────────────┼────────────┘
                    │                     │
             Discord Gateway        Painel + API (/api/*)
                    │                     │
              🎶 Servidor            🌐 Navegador
```

* O **Bot Token** liga a Miku ao Discord.
* O **servidor web** serve o painel **e** a API no mesmo endereço.
* Ao servir o painel, injeta a URL (mesma origem) e o token → **auto-conexão**.

Resultado: abres `http://localhost:8787` e o painel já está ligado. 💙

---

## 🚀 Começar (5 minutos)

### 1. Criar/abrir a aplicação no Discord Developer Portal
Vai a <https://discord.com/developers/applications> e abre a tua aplicação
(ou cria uma nova). Reúne estas informações:

| Onde | O que copiar | Para que serve |
|------|--------------|----------------|
| **General Information** | Application ID | Identificar o app |
| **General Information** | Public Key | Verificação |
| **Bot → Reset Token** | Bot Token | Ligar o bot ao Discord |
| **OAuth2** | Client ID | Login com Discord |
| **OAuth2** | Client Secret | OAuth2 |

### 2. Ligar os Intents (importante!)
Em **Bot → Privileged Gateway Intents**, liga:
* ✅ **Server Members Intent** (boas-vindas e contagem de membros)
* ✅ **Message Content Intent** (níveis/XP e comandos)

### 3. Configurar o `.env`
```bash
cd bot
cp .env.example .env
# abre o .env e cola as tuas credenciais
```

### 4. Instalar e correr
```bash
pip install -r bot/requirements.txt
python -m bot.main
```

Vais ver no terminal algo assim:

```
  🎤  HATSUNE MIKU BOT — Painel + API + Discord
  Application ID : 1551238667492790352
  Bot Token      : definida
  Token do painel: xxxxxxxxxxxxxxxxxxxxxxxx
  Auto-conectar  : True
  🌐 Abre o painel em:  http://localhost:8787
```

### 5. Abrir o painel
Abre <http://localhost:8787> — **já está ligado**. 🎉

---

## 🤖 Convidar o bot para o servidor

No Developer Portal → **OAuth2 → URL Generator**:
* Scopes: `bot`, `applications.commands`
* Bot Permissions: `Manage Roles`, `Manage Channels`, `Manage Messages`,
  `Send Messages`, `Embed Links`, `Read Message History`, `View Channels`

Copia o URL gerado e abre-o para adicionar a Miku ao teu servidor.

---

## 💬 Comandos de chat (prefixo `!`)

| Comando | Descrição |
|---------|-----------|
| `!anunciar Título \| Texto` | Envia um anúncio em embed |
| `!lembrar 30 Texto` | Lembra-te daqui a 30 minutos |
| `!limpar 20` | Apaga 20 mensagens |
| `!rank` | Mostra o teu nível/XP |
| `!daily` | Recompensa diária de moedas |
| `!saldo` | Mostra o teu saldo |

---

## ⚙️ O que cada informação do Developer Portal faz

| Variável | Usada para |
|----------|-----------|
| `DISCORD_APPLICATION_ID` | Identidade do app (e Client ID por omissão) |
| `DISCORD_PUBLIC_KEY` | Verificação de interações |
| `DISCORD_BOT_TOKEN` | **Ligar o bot ao Discord** |
| `DISCORD_CLIENT_ID` | Login com Discord no painel |
| `DISCORD_CLIENT_SECRET` | OAuth2 |

---

## 🌍 Pôr online (opcional)

O bot pode correr em qualquer serviço que suporte Python (Railway, Render,
Fly.io, uma VPS, etc.). Define as variáveis de ambiente do `.env` no painel do
serviço e corre `python -m bot.main`.

> 🔒 **Segurança:** quando expões o painel na internet, define um
> `DASHBOARD_TOKEN` forte no `.env`. Só quem tiver o token consegue controlar o bot.

---

## 🛠️ Resolução de problemas

| Problema | Solução |
|----------|---------|
| `Falta o DISCORD_BOT_TOKEN` | Preenche o `.env` (passo 3) |
| Bot não liga / erro de intents | Liga os Privileged Intents (passo 2) |
| Painel diz "Sem ligação" | Confirma que o bot está a correr e abre o endereço que ele mostra |
| Boas-vindas não aparecem | Define o canal no painel e confirma as permissões |

---

Feito com 💙 para a Miku.

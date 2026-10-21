# 🎤 Miku-Dashboard — Plano de trabalho

## Objetivo
Fazer o painel funcionar **sem precisar digitar URL/token manualmente** ("ativar pelo URL").
O bot deve ser reconhecido automaticamente usando as **informações do Discord Developer Portal**
(Application ID, Bot Token, Public Key, Client ID, Client Secret).

## Estratégia
O painel é só frontend. Para ele "reconhecer o bot" sozinho, o próprio bot passa a:
1. Correr o bot do Discord (discord.py) com o **Bot Token** do Developer Portal.
2. Servir a **API** que o painel consome (`/api/status`, `/api/guilds`, ...).
3. Servir o **próprio painel** no mesmo servidor (mesma origem) e **auto-conectar** (injeta URL+token).

## Tarefas
- [x] 1. Estrutura do backend do bot (`bot/`)
- [x] 2. `config.py` — lê as credenciais do Discord Developer (`.env`)
- [x] 3. `storage.py` — persistência (config, verificação, contadores, XP, economia, logs)
- [x] 4. `web.py` — servidor aiohttp (API + painel estático + auto-conexão)
- [x] 5. `bot.py` + cogs (boas-vindas, verificação, contadores, anúncios, lembretes, moderação, XP, economia)
- [x] 6. `main.py` — arranca bot + servidor juntos
- [x] 7. Atualizar `app.js`/`index.html` do painel para auto-conectar
- [x] 8. `requirements.txt`, `.env.example`, `.gitignore`, `README.md`
- [ ] 9. Testar localmente (servidor web + API)
- [ ] 10. Commit, push de branch e abrir Pull Request

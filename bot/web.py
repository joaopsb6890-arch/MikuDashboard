"""
🌐 web.py — servidor HTTP que junta o painel e a API do bot.

Responsabilidades:
  • Servir o painel (index.html, app.js, styles.css, imagens).
  • Servir a API que o painel consome (/api/status, /api/guilds, ...).
  • AUTO-CONECTAR o painel: ao servir o index.html injeta um <script> com
    a URL (mesma origem) e o token do painel, para o bot ser reconhecido
    automaticamente — sem o utilizador digitar nada.

Isto é o que faz o painel "funcionar sozinho" com as credenciais do
Discord Developer Portal.
"""

from __future__ import annotations

import asyncio
import json
import time

from aiohttp import web

import discord

from .config import Config, ROOT_DIR

MIMES = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".json": "application/json; charset=utf-8",
}


# ═══════════════════════════════════════════════════════════════════════════
#  helpers
# ═══════════════════════════════════════════════════════════════════════════

def _ok(**dados) -> web.Response:
    return web.json_response({"ok": True, **dados})


def _erro(mensagem: str, status: int = 400) -> web.Response:
    return web.json_response({"ok": False, "erro": mensagem}, status=status)


def _autorizado(request: web.Request) -> bool:
    token = Config.dashboard_token
    cabecalho = request.headers.get("Authorization", "")
    if cabecalho.startswith("Bearer "):
        return cabecalho[7:].strip() == token
    # aceita também ?token= (útil para testes rápidos)
    return request.query.get("token") == token


async def _corpo(request: web.Request) -> dict:
    if request.can_read_body:
        try:
            return await request.json()
        except (json.JSONDecodeError, ValueError):
            return {}
    return {}


def _canal(bot, channel_id):
    try:
        return bot.get_channel(int(channel_id))
    except (TypeError, ValueError):
        return None


def _guild(bot, guild_id):
    try:
        return bot.get_guild(int(guild_id))
    except (TypeError, ValueError):
        return None


# ═══════════════════════════════════════════════════════════════════════════
#  painel (estático + injeção de auto-conexão)
# ═══════════════════════════════════════════════════════════════════════════

async def servir_index(request: web.Request) -> web.Response:
    caminho = ROOT_DIR / "index.html"
    if not caminho.exists():
        return web.Response(status=404, text="index.html não encontrado")
    html = caminho.read_text(encoding="utf-8")

    boot = {
        "apiUrl": "",  # vazio → o painel usa a própria origem (window.location.host)
        "token": Config.dashboard_token,
        "clientId": Config.client_id,
        "autoConnect": Config.auto_connect,
    }
    injecao = (
        "<script>window.MIKU_BOOT = "
        + json.dumps(boot, ensure_ascii=False)
        + ";</script>\n"
    )
    # injeta antes do app.js para o painel já arrancar ligado
    if '<script src="./app.js"></script>' in html:
        html = html.replace(
            '<script src="./app.js"></script>',
            injecao + '    <script src="./app.js"></script>',
        )
    else:
        html = html.replace("</body>", injecao + "</body>")

    return web.Response(text=html, content_type="text/html", charset="utf-8")


async def servir_estatico(request: web.Request) -> web.Response:
    nome = request.match_info["ficheiro"]
    # impede path traversal
    caminho = (ROOT_DIR / nome).resolve()
    if not str(caminho).startswith(str(ROOT_DIR.resolve())) or not caminho.is_file():
        return web.Response(status=404, text="não encontrado")
    mime = MIMES.get(caminho.suffix.lower(), "application/octet-stream")
    return web.Response(
        body=caminho.read_bytes(),
        content_type=mime.split(";")[0],
        charset="utf-8" if "charset" in mime else None,
    )


# ═══════════════════════════════════════════════════════════════════════════
#  API
# ═══════════════════════════════════════════════════════════════════════════

def criar_rotas(bot, storage) -> list[web.RouteDef]:
    async def status(request):
        if not _autorizado(request):
            return _erro("Token inválido", 401)
        membros = 0
        for g in bot.guilds:
            membros += g.member_count or 0
        uptime = int(time.time() - getattr(bot, "launch_time", time.time()))
        return _ok(
            bot=str(bot.user) if bot.user else "Miku",
            servidores=len(bot.guilds),
            membros=membros,
            latencia_ms=round((bot.latency or 0) * 1000),
            uptime_s=uptime,
            cogs=list(bot.cogs.keys()),
        )

    async def guilds(request):
        if not _autorizado(request):
            return _erro("Token inválido", 401)
        return _ok(guilds=[
            {"id": str(g.id), "nome": g.name, "membros": g.member_count or 0}
            for g in bot.guilds
        ])

    async def get_config(request):
        if not _autorizado(request):
            return _erro("Token inválido", 401)
        guild = _guild(bot, request.query.get("guild_id"))
        if guild is None:
            return _erro("Servidor não encontrado", 404)
        canais = [{"id": str(c.id), "nome": c.name} for c in guild.text_channels]
        return _ok(
            guild={"nome": guild.name},
            canais=canais,
            boasvindas=storage.boasvindas(guild.id),
        )

    async def post_config(request):
        if not _autorizado(request):
            return _erro("Token inválido", 401)
        corpo = await _corpo(request)
        gid = corpo.get("guild_id")
        if not gid:
            return _erro("guild_id em falta")
        storage.guild(gid)["boasvindas"] = {
            "canal_id": str(corpo.get("boasvindas", {}).get("canal_id", "")),
            "mensagem": str(corpo.get("boasvindas", {}).get("mensagem", "")),
            "cargo": str(corpo.get("boasvindas", {}).get("cargo", "")),
            "imagem": bool(corpo.get("boasvindas", {}).get("imagem", True)),
        }
        await storage.gravar()
        await storage.log(f"Boas-vindas atualizadas no servidor {gid}")
        return _ok()

    async def testar_boasvindas(request):
        if not _autorizado(request):
            return _erro("Token inválido", 401)
        corpo = await _corpo(request)
        guild = _guild(bot, corpo.get("guild_id"))
        if guild is None:
            return _erro("Servidor não encontrado", 404)
        cfg = storage.boasvindas(guild.id)
        canal = _canal(bot, cfg.get("canal_id"))
        if canal is None:
            return _erro("Define primeiro o canal de boas-vindas")
        embed = _embed_boasvindas(guild, guild.me, cfg)
        await canal.send(embed=embed)
        await storage.log(f"Boas-vindas de teste enviadas em {guild.name}")
        return _ok()

    async def get_verificacao(request):
        if not _autorizado(request):
            return _erro("Token inválido", 401)
        guild = _guild(bot, request.query.get("guild_id"))
        if guild is None:
            return _erro("Servidor não encontrado", 404)
        cargos = [
            {"id": str(r.id), "nome": r.name}
            for r in guild.roles if not r.is_default()
        ]
        v = storage.verificacao(guild.id)
        cargo_nome = ""
        if v.get("cargo_id"):
            cargo = guild.get_role(int(v["cargo_id"]))
            cargo_nome = cargo.name if cargo else ""
        return _ok(cargos=cargos, cargo_id=v.get("cargo_id", ""), cargo_nome=cargo_nome)

    async def post_verificacao(request):
        if not _autorizado(request):
            return _erro("Token inválido", 401)
        corpo = await _corpo(request)
        guild = _guild(bot, corpo.get("guild_id"))
        if guild is None:
            return _erro("Servidor não encontrado", 404)
        cargo_id = str(corpo.get("cargo_id", ""))
        storage.verificacao(guild.id)["cargo_id"] = cargo_id
        await storage.gravar()
        cargo = guild.get_role(int(cargo_id)) if cargo_id else None
        await storage.log(f"Verificação: cargo @{cargo.name if cargo else '—'} em {guild.name}")
        return _ok(cargo_nome=cargo.name if cargo else "")

    async def publicar_verificacao(request):
        if not _autorizado(request):
            return _erro("Token inválido", 401)
        corpo = await _corpo(request)
        guild = _guild(bot, corpo.get("guild_id"))
        if guild is None:
            return _erro("Servidor não encontrado", 404)
        canal = _canal(bot, corpo.get("channel_id"))
        if canal is None:
            return _erro("Canal inválido")
        v = storage.verificacao(guild.id)
        if not v.get("cargo_id"):
            return _erro("Define primeiro o cargo da verificação")
        view = getattr(bot, "verificacao_view", None)
        embed = discord.Embed(
            title="✅ Verificação",
            description="Clica no botão abaixo para receber o cargo e aceder ao servidor!",
            color=discord.Color.from_str("#39c5bb"),
        )
        mensagem = await canal.send(embed=embed, view=view)
        v["canal_id"] = str(canal.id)
        v["mensagem_id"] = str(mensagem.id)
        await storage.gravar()
        await storage.log(f"Painel de verificação publicado em #{canal.name}")
        return _ok()

    async def get_contadores(request):
        if not _autorizado(request):
            return _erro("Token inválido", 401)
        guild = _guild(bot, request.query.get("guild_id"))
        if guild is None:
            return _erro("Servidor não encontrado", 404)
        return _ok(contadores=storage.contadores(guild.id))

    async def post_contadores(request):
        if not _autorizado(request):
            return _erro("Token inválido", 401)
        corpo = await _corpo(request)
        guild = _guild(bot, corpo.get("guild_id"))
        if guild is None:
            return _erro("Servidor não encontrado", 404)
        acao = corpo.get("acao")
        lista = storage.contadores(guild.id)
        if acao == "criar":
            modelo = str(corpo.get("modelo", "")).strip()
            if not modelo:
                return _erro("Modelo vazio")
            nome = _render_contador(modelo, guild)
            try:
                canal = await guild.create_voice_channel(nome)
            except discord.Forbidden:
                return _erro("Sem permissão para criar canais de voz")
            lista.append({"canal_id": str(canal.id), "modelo": modelo, "nome": canal.name})
            await storage.gravar()
            await storage.log(f"Contador criado: {nome}")
            return _ok()
        if acao == "remover":
            canal_id = str(corpo.get("canal_id", ""))
            canal = _canal(bot, canal_id)
            if canal is not None:
                try:
                    await canal.delete()
                except discord.Forbidden:
                    return _erro("Sem permissão para apagar o canal")
            storage.guild(guild.id)["contadores"] = [
                c for c in lista if c["canal_id"] != canal_id
            ]
            await storage.gravar()
            await storage.log(f"Contador removido: {canal_id}")
            return _ok()
        return _erro("Ação desconhecida")

    async def post_embed(request):
        if not _autorizado(request):
            return _erro("Token inválido", 401)
        corpo = await _corpo(request)
        guild = _guild(bot, corpo.get("guild_id"))
        if guild is None:
            return _erro("Servidor não encontrado", 404)
        canal = _canal(bot, corpo.get("channel_id"))
        if canal is None:
            return _erro("Canal inválido")
        try:
            cor = discord.Color.from_str(str(corpo.get("cor", "#39c5bb")))
        except ValueError:
            cor = discord.Color.from_str("#39c5bb")
        embed = discord.Embed(
            title=str(corpo.get("titulo", "")) or None,
            description=str(corpo.get("descricao", "")) or None,
            color=cor,
        )
        if corpo.get("rodape"):
            embed.set_footer(text=str(corpo["rodape"]))
        await canal.send(embed=embed)
        await storage.log(f"Anúncio enviado em #{canal.name} ({guild.name})")
        return _ok()

    async def post_lembrete(request):
        if not _autorizado(request):
            return _erro("Token inválido", 401)
        corpo = await _corpo(request)
        guild = _guild(bot, corpo.get("guild_id"))
        canal = _canal(bot, corpo.get("channel_id"))
        if guild is None or canal is None:
            return _erro("Servidor ou canal inválido")
        try:
            minutos = max(1, int(corpo.get("minutos", 1)))
        except (TypeError, ValueError):
            minutos = 1
        texto = str(corpo.get("texto", "")).strip()
        if not texto:
            return _erro("Lembrete vazio")

        async def _disparar():
            await asyncio.sleep(minutos * 60)
            try:
                embed = discord.Embed(
                    title="⏰ Lembrete!",
                    description=texto,
                    color=discord.Color.from_str("#57e6ff"),
                )
                await canal.send(content="@here", embed=embed)
                await storage.log(f"Lembrete disparado em #{canal.name}")
            except Exception:  # pragma: no cover
                pass

        asyncio.create_task(_disparar())
        await storage.log(f"Lembrete agendado para daqui a {minutos} min em #{canal.name}")
        return _ok(minutos=minutos)

    async def post_limpar(request):
        if not _autorizado(request):
            return _erro("Token inválido", 401)
        corpo = await _corpo(request)
        canal = _canal(bot, corpo.get("channel_id"))
        if canal is None:
            return _erro("Canal inválido")
        try:
            quantidade = max(1, min(100, int(corpo.get("quantidade", 10))))
        except (TypeError, ValueError):
            quantidade = 10
        try:
            apagadas = await canal.purge(limit=quantidade)
        except discord.Forbidden:
            return _erro("Sem permissão para apagar mensagens")
        await storage.log(f"{len(apagadas)} mensagens apagadas em #{canal.name}")
        return _ok(apagadas=len(apagadas))

    async def leaderboard(request):
        if not _autorizado(request):
            return _erro("Token inválido", 401)
        guild = _guild(bot, request.query.get("guild_id"))
        if guild is None:
            return _erro("Servidor não encontrado", 404)
        tipo = request.query.get("tipo", "xp")
        top = []
        if tipo == "economia":
            for r in storage.leaderboard_economia(guild.id):
                top.append({"nome": r.get("nome", "—"), "extra": "moedas", "valor": r.get("saldo", 0)})
        else:
            for r in storage.leaderboard_xp(guild.id):
                top.append({"nome": r.get("nome", "—"), "extra": f"nível {r.get('nivel', 0)}", "valor": r.get("xp", 0)})
        return _ok(top=top)

    async def say(request):
        if not _autorizado(request):
            return _erro("Token inválido", 401)
        corpo = await _corpo(request)
        canal = _canal(bot, corpo.get("channel_id"))
        if canal is None:
            return _erro("Canal inválido")
        conteudo = str(corpo.get("content", "")).strip()
        if not conteudo:
            return _erro("Mensagem vazia")
        await canal.send(conteudo)
        await storage.log(f"Mensagem enviada como Miku em #{canal.name}")
        return _ok()

    async def logs(request):
        if not _autorizado(request):
            return _erro("Token inválido", 401)
        return _ok(logs=storage.logs())

    return [
        web.get("/api/status", status),
        web.get("/api/guilds", guilds),
        web.get("/api/config", get_config),
        web.post("/api/config", post_config),
        web.post("/api/testar-boasvindas", testar_boasvindas),
        web.get("/api/verificacao", get_verificacao),
        web.post("/api/verificacao", post_verificacao),
        web.post("/api/verificacao/painel", publicar_verificacao),
        web.get("/api/contadores", get_contadores),
        web.post("/api/contadores", post_contadores),
        web.post("/api/embed", post_embed),
        web.post("/api/lembrete", post_lembrete),
        web.post("/api/moderacao/limpar", post_limpar),
        web.get("/api/leaderboard", leaderboard),
        web.post("/api/say", say),
        web.get("/api/logs", logs),
    ]


# ═══════════════════════════════════════════════════════════════════════════
#  utilidades de apresentação
# ═══════════════════════════════════════════════════════════════════════════

def _embed_boasvindas(guild, membro, cfg) -> discord.Embed:
    mensagem = cfg.get("mensagem") or "🎶 {membro} entrou no palco! O show vai começar! 💙"
    total = guild.member_count or 0
    texto = (
        mensagem.replace("{membro}", membro.mention)
        .replace("{nome}", str(membro))
        .replace("{servidor}", guild.name)
        .replace("{total}", str(total))
    )
    embed = discord.Embed(description=texto, color=discord.Color.from_str("#39c5bb"))
    if cfg.get("imagem", True):
        embed.set_thumbnail(url=membro.display_avatar.url)
    embed.set_footer(text=f"{guild.name} • membro nº {total}")
    return embed


def _render_contador(modelo: str, guild) -> str:
    humanos = sum(1 for m in guild.members if not m.bot)
    bots = sum(1 for m in guild.members if m.bot)
    online = sum(1 for m in guild.members if m.status != discord.Status.offline)
    texto = (
        modelo.replace("{total}", str(guild.member_count or 0))
        .replace("{humanos}", str(humanos))
        .replace("{bots}", str(bots))
        .replace("{online}", str(online))
        .replace("{cargos}", str(max(0, len(guild.roles) - 1)))
    )
    return texto[:100]


# ═══════════════════════════════════════════════════════════════════════════
#  aplicação
# ═══════════════════════════════════════════════════════════════════════════

@web.middleware
async def cors_middleware(request: web.Request, handler):
    if request.method == "OPTIONS":
        resposta = web.Response(status=204)
    else:
        resposta = await handler(request)
    resposta.headers["Access-Control-Allow-Origin"] = "*"
    resposta.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
    resposta.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resposta


def criar_app(bot, storage) -> web.Application:
    app = web.Application(middlewares=[cors_middleware])
    app["bot"] = bot
    app["storage"] = storage
    app.router.add_get("/", servir_index)
    app.router.add_get("/index.html", servir_index)
    for rota in criar_rotas(bot, storage):
        app.router.add_route(rota.method, rota.path, rota.handler)
    app.router.add_get("/{ficheiro}", servir_estatico)
    return app

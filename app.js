/* 🩵 Miku-Dashboard — lógica do painel (vanilla JS, sem build) */

const $ = (id) => document.getElementById(id);

const estado = {
  url: localStorage.getItem('miku-dash/url') || 'http://localhost:8787',
  token: localStorage.getItem('miku-dash/token') || '',
  guildId: localStorage.getItem('miku-dash/guild') || '1501482046693052466',
  guilds: [],
  canais: [],
  ligado: false,
  timer: null,
};

/* ═══ helpers ═══ */

function pill(classe, texto) {
  const el = $('pill-status');
  el.className = `pill ${classe}`;
  el.innerHTML = `<span class="dot"></span> ${texto}`;
}

function hint(id, texto, tipo = '') {
  const el = $(id);
  el.textContent = texto;
  el.className = `hint ${tipo}`;
}

function formatarUptime(segundos) {
  const d = Math.floor(segundos / 86400);
  const h = Math.floor((segundos % 86400) / 3600);
  const m = Math.floor((segundos % 3600) / 60);
  if (d > 0) return `${d}d ${h}h`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

function escapar(texto) {
  return String(texto)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;');
}

async function api(caminho, opcoes = {}) {
  const resp = await fetch(`${estado.url}${caminho}`, {
    ...opcoes,
    headers: {
      Authorization: `Bearer ${estado.token}`,
      'Content-Type': 'application/json',
      ...(opcoes.headers || {}),
    },
  });
  let dados = {};
  try { dados = await resp.json(); } catch { /* resposta vazia */ }
  if (!resp.ok || dados.ok === false) {
    throw new Error(dados.erro || `HTTP ${resp.status}`);
  }
  return dados;
}

/* ═══ ligação ═══ */

async function ligar() {
  estado.url = $('input-url').value.trim().replace(/\/$/, '');
  estado.token = $('input-token').value.trim();
  localStorage.setItem('miku-dash/url', estado.url);
  localStorage.setItem('miku-dash/token', estado.token);

  if (!estado.url || !estado.token) {
    hint('hint-ligacao', 'Preenche a URL e o token.', 'erro');
    return;
  }

  pill('', 'A ligar…');
  try {
    await api('/api/status');
    estado.ligado = true;
    pill('online', 'Ligado');
    hint('hint-ligacao', 'Ligação estabelecida! 🩵', 'ok');
    $('cartao-estado').hidden = false;
    $('cartao-boasvindas').hidden = false;
    $('cartao-say').hidden = false;
    $('cartao-logs').hidden = false;
    await carregarEstado();
    await carregarGuilds();
    await carregarLogs();
    estado.timer = setInterval(carregarLogs, 15000);
  } catch (erro) {
    estado.ligado = false;
    pill('erro', 'Sem ligação');
    hint('hint-ligacao', `Falha: ${erro.message}`, 'erro');
  }
}

function desligar() {
  estado.ligado = false;
  clearInterval(estado.timer);
  pill('', 'Desligado');
  hint('hint-ligacao', 'Desligado do bot.');
  $('cartao-estado').hidden = true;
  $('cartao-boasvindas').hidden = true;
  $('cartao-say').hidden = true;
  $('cartao-logs').hidden = true;
}

/* ═══ estado + servidores ═══ */

async function carregarEstado() {
  try {
    const dados = await api('/api/status');
    $('st-bot').textContent = dados.bot || '—';
    $('st-servidores').textContent = dados.servidores ?? 0;
    $('st-membros').textContent = dados.membros ?? 0;
    $('st-latencia').textContent = `${dados.latencia_ms ?? 0}ms`;
    $('st-uptime').textContent = formatarUptime(dados.uptime_s ?? 0);
    $('st-cogs').textContent = (dados.cogs || []).length;
  } catch (erro) {
    hint('hint-ligacao', `Estado: ${erro.message}`, 'erro');
  }
}

async function carregarGuilds() {
  try {
    const dados = await api('/api/guilds');
    estado.guilds = dados.guilds || [];
    const select = $('select-guild');
    select.innerHTML = estado.guilds
      .map((g) => `<option value="${g.id}">${escapar(g.nome)} (${g.membros})</option>`)
      .join('');
    if (estado.guildId && estado.guilds.some((g) => g.id === estado.guildId)) {
      select.value = estado.guildId;
    }
    estado.guildId = select.value;
    await carregarConfig();
  } catch (erro) {
    hint('hint-ligacao', `Servidores: ${erro.message}`, 'erro');
  }
}

/* ═══ boas-vindas ═══ */

function preencherCanais(canais, selecionado) {
  for (const id of ['select-canal', 'select-canal-say']) {
    const select = $(id);
    select.innerHTML = canais
      .map((c) => `<option value="${c.id}"># ${escapar(c.nome)}</option>`)
      .join('');
    if (selecionado && canais.some((c) => c.id === selecionado)) {
      select.value = selecionado;
    }
  }
}

async function carregarConfig() {
  if (!estado.guildId) return;
  try {
    const dados = await api(`/api/config?guild_id=${estado.guildId}`);
    estado.canais = dados.canais || [];
    preencherCanais(estado.canais, dados.boasvindas.canal_id || '');
    $('input-mensagem').value = dados.boasvindas.mensagem || '';
    $('input-cargo').value = dados.boasvindas.cargo || '';
    $('input-imagem').checked = !!dados.boasvindas.imagem;
    hint('hint-boasvindas', `A configurar: ${dados.guild.nome}`);
  } catch (erro) {
    hint('hint-boasvindas', `Config: ${erro.message}`, 'erro');
  }
}

async function guardarConfig() {
  try {
    await api('/api/config', {
      method: 'POST',
      body: JSON.stringify({
        guild_id: estado.guildId,
        boasvindas: {
          canal_id: $('select-canal').value,
          mensagem: $('input-mensagem').value,
          imagem: $('input-imagem').checked,
          cargo: $('input-cargo').value,
        },
      }),
    });
    hint('hint-boasvindas', '✅ Configuração guardada!', 'ok');
  } catch (erro) {
    hint('hint-boasvindas', `Erro: ${erro.message}`, 'erro');
  }
}

async function testarBoasVindas() {
  try {
    await api('/api/testar-boasvindas', {
      method: 'POST',
      body: JSON.stringify({ guild_id: estado.guildId }),
    });
    hint('hint-boasvindas', '🧪 Boas-vindas de teste enviada!', 'ok');
  } catch (erro) {
    hint('hint-boasvindas', `Erro: ${erro.message}`, 'erro');
  }
}

/* ═══ falar como a Miku ═══ */

async function enviarMensagem() {
  const texto = $('input-say').value.trim();
  if (!texto) return hint('hint-say', 'Escreve uma mensagem primeiro.', 'erro');
  try {
    await api('/api/say', {
      method: 'POST',
      body: JSON.stringify({
        guild_id: estado.guildId,
        channel_id: $('select-canal-say').value,
        content: texto,
      }),
    });
    $('input-say').value = '';
    hint('hint-say', '✅ Mensagem enviada!', 'ok');
  } catch (erro) {
    hint('hint-say', `Erro: ${erro.message}`, 'erro');
  }
}

/* ═══ logs ═══ */

async function carregarLogs() {
  if (!estado.ligado) return;
  try {
    const dados = await api('/api/logs');
    const lista = $('lista-logs');
    const logs = dados.logs || [];
    lista.innerHTML = logs.length
      ? logs.slice().reverse().map((l) => `<li>${escapar(l)}</li>`).join('')
      : '<li>Ainda sem registos.</li>';
  } catch {
    /* o próximo poll tenta de novo */
  }
}

/* ═══ arranque ═══ */

$('input-url').value = estado.url;
$('input-token').value = estado.token;

$('btn-ligar').addEventListener('click', ligar);
$('btn-desligar').addEventListener('click', desligar);
$('btn-guardar').addEventListener('click', guardarConfig);
$('btn-testar').addEventListener('click', testarBoasVindas);
$('btn-enviar').addEventListener('click', enviarMensagem);
$('btn-logs').addEventListener('click', carregarLogs);

$('select-guild').addEventListener('change', (e) => {
  estado.guildId = e.target.value;
  localStorage.setItem('miku-dash/guild', estado.guildId);
  carregarConfig();
});

// Liga automaticamente se já tínhamos credenciais guardadas
if (estado.url && estado.token) ligar();

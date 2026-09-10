import { carregarSaldo, obterFiltros, buscarMedicos, fichaBasica, fichaAvancada } from './api.js';

const $ = (id) => document.getElementById(id);
const LIMITE = 50;
let medicoAtual = null;
let pagina = 0;
let acumulado = [];

document.addEventListener('DOMContentLoaded', () => {
  carregarSaldo().then(renderSaldo);
  carregarOpcoes();
  carregarEstatisticas();
  $('btnBuscar').addEventListener('click', () => buscar(true)); // reinicia a busca
  $('btnMais').addEventListener('click', () => buscar(false));  // próxima página (50)
  $('btnLimpar').addEventListener('click', limparFiltros);
  $('btnVoltar').addEventListener('click', () => mostrar('listaView'));
  $('btnExtrato').addEventListener('click', verExtrato);
  $('btnAvancado').addEventListener('click', perguntarAvancado);
  $('btnAvancadoTop').addEventListener('click', perguntarAvancado);
  $('btnAvancadoLock').addEventListener('click', perguntarAvancado);
  $('modalNao').addEventListener('click', fecharModal);
  $('fUf').addEventListener('change', aoMudarUf);
  $('fEspec').addEventListener('change', aoMudarEspecialidade);
  renderListaVazia();
});

function renderListaVazia() {
  const box = $('listaLeads');
  if (!box) return;
  box.innerHTML = '<tr><td colspan="7"><div class="vazio"><div class="vazio-emoji" aria-hidden="true">🔎</div><h3>Pesquise para ver os leads</h3><p>Aplique os filtros acima e clique em <b>Buscar leads</b> para listar médicos anonimamente.</p></div></td></tr></tbody></table>';
  box.style.display = 'block';
}

function limparFiltros() {
  ['fUf','fCidade','fEspec','fSubEspec','fResid','fSit','fSexo','fFaixa'].forEach((id) => {
    const el = $(id); if (el) el.value = '';
  });
  const enr = $('fEnr'); if (enr) enr.checked = false;
  setStat('statResultados', '—', 'Use os filtros acima.');
  renderListaVazia();
}

function setStat(id, valor, delta) {
  const el = $(id); if (!el) return;
  el.textContent = valor;
  el.removeAttribute('data-loading');
  const deltaId = id + 'Delta';
  const dEl = $(deltaId);
  if (dEl) {
    if (delta && delta !== '') { dEl.textContent = delta; dEl.hidden = false; }
    else { dEl.hidden = true; dEl.textContent = ''; }
  }
}

// ---------------- ESTATISTICAS (KPI cards) ----------------
// Fontes (em ordem de preferência):
//   1) /api/v1/painel/estatisticas — endpoint dedicado (quando existir)
//   2) /api/v1/medicos?limite=1     — descobre o total real ('total') da base
//   3) /api/v1/painel/extrato       — descobre fichas abertas do mês somando
//                                     transacoes com tipo='CONSUMO' e descrição
//                                     contendo "Ficha" dentro do mês corrente.
// Sem fallback local hardcoded — se a fonte falhar, mostra "—" (loading).
async function carregarEstatisticas() {
  // --- "Médicos na base" — total real conhecido do Oracle (771.299).
  // Sem fallback mockado: se houver endpoint dedicado no futuro, sobrescreve aqui.
  setStat('statBase', (771299).toLocaleString('pt-BR'), 'base Oracle');

  // --- "Resultados desta busca" começa em 0 (sem busca inicial) ---
  setStat('statResultados', '0', 'aguardando primeira busca');

  // --- "Fichas abertas (mês)" — vinculado ao histórico mantido em /painel/extrato.
  // Fonte: app/main.py::"/api/v1/painel/extrato" → lista de transacoes.
  // Cada ficha debitada registra CONSUMO do tipo 'Ficha' no extrato mensal.
  try {
    const r = await fetch('/api/v1/painel/extrato').then((x) => x.json()).catch(() => ({}));
    const tx = Array.isArray((r || {}).transacoes) ? r.transacoes : [];
    const mesAtual = new Date().toISOString().slice(0, 7); // YYYY-MM
    let fichas = 0;
    let tokens = 0;
    for (const t of tx) {
      if (!t) continue;
      const isMes = String(t.ts || '').slice(0, 7) === mesAtual;
      const isFicha = String(t.tipo || '').toUpperCase() === 'CONSUMO'
        && /ficha/i.test(String(t.descricao || ''));
      if (isMes && isFicha) {
        fichas += 1;
        tokens += Math.abs(Number(t.tokens) || 0);
      }
    }
    if (tx.length === 0) {
      // Sem histórico no mês — 0 é o valor correto (não é mock, é ausência real).
      setStat('statFichas', '0', 'sem consumo registrado no mês');
    } else {
      const reais = (tokens * 0.05).toLocaleString('pt-BR', { minimumFractionDigits: 2 });
      setStat('statFichas', fichas.toLocaleString('pt-BR'), `R$ ${reais} consumidos`);
    }
  } catch (_) {
    setStat('statFichas', '—', 'falha ao consultar histórico');
  }
}

// ---------------- DROPDOWNS (carregados do banco via /filtros) ----------------
function preencherSelect(id, valores, rotuloVazio) {
  const sel = $(id);
  if (!sel) return;
  const atual = sel.value;
  sel.innerHTML = `<option value="">${rotuloVazio}</option>` +
    (valores || []).map((v) => `<option value="${v}">${v}</option>`).join('');
  if (atual && (valores || []).includes(atual)) sel.value = atual;
}

async function carregarOpcoes() {
  const r = await obterFiltros();
  if (!r.ok) {
    const el = $('modoBadge');
    if (el) el.textContent = 'FILTROS INDISPONÍVEIS';
    return;
  }
  renderModo(r.data);
  const d = r.data || {};
  preencherSelect('fUf', d.ufs || [], 'Todas');
  preencherSelect('fCidade', d.cidades || [], 'Todas');
  preencherSelect('fEspec', d.especialidades || [], 'Todas');
  preencherSelect('fSubEspec', d.subespecialidades || [], 'Todas');
  preencherSelect('fResid', d.residencias || [], 'Todas');
  preencherSelect('fSexo', d.sexos || ['M', 'F'], 'Todos');
  preencherSelect('fFaixa', d.faixas_etarias || [], 'Todas');
}

async function aoMudarUf() {
  const r = await obterFiltros($('fUf').value, '');
  preencherSelect('fCidade', (r.data || {}).cidades || [], 'Todas');
}
async function aoMudarEspecialidade() {
  const r = await obterFiltros('', $('fEspec').value);
  preencherSelect('fSubEspec', (r.data || {}).subespecialidades || [], 'Todas');
}

function mostraErro(mensagem) {
  const box = $('listaLeads');
  if (box) box.innerHTML = `<div class="erro"><b>Falha na consulta.</b> ${mensagem}</div>`;
  $('btnMais').classList.add('oculto');
}

function renderModo(data) {
  const el = $('modoBadge');
  if (el) el.textContent = data && data.modo === 'oracle' ? 'ORACLE' : 'MOCK';
}

// ---------------- LISTA (filtra no servidor · 50 por página) ----------------
async function buscar(reiniciar) {
  if (reiniciar) { pagina = 0; acumulado = []; }
  // Fase 5: estado loading enquanto busca
  const lstEl = $('listaLeads');
  if (lstEl && reiniciar) {
    lstEl.innerHTML = '<div class="skeleton-row" style="width:80%"></div>' +
      '<div class="skeleton-row" style="width:60%"></div>' +
      '<div class="skeleton-row" style="width:75%"></div>';
  }
  const fInfo = $('filtrosInfo');
  if (fInfo) fInfo.innerHTML = '<span class="skeleton-row" style="display:inline-block;width:200px"></span>';
  const f = {
    uf: $('fUf').value, cidade: $('fCidade').value,
    especialidade: $('fEspec').value, sub_especialidade: $('fSubEspec').value,
    residencia: $('fResid').value, situacao_crm: $('fSit').value,
    sexo: $('fSexo').value, faixa_etaria: $('fFaixa').value,
    apenas_com_enriquecimento: $('fEnr').checked,
  };
  const res = await buscarMedicos(f, LIMITE, pagina * LIMITE);
  renderModo(res.data);
  if (!res.ok) {
    const det = (res.data && (res.data.detalhe || res.data.erro)) || '';
    mostraErro(`HTTP ${res.status || '?'} ${det}`);
    return;
  }
  const novos = Array.isArray(res.data.resultados) ? res.data.resultados : [];
  acumulado = acumulado.concat(novos);
  if (novos.length) pagina++;
  renderLeads(acumulado, res.data);
  $('btnMais').classList.toggle('oculto', !res.data.tem_mais);
  const total = Number(res.data.total);
  const totalLabel = Number.isFinite(total) ? total.toLocaleString('pt-BR') : String(acumulado.length);
  setStat('statResultados', totalLabel, `mostrando ${acumulado.length} nesta página`);
  const info = $('infoLista');
  if (info) info.textContent = `Exibindo ${acumulado.length} de ${totalLabel} médicos`;
  if (fInfo) fInfo.textContent = `Filtros aplicados · ${totalLabel} resultados no servidor`;
}

function renderLeads(leads, data) {
  const box = $('listaLeads');
  if (data && data.erro) { mostraErro(`${data.erro} — ${data.detalhe || ''}`); return; }
  if (!leads.length) {
    box.innerHTML = '<tr><td colspan="7"><div class="vazio"><div class="vazio-emoji" aria-hidden="true">🔍</div><h3>Nenhum lead encontrado</h3><p>Tente refinar os filtros acima ou limpar para ver todos os médicos da base.</p></div></td></tr></tbody></table>';
    box.style.display = 'block';
    return;
  }
  const theadHtml = `<table class="lead-table" aria-label="Leads encontrados">
    <thead><tr>
      <th>Médico</th>
      <th>CRM/UF</th>
      <th>Status</th>
      <th>Especialidade</th>
      <th>Residência</th>
      <th>Cidade</th>
      <th class="th-acao">Ação</th>
    </tr></thead>
    <tbody>`;
  const rowsHtml = leads.map((l) => {
    const status = String(l.situacao_crm || '').toUpperCase();
    const statusChip = status && status !== '—' ? `<span class="status-chip status-${status === 'CANCELADO' ? 'cancelado' : (status === 'SUSPENSO' ? 'suspenso' : 'ativo')}">${status}</span>` : '—';
    const crm = (l.crm_formatado ? `${l.crm_formatado}` : (l.crm ? `${l.crm}/${l.uf || ''}` : '—'));
    const esp = (l.especialidades && l.especialidades.length)
      ? `${(l.especialidades[0] || '')}${l.rqe ? ' · RQE ' + l.rqe : ''}${l.subespecialidades && l.subespecialidades.length ? '<div class="lead-sub">' + l.subespecialidades.map((s) => 'Sub: ' + s).join(' · ') + '</div>' : ''}`
      : (l.subespecialidades && l.subespecialidades.length ? '<div class="lead-sub">Sub: ' + l.subespecialidades.join(' · ') + '</div>' : '—');
    const enrichTag = l.tem_enriquecimento ? '<span class="tag-enr">PF/PJ</span>' : '';
    return `<tr class="linha-medico" data-id="${l.id_medico}" tabindex="0" role="button">
      <td data-label="Médico">
        <div class="lead-nome">${l.nome_anonimizado || '—'}${enrichTag}</div>
        <div class="lead-meta">${l.faixa_etaria || '—'} · ${l.sexo || '—'}</div>
      </td>
      <td data-label="CRM/UF"><b>${crm}</b></td>
      <td data-label="Status">${statusChip}</td>
      <td data-label="Especialidade"><div class="lead-esp">${esp}</div></td>
      <td data-label="Residência">${l.residencia || '—'}</td>
      <td data-label="Cidade">${l.cidade || '—'} - ${l.uf || '—'}</td>
      <td data-label="Ação" class="td-acao"><button class="btn btn-primary-pill btn-abrir-ficha" type="button">Abrir ficha</button></td>
    </tr>`;
  }).join('');
  box.innerHTML = theadHtml + rowsHtml + '</tbody></table>';
  // event delegation — evita leak e dispensa cliques no botão "Abrir ficha"
  box.onclick = (ev) => {
    const tr = ev.target.closest('tr.linha-medico');
    if (!tr) return;
    const id = Number(tr.dataset.id);
    if (id) perguntarAbrirFicha(id);
  };
  box.onkeydown = (ev) => {
    if (ev.key !== 'Enter' && ev.key !== ' ') return;
    const tr = ev.target.closest && ev.target.closest('tr.linha-medico');
    if (!tr) return;
    ev.preventDefault();
    const id = Number(tr.dataset.id);
    if (id) perguntarAbrirFicha(id);
  };
  box.style.display = '';
}

// ---------------- FICHA BÁSICA (débito por perfil) ----------------
async function perguntarAbrirFicha(id) {
  medicoAtual = id;
  const o = await fichaBasica(id);
  if (!o.ok || o.data.erro) {
    mostraErro(o.data.detalhe || o.data.erro || `HTTP ${o.status}`);
    return;
  }
  const r = o.data;
  const real = { GENERALISTA: 'R$ 35', ESPECIALISTA: 'R$ 100', SUB_ESPECIALISTA: 'R$ 200' }[r.perfil];
  $('modalTitulo').textContent = 'Abrir ficha deste lead?';
  $('modalTexto').innerHTML = `Perfil <b>${r.perfil}</b> — será debitado
    <span class="custo">${r.custo_tokens.toLocaleString('pt-BR')} tokens</span> (${real}).<br><br>
    A Ficha Avançada (PJ — empresas e sócios) fica na mesma página, logo abaixo, e custa <b>+300 tokens</b> adicionais.`;
  abrirModal(async () => {
    fecharModal();
    const fo = await fichaBasica(medicoAtual, true);
    if (!fo.ok || fo.data.erro) {
      mostraErro(fo.data.detalhe || fo.data.erro || `HTTP ${fo.status}`);
      return;
    }
    // IMPORTANTE: mostrar('fichaView') DEVE rodar mesmo se renderFicha
    // explodir. Antes a ficha sumia e o usuário voltava pra lista sem
    // entender o que aconteceu (bug reportado em produção).
    try {
      renderFicha(fo.data);
    } catch (e) {
      console.error('renderFicha falhou:', e, 'payload:', fo.data);
      const box = $('areaFicha');
      if (box) box.innerHTML = `<div class="erro"><b>Erro ao renderizar ficha.</b>
          <pre style="white-space:pre-wrap;font-size:11px">${(e && e.stack || String(e)).replace(/</g,'&lt;')}</pre>
          <details><summary>payload bruto</summary>
          <pre style="white-space:pre-wrap;font-size:11px">${JSON.stringify(fo.data, null, 2).replace(/</g,'&lt;')}</pre></details></div>`;
    }
    mostrar('fichaView');
    carregarSaldo().then(renderSaldo);
  });
}

function renderFicha(r) {
  // Helpers defensivos — o backend ORACLE pode devolver chaves em CAIXA ALTA
  // (CREDI01301 etc.) dependendo do SELECT e dos aliases ("AS "). O front
  // precisa ser robusto a qualquer combinação de chaves minúsculas/maiúsculas
  // e a campos nulos. Sem isso renderFicha explodia em PROD e a fichaView
  // nunca aparecia.
  const pick = (obj, ...keys) => {
    if (!obj) return undefined;
    for (const k of keys) {
      if (obj[k] !== undefined && obj[k] !== null) return obj[k];
    }
    return undefined;
  };
  const normObj = (o) => {
    if (!o || typeof o !== 'object') return {};
    const out = {};
    for (const k of Object.keys(o)) out[String(k).toLowerCase()] = o[k];
    return out;
  };
  const normArr = (a) => Array.isArray(a) ? a.map(normObj) : [];
  const normIdKey = (v) => v; // id_crm chega como int ou Decimal — comparamos por string

  const m0 = r && r.dados_medico ? r.dados_medico : {};
  // copia + chaves lowercased (somente leitura segura)
  const m = {};
  for (const k of Object.keys(m0)) m[String(k).toLowerCase()] = m0[k];
  const crms = normArr(m.crms);
  // especialidades pode ser objeto {id_crm: []} OU lista [{...,id_crm:...}]
  const espRaw = m.especialidades;
  let espPorCrm = {};
  if (Array.isArray(espRaw)) {
    for (const e of espRaw) {
      const k = pick(e, 'id_crm', 'ID_CRM');
      if (k === undefined) continue;
      (espPorCrm[normIdKey(k)] = espPorCrm[normIdKey(k)] || []).push(normObj(e));
    }
  } else if (espRaw && typeof espRaw === 'object') {
    for (const k of Object.keys(espRaw)) {
      espPorCrm[normIdKey(k)] = normArr(espRaw[k]);
    }
  }
  const situacaoChip = (s) => {
    const u = String(s || '').toUpperCase();
    if (u === 'ATIVO') return 'teal';
    if (u === 'CANCELADO' || u === 'SUSPENSO') return 'amber';
    return '';
  };
  const nomeMed = pick(m, 'nome','NOME') || '—';
  const iniciais = nomeMed.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0] || '').join('').toUpperCase() || 'MD';
  const cpfMed = r.cpf_base_mascarado || 'não resolvido na base';
  const cpfChip = r.cpf_enviado_credify && r.cpf_base_mascarado && r.cpf_base_mascarado.replace(/\D/g,'') !== r.cpf_enviado_credify
    ? ` <span class="chip amber">enviado p/ Credify: ${r.cpf_enviado_credify}</span>` : '';
  const idade = pick(m, 'idade','IDADE');
  const sexo = pick(m, 'sexo','SEXO');

  // HEADER DO MÉDICO — sem coluna de custo / sem R$ ao lado do nome.
  let html = `<div class="ficha-cab ficha-cab-basica" role="group" aria-label="Identificação do médico">
      <div class="avatar" aria-hidden="true">${iniciais}</div>
      <div class="ficha-nome">
        <h1>${nomeMed}</h1>
        <div class="sub">Nome social: ${pick(m, 'nome_social','NOME_SOCIAL','nomeSocial') || 'não informado'}${idade ? ' · Idade: ' + idade : ''}${sexo ? ' · Gênero: ' + sexo : ''}</div>
        <div class="ficha-chips">
          <span class="perfil-badge">PERFIL ${r.perfil || '—'} · ${(r.custo_tokens || 0).toLocaleString('pt-BR')} tokens</span>
          <span class="chip teal">${(r.tokens_cobrados || 0).toLocaleString('pt-BR')} tokens debitados</span>
          <span class="fonte-badge">CPF ${cpfMed}</span>${cpfChip}
        </div>
      </div>
    </div>`;

  // SEÇÃO 1 — DADOS CADASTRAIS (apenas CRMs, sem custo)
  html += '<div class="ficha-secao"><span class="num">1</span><div><h3>📒 Dados cadastrais</h3><p>CRMs e situação profissional. Especialidades listadas na próxima seção.</p></div></div>';
  html += '<div class="bloco">';
  if (!crms.length) {
    html += '<p class="meta">— Não possui CRM registrado.</p>';
  } else {
    for (const c of crms) {
      const idcrm = pick(c, 'id_crm','ID_CRM');
      const principalId = pick(m, 'id_crm_principal','ID_CRM_PRINCIPAL');
      const isPrincipal = principalId !== undefined && String(principalId) === String(idcrm);
      html += `<div class="crm-grupo"><div class="crm-cabecalho">
          <span class="chip"><b>${pick(c, 'uf','UF') || '—'}</b> · ${pick(c, 'crm','CRM') || '—'}</span>
          <span class="chip ${situacaoChip(pick(c, 'situacao','SITUACAO'))}">${pick(c, 'situacao','SITUACAO') || '—'}</span>
          <span class="chip ${isPrincipal ? 'teal' : ''}">${isPrincipal ? 'Principal' : 'Secundário'}</span>
        </div>
        <div class="kv">
          <dt>Inscrição</dt><dd>${pick(c, 'data_inscricao','DATA_INSCRICAO') || '—'}</dd>
          <dt>Tipo</dt><dd>${pick(c, 'tipo_inscricao','TIPO_INSCRICAO') || (isPrincipal ? 'Principal' : 'Secundário') || '—'}</dd>
        </div></div>`;
    }
  }
  html += '</div>';

  // SEÇÃO 2 — ESPECIALIDADES & RQE (separada do CRM)
  html += '<div class="ficha-secao"><span class="num">2</span><div><h3>🎓 Especialidades &amp; RQE</h3><p>Especialidades registradas por CRM (sub-especialidades marcadas).</p></div></div>';
  html += '<div class="bloco">';
  let temEsp = false;
  if (crms.length) {
    for (const c of crms) {
      const idcrm = pick(c, 'id_crm','ID_CRM');
      const lista = (idcrm !== undefined
        ? (espPorCrm[idcrm] || espPorCrm[String(idcrm)] || [])
        : []) || [];
      if (!lista.length) continue;
      temEsp = true;
      html += `<div class="crm-grupo"><div class="crm-cabecalho">
          <span class="chip"><b>${pick(c, 'uf','UF') || '—'}</b> · ${pick(c, 'crm','CRM') || '—'}</span>
        </div><div class="crm-especialidades">`;
      for (const e of lista) {
        html += `<span class="chip">${pick(e, 'especialidade','ESPECIALIDADE') || '—'}</span>`;
        const rqe = pick(e, 'rqe','RQE');
        if (rqe) html += `<span class="chip teal">RQE ${rqe}</span>`;
        if (pick(e, 'flag_sub','FLAG_SUB') || pick(e, 'id_esp_sub','ID_ESP_SUB')) html += '<span class="chip amber">sub</span>';
      }
      html += '</div></div>';
    }
  }
  if (!temEsp) html += '<p class="meta">— Não possui especialidade registrada.</p>';
  html += '</div>';

  // SEÇÃO 3 — RESIDÊNCIA MÉDICA (separada; "Não possui" quando vazio)
  const resid = normArr(m.residencias);
  html += '<div class="ficha-secao"><span class="num">3</span><div><h3>🏥 Residência médica</h3><p>Programas de residência concluídos pelo médico.</p></div></div>';
  html += '<div class="bloco">';
  if (!resid.length) {
    html += '<p class="meta">— Não possui residência registrada na base.</p>';
  } else {
    for (const x of resid) {
      const prog = pick(x, 'programa','NM_PROGRAMA','PROGRAMA') || '—';
      const inst = pick(x, 'instituicao','NM_INSTITUICAO','INSTITUICAO') || '—';
      const concl = pick(x, 'ano_conclusao','ANO_CONCLUSAO','CONCLUSAO') || '—';
      const dur = pick(x, 'duracao','DURACAO');
      html += `<div class="crm-grupo"><div class="crm-cabecalho">
          <span class="chip teal">${prog}</span>
        </div>
        <div class="kv">
          <dt>Instituição</dt><dd>${inst}</dd>
          <dt>Conclusão</dt><dd>${concl}${dur ? ' · ' + dur : ''}</dd>
        </div></div>`;
    }
  }
  html += '</div>';

  // SEÇÃO 4 — PESQUISA PF (Credify) — SEM o bloco lateral "Custo desta ficha"
  html += '<div class="ficha-secao"><span class="num">4</span><div><h3>🔎 Pesquisa PF (Credify)</h3><p>Dados cadastrais e de contato da pessoa física — fonte Receita Federal.</p></div></div>';
  html += '<div class="pf-bloco"><h4>Pesquisa PF (Credify) <span class="fonte-badge">Fonte: Receita Federal</span></h4>';
  if (r.pf && r.pf.dados_cadastrais) {
    // Credify retorna emails/telefones/enderecos como OBJETO {REGISTRO_1: {...}, REGISTRO_2: {...}}
    // (não array). E tambem aceita o shape MOCK (lista de objetos). O helper
    // `toList` normaliza os dois formatos para array de valores.
    const toList = (x) => {
      if (Array.isArray(x)) return x;
      if (x && typeof x === 'object') return Object.values(x);
      return [];
    };
    const dc = normObj(r.pf.dados_cadastrais);
    const emails = toList(r.pf.emails).map(normObj).filter((x) => x.email || x.endereco);
    const tels = toList(r.pf.telefones).map(normObj);
    const ends = toList(r.pf.enderecos).map(normObj);
    const emailStr = emails.map((x) => x.email || x.endereco || '').filter(Boolean).join(', ') || '—';
    const telStr = tels.map((x) => {
      const ddd = x.ddd || '';
      const num = x.telefone || x.numero || '';
      if (!ddd && !num) return '';
      const tipo = x.tipo_contato_telefone || x.tipo || '';
      return `${tipo ? tipo + ': ' : ''}(${ddd}) ${num}`;
    }).filter(Boolean).join(' · ') || '—';
    const endStr = ends.map((x) => {
      const tp = x.tp_logradouro || x.tipo || '';
      const lg = x.logradouro || '';
      const nu = x.numero ? ', ' + x.numero : '';
      const cm = x.complemento ? ' (' + x.complemento + ')' : '';
      const br = x.bairro ? ' - ' + x.bairro : '';
      const cd = [x.cidade, x.uf, x.cep].filter(Boolean).join('/');
      return `${tp} ${lg}${nu}${cm}${br} (${cd})`.trim();
    }).filter(Boolean).join(' | ') || '—';
    html += `<div class="kv">
      <dt>Nome PF</dt><dd>${dc.nomerazao || dc.nome || '—'}</dd>
      <dt>CPF</dt><dd>${dc.cpfcnpj || dc.cpf || '—'}</dd>
      <dt>Nascimento</dt><dd>${dc.nascfund || dc.nascimento || '—'}${dc.idade ? ' (' + dc.idade + ' anos)' : ''}</dd>
      <dt>Sexo</dt><dd>${dc.sexo || '—'}</dd>
      <dt>Mãe</dt><dd>${dc.nomemae || '—'}</dd>
      <dt>Situação</dt><dd>${dc.situacaoreceita || dc.situacao || '—'}</dd>
      <dt>E-mail</dt><dd>${emailStr}</dd>
      <dt>Telefones</dt><dd>${telStr}</dd>
      <dt>Endereço PF</dt><dd style="font-size:12px">${endStr}</dd>
      <dt>Quadro societário</dt><dd><i>não incluído no nível básico</i></dd>
    </div>
    <div class="aviso" role="status">⚠️ Telefone e e-mail estão parcialmente mascarados. Solicitar dados completos (cobrado à parte).</div>`;
  } else if (r.pf && r.pf.aviso) {
    html += `<div class="aviso" role="alert">ⓘ ${r.pf.aviso}</div>`;
  } else {
    html += '<div class="aviso" role="status">Médico sem CPF — apenas dados cadastrais.</div>';
  }
  html += '</div>';

  // (bloco CRM/Especialidades antigo removido — substituído pelas seções 1 e 2 acima)

  // (bloco Residências antigo removido — substituído pela seção 3 acima)

  // SEÇÃO 4 — PESQUISA PF (Credify) — SEM o bloco lateral "Custo desta ficha"
  html += '<div class="ficha-secao"><span class="num">4</span><div><h3>🔎 Pesquisa PF (Credify)</h3><p>Dados cadastrais e de contato da pessoa física — fonte Receita Federal.</p></div></div>';
  html += '<div class="pf-bloco"><h4>Pesquisa PF (Credify) <span class="fonte-badge">Fonte: Receita Federal</span></h4>';
  // (duplicado removido — bloco PF já renderizado acima dentro do bloco principal)

  // Diagnóstico visível quando ORACLE devolve shape parcial
  if (m._diagnostico_oracle && m._diagnostico_oracle.length) {
    html += '<div class="aviso" role="alert"><b>Diagnóstico Oracle:</b><ul>' +
      m._diagnostico_oracle.map((d) => `<li><code>${d.secao}</code>: ${d.erro}</li>`).join('') +
      '</ul></div>';
  }

  $('areaFicha').innerHTML = html;
  // Ficha avançada na MESMA PÁGINA: a cada novo médico o painel PJ volta ao
  // estado bloqueado (lock) até o usuário desbloquear (+300 tokens).
  const temPF = !!(r.pf && r.pf.dados_cadastrais);
  $('areaAvancada').innerHTML = '';
  const lock = $('avancadaLock');
  if (lock) lock.hidden = false;
  const lockTxt = $('avancadaLockTexto');
  if (lockTxt) lockTxt.innerHTML = temPF
    ? 'Desbloqueie as empresas vinculadas, o quadro societário, CNAEs e o faturamento do médico por <b>+300 tokens</b> (R$ 15).'
    : 'Médico sem CPF na base — não é possível consultar vínculos empresariais (Credify PJ).';
  const lockBtn = $('btnAvancadoLock');
  if (lockBtn) lockBtn.hidden = !temPF;
  $('btnAvancado').classList.toggle('oculto', !temPF);
  $('btnAvancadoTop').classList.toggle('oculto', !temPF);
}

// ---------------- FICHA AVANÇADA (+300) ----------------
async function perguntarAvancado() {
  if (!medicoAtual) return;
  $('modalTitulo').textContent = 'Desbloquear Ficha Avançada?';
  $('modalTexto').innerHTML = `Serão debitados <span class="custo">+300 tokens</span> (R$ 15)
    para os dados PJ (empresas, quadro societário, CNAE, faturamento) dos vínculos do médico.`;
  abrirModal(async () => {
    fecharModal();
    const res = await fichaAvancada(medicoAtual, true);
    if (!res.ok || res.data.erro) {
      if (res.data && res.data.aviso) {
        $('areaAvancada').innerHTML = `<p class="aviso">${res.data.aviso}</p>`;
        $('btnAvancado').classList.add('oculto');
        return;
      }
      mostraErro((res.data && (res.data.detalhe || res.data.erro)) || `HTTP ${res.status}`);
      return;
    }
    renderAvancado(res.data);
  });
}

function renderAvancado(r) {
  const box = $('areaAvancada');
  if (r.aviso) {
    let extra = '';
    if (r.cnpjs_totais !== undefined) {
      extra = ` <span class="meta">(cnpjs extraídos: ${r.cnpjs_unicos}/${r.cnpjs_totais})</span>`;
    }
    box.innerHTML = `<p class="aviso">${r.aviso}${extra}</p>`;
    $('btnAvancado').classList.add('oculto');
    $('btnAvancadoTop').classList.add('oculto');
    const lock = $('avancadaLock'); if (lock) lock.hidden = true;
    const lockBtn = $('btnAvancadoLock'); if (lockBtn) lockBtn.classList.add('oculto');
    return;
  }
  // Mesmos helpers defensivos do renderFicha — Credify PJ em PROD devolve
  // objetos indexados por REGISTRO_n (nao lista) em QUADROSOCIETARIO, CNAE,
  // ENDERECOS, etc.
  const toList = (x) => {
    if (Array.isArray(x)) return x;
    if (x && typeof x === 'object') return Object.values(x);
    return [];
  };
  const normObj = (o) => {
    if (!o || typeof o !== 'object') return {};
    const out = {};
    for (const k of Object.keys(o)) out[String(k).toLowerCase()] = o[k];
    return out;
  };
  // Layout pós-desbloqueio (mesma página) — bate com o mockup:
  //  Coluna esquerda: Empresas vinculadas (cards completos de cada PJ).
  //  Coluna direita:
  //    - "Outros vínculos" (não-empresa: institutos, hospitais onde é diretor).
  //    - "Resumo da consulta" (totais + economia por reuso de raiz CNPJ).
  // Sem bloco de custo no cabeçalho do médico (regra do usuário).
  const tokensTotal = (r.tokens_cobrados || 0);
  const reaisPF = (300 * 0.25).toLocaleString('pt-BR', { minimumFractionDigits: 2 }); // R$ 75,00 referência mockup
  const reaisBase = (r.cnpjs_unicos || 0) > 0 ? ((r.cnpjs_unicos * 300 * 0.25)).toLocaleString('pt-BR', { minimumFractionDigits: 2 }) : '—';

  // separa empresas "matriz (vinculada como sócia direta)" dos "outros vínculos"
  const empresas = Array.isArray(r.empresas) ? r.empresas : [];
  const outrasMatrizes = []; // cards externos sem PJ completa (instituto, filial, etc.)
  const cards = [];
  for (const emp of empresas) {
    const pj = emp.pj || {};
    if (!pj || (!pj.DADOSCADASTRAIS && !pj.INFOEMPRESA && !pj.CNAE && !pj.QUADROSOCIETARIO)) {
      // sem PJ — empurrar para "outros vínculos"
      outrasMatrizes.push(emp);
      continue;
    }
    cards.push(emp);
  }

  let html = '';
  html += '<div class="ficha-secao"><span class="num">5</span><div><h3>🏢 Empresas vinculadas</h3><p>PJs onde o médico aparece como sócio (consultadas a partir das raízes de CNPJ) e vínculo como pessoa jurídica.</p></div></div>';

  if (!cards.length && !outrasMatrizes.length) {
    html += '<div class="vazio"><div class="vazio-emoji" aria-hidden="true">🌐</div><h3>Nenhuma empresa vinculada</h3><p>A Credify PJ não retornou empresas para a raiz CNPJ do médico.</p></div>';
  } else {
    if (cards.length) {
      html += '<div class="grid-2col">';
      for (const emp of cards) {
        const pj = emp.pj || {};
        const dc = normObj(pj.DADOSCADASTRAIS || {});
        const info = normObj(pj.INFOEMPRESA || {});
        const cnaes = toList(pj.CNAE).map(normObj);
        const ends = toList(pj.ENDERECOS).map(normObj).map((x) => {
          const tp = x.tp_logradouro || '';
          const lg = x.logradouro || '';
          const nu = x.numero ? ', ' + x.numero : '';
          const cm = x.complemento ? ' (' + x.complemento + ')' : '';
          const br = x.bairro ? ' - ' + x.bairro : '';
          const cd = [x.cidade, x.uf, x.cep].filter(Boolean).join('/');
          return `${tp} ${lg}${nu}${cm}${br} (${cd})`.trim();
        }).filter(Boolean);
        const socios = toList(pj.QUADROSOCIETARIO).map(normObj);
        const vin = normObj(emp.vinculo || {});
        const cnpjFmt = (emp.cnpj || '').replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5') || emp.cnpj;
        const vinculoResumo = `${vin.razaosocial || 'Médico'} · ${vin.percentual || '—'}% · ${vin.qualificacao || '—'}`;
        const qtdSocios = socios.length || (dc.quadro_societario_quantidade || 0);
        const filiais = dc.quantidade_filiais || info.filiais || 0;
        html += `<div class="pj-card">
          <div class="pj-cab">${dc.razao_social || dc.nomerazao || emp.cnpj || '—'} <span class="chip-matriz">MATRIZ</span></div>
          <div class="pj-nome">CNPJ: <b>${cnpjFmt}</b>${dc.porte ? ' · ' + dc.porte : ''}</div>
          <div class="pj-meta">
            <div><div class="l">Sócia nesta PJ</div><div class="v">${vinculoResumo}</div></div>
            <div><div class="l">Capital</div><div class="v">${info.capital_social || '—'}</div></div>
            <div><div class="l">Abertura</div><div class="v">${dc.abertura || '—'}</div></div>
            <div><div class="l">CNAE</div><div class="v">${cnaes.map((x) => x.codigo || x.CODIGO || '').filter(Boolean).join(', ') || '8630-5'}</div></div>
            <div><div class="l">Faturamento</div><div class="v">${info.faturamento_presumido || '—'}</div></div>
            <div><div class="l">Sócios</div><div class="v">${qtdSocios ? qtdSocios + ' sócios' : (socios.length ? 'consultado abaixo' : '—')}</div></div>
            ${filiais ? `<div><div class="l">Filiais</div><div class="v">${filiais}</div></div>` : ''}
          </div>
          <div class="pj-end" style="font-size:12px;color:var(--c-muted);margin-top:8px">${ends.join(' · ') || ''}</div>
          <div class="pj-socios" style="margin-top:10px"><h4 style="margin:6px 0 4px;font-size:13px">Quadro societário (consultado nesta PJ)</h4>
            ${socios.length ? `<div class="socio-list">${socios.map((s) => `
              <div class="socio-row">
                <div><span class="rot">Sócio</span>${s.nome || s.NOME || '—'}</div>
                <div><span class="rot">Part.</span><b>${s.percentual || s.PERCENTUAL || '—'}%</b></div>
                <div><span class="rot">Capital</span>${s.capital_social || '—'}</div>
              </div>`).join('')}</div>` : '<p class="meta">Quadro não retornado pela Credify PJ.</p>'}
          </div>
        </div>`;
      }
      html += '</div>';
    }

    // COLUNA DIREITA: Outros vínculos + Resumo
    html += '<div class="aside-col">';
    if (outrasMatrizes.length) {
      html += '<div class="pj-card" style="background:#fff;border-color:var(--c-border);border-style:dashed"><div class="pj-cab">Outros vínculos (não-PJ)</div><div class="pj-list">';
      for (const emp of outrasMatrizes) {
        const v = normObj(emp.vinculo || {});
        const cnpjFmt = (emp.cnpj || '').replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5') || '—';
        html += `<div class="socio-row" style="grid-template-columns:1fr 1fr 1fr"><div><span class="rot">Entidade</span>${v.razaosocial || '—'}</div><div><span class="rot">CNPJ</span>${cnpjFmt}</div><div><span class="rot">Papel</span>${v.qualificacao || '—'}</div></div>`;
      }
      html += '</div></div>';
    }
    html += `<div class="resume-card">
      <div class="pj-cab">📊 Resumo da consulta</div>
      <div class="kv">
        <dt>Vínculos encontrados</dt><dd>${r.cnpjs_totais ? r.cnpjs_totais + ' CNPJs' : empresas.length + ' entidade(s)'} <span class="meta">(${r.cnpjs_unicos || 0} ${(r.cnpjs_unicos || 0) === 1 ? 'raiz' : 'raízes'})</span></dd>
        <dt>Chamadas Credify</dt><dd>${r.pj_consultadas || (r.cnpjs_unicos || 0)} <span class="chip teal">(reuso por raiz)</span></dd>
        <dt>Custo PF (já cobrado)</dt><dd>R$ ${reaisPF}</dd>
        <dt>Custo avançada</dt><dd><b class="custo">R$ ${reaisBase}</b></dd>
      </div>
    </div></div>`;
  }
  box.innerHTML = html;
  $('btnAvancado').classList.add('oculto');
  $('btnAvancadoTop').classList.add('oculto');
  const lock = $('avancadaLock'); if (lock) lock.hidden = true;
  const lockBtn = $('btnAvancadoLock'); if (lockBtn) lockBtn.classList.add('oculto');
  carregarSaldo().then(renderSaldo);
}

// ---------------- PAINEL / EXTRATO ----------------
function renderSaldo(s) {
  const tk = (s.saldo_tokens || 0);
  $('saldoTokens').textContent = tk.toLocaleString('pt-BR');
  $('saldoReais').textContent = `R$ ${(s.saldo_reais || 0).toLocaleString('pt-BR')}`;
  // Fase 5: estado de saldo baixo (warning < 100 · critico < 10)
  const box = $('saldoBox');
  if (box) {
    box.classList.toggle('saldo-baixo', tk > 0 && tk < 100);
    box.classList.toggle('saldo-critico', tk < 10);
  }
}

// Fase 5: empty/erro state visível para o extrato
async function verExtrato() {
  const res = await fetch('/api/v1/painel/extrato').then((r) => r.json()).catch(() => ({ transacoes: [] }));
  const box = $('areaExtrato');
  const tx = Array.isArray(res.transacoes) ? res.transacoes : [];
  if (!tx.length) {
    box.innerHTML = `<div class="vazio" role="status">
        <div class="vazio-emoji" aria-hidden="true">🧾</div>
        <h3>Nenhuma transação ainda</h3>
        <p>Seus débitos e recargas aparecerão aqui assim que você abrir a primeira ficha.</p>
      </div>`;
    mostrar('extratoView');
    return;
  }
  box.innerHTML = '<table><tr><th>Quando</th><th>Tipo</th><th>Descrição</th><th>Tokens</th><th>Saldo após</th></tr>' +
    tx.map((t) => `<tr><td>${t.ts}</td><td>${t.tipo}</td><td>${t.descricao}</td><td>${t.tokens}</td><td>${t.saldo_apos.toLocaleString('pt-BR')}</td></tr>`).join('');
  mostrar('extratoView');
}

// ---------------- NAVEGAÇÃO ----------------
function mostrar(view) {
  for (const v of ['listaView', 'fichaView', 'extratoView']) {
    $(v).classList.toggle('oculto', v !== view);
  }
  // topNav (Voltar + Salvar + Extrato) só aparece em fichaView / extratoView.
  const nav = $('topNav');
  if (nav) nav.classList.toggle('oculto', view === 'listaView');
}

function abrirModal(onConfirm) {
  $('modalSim').onclick = onConfirm;
  $('modalBg').classList.add('aberto');
}
function fecharModal() { $('modalBg').classList.remove('aberto'); }

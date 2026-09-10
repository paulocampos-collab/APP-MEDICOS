import { carregarSaldo, buscarMedicos, fichaBasica, fichaAvancada } from './api.js';

const $ = (id) => document.getElementById(id);
let medicoAtual = null;

document.addEventListener('DOMContentLoaded', () => {
  carregarSaldo().then(renderSaldo);
  $('btnBuscar').addEventListener('click', buscar);
  $('btnVoltar').addEventListener('click', () => mostrar('listaView'));
  $('btnExtrato').addEventListener('click', verExtrato);
  $('btnAvancado').addEventListener('click', perguntarAvancado);
  $('modalNao').addEventListener('click', fecharModal);
  buscar();
});

function mostraErro(mensagem) {
  const box = $('listaLeads');
  if (box) box.innerHTML = `<div class="erro"><b>Falha na consulta.</b> ${mensagem}</div>`;
}

function renderModo(data) {
  const el = $('modoBadge');
  if (!el) return;
  el.textContent = data && data.modo === 'oracle' ? 'ORACLE' : 'MOCK';
}

// ---------------- LISTA ----------------
async function buscar() {
  const f = {
    uf: $('fUf').value, cidade: $('fCidade').value,
    especialidade: $('fEspec').value, residencia: $('fResid').value,
    situacao_crm: $('fSit').value, sexo: $('fSexo').value,
    faixa_etaria: $('fFaixa').value,
    apenas_com_enriquecimento: $('fEnr').checked,
  };
  const res = await buscarMedicos(f);
  renderModo(res.data);
  if (!res.ok) {
    const det = (res.data && (res.data.detalhe || res.data.erro)) || '';
    mostraErro(`HTTP ${res.status || '?'} ${det}`);
    return;
  }
  renderLeads(Array.isArray(res.data.resultados) ? res.data.resultados : [], res.data);
}

function renderLeads(leads, data) {
  const box = $('listaLeads');
  box.innerHTML = '';
  if (data && data.erro) { mostraErro(`${data.erro} — ${data.detalhe || ''}`); return; }
  if (!leads.length) {
    box.innerHTML = '<p class="aviso">Nenhum médico encontrado com esses filtros.</p>';
    return;
  }
  for (const l of leads) {
    const el = document.createElement('div');
    el.className = 'lead';
    const chips = (l.especialidades || []).map((e) => `<span class="chip teal">${e}</span>`).join('');
    el.innerHTML = `
      <span class="tag-enr">${l.tem_enriquecimento ? 'PF/PJ' : 'só base'}</span>
      <h3>${l.nome_anonimizado}</h3>
      <div>${chips}</div>
      <div class="meta">${l.cidade || '—'} / ${l.uf || '—'} · ${l.bairro || ''}<br>
        CRM: <b>${l.situacao_crm || '—'}</b> · ${l.faixa_etaria || '—'} · ${l.sexo || '—'}</div>`;
    el.addEventListener('click', () => perguntarAbrirFicha(l.id_medico));
    box.appendChild(el);
  }
}

// ---------------- FICHA BÁSICA (débito por perfil) ----------------
async function perguntarAbrirFicha(id) {
  medicoAtual = id;
  const o = await fichaBasica(id); // sem confirmar: só mostra o custo
  if (!o.ok || o.data.erro) {
    mostraErro(o.data.detalhe || o.data.erro || `HTTP ${o.status}`);
    return;
  }
  const r = o.data;
  const real = { GENERALISTA: 'R$ 35', ESPECIALISTA: 'R$ 100', SUB_ESPECIALISTA: 'R$ 200' }[r.perfil];
  $('modalTitulo').textContent = 'Abrir ficha deste lead?';
  $('modalTexto').innerHTML = `Perfil <b>${r.perfil}</b> — será debitado
    <span class="custo">${r.custo_tokens.toLocaleString('pt-BR')} tokens</span> (${real}).<br><br>
    Depois de abrir, a Ficha Avançada (PJ — empresas e sócios) custa <b>+300 tokens</b>.`;
  abrirModal(async () => {
    fecharModal();
    const fo = await fichaBasica(medicoAtual, true);
    if (!fo.ok || fo.data.erro) {
      mostraErro(fo.data.detalhe || fo.data.erro || `HTTP ${fo.status}`);
      return;
    }
    renderFicha(fo.data);
    mostrar('fichaView');
    carregarSaldo().then(renderSaldo);
  });
}

function renderFicha(r) {
  const m = r.dados_medico;
  let html = `<div class="bloco"><h4>Médico (base)</h4><div class="kv">
      <dt>Nome</dt><dd>${m.nome}</dd>
      <dt>Perfil</dt><dd><span class="chip">${r.perfil}</span>
        <span class="chip teal">${r.tokens_cobrados.toLocaleString('pt-BR')} tokens debitados</span></dd>
      <dt>Faculdade</dt><dd>${m.instituicao_graduacao || '—'} (${m.ano_conclusao || '—'})</dd>
    </div></div>`;

  html += `<div class="bloco"><h4>CRMs por UF</h4><table><tr><th>CRM</th><th>UF</th><th>Situação</th></tr>`;
  for (const c of m.crms || []) html += `<tr><td>${c.crm}</td><td>${c.uf}</td><td>${c.situacao}</td></tr>`;
  html += '</table></div>';

  html += '<div class="bloco"><h4>Especialidades / RQE</h4>';
  const espSet = new Set();
  for (const lista of Object.values(m.especialidades || {})) for (const e of lista) {
    const key = `${e.especialidade}|${e.rqe || ''}|${e.flag_sub ? 1 : 0}`;
    if (espSet.has(key)) continue;
    espSet.add(key);
    html += `<span class="chip">${e.especialidade}</span>`;
    if (e.rqe) html += `<span class="chip teal">RQE ${e.rqe}</span>`;
    if (e.flag_sub || e.id_esp_sub) html += `<span class="chip amber">sub</span>`;
  }
  html += '</div>';

  if (m.residencias && m.residencias.length) {
    html += '<div class="bloco"><h4>Residências</h4>';
    for (const x of m.residencias) html += `<span class="chip teal">${x.programa} · ${x.instituicao}</span> `;
    html += '</div>';
  }

  html += '<div class="bloco"><h4>Pesquisa PF (Credify)</h4>';
  if (r.pf && r.pf.dados_cadastrais) {
    html += `<div class="kv">
      <dt>Nome PF</dt><dd>${r.pf.dados_cadastrais.NOME || '—'}</dd>
      <dt>Nascimento</dt><dd>${r.pf.dados_cadastrais.NASCIMENTO || '—'}</dd>
      <dt>E-mail</dt><dd>${(r.pf.emails || []).map((x) => x.ENDERECO).join(', ') || '—'}</dd>
      <dt>Telefones</dt><dd>${(r.pf.telefones || []).map((x) => `(${x.DDD}) ${x.NUMERO}`).join(', ') || '—'}</dd>
      <dt>Endereço PF</dt><dd>${(r.pf.enderecos || []).map((x) => x.LOGRADOURO).join('; ') || '—'}</dd>
      <dt>Quadro societário</dt><dd><i>não exibido no nível básico</i></dd>
    </div>`;
  } else if (r.pf && r.pf.aviso) {
    html += `<p class="aviso">${r.pf.aviso}</p>`;
  } else {
    html += '<p class="aviso">Médico sem CPF resolvido na base — apenas dados cadastrais, sem débito de enriquecimento.</p>';
  }
  html += '</div>';

  $('areaFicha').innerHTML = html;
  $('areaAvancada').innerHTML = '';
  const temPF = !!(r.pf && r.pf.dados_cadastrais);
  $('btnAvancado').classList.toggle('oculto', !temPF);
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
    box.innerHTML = `<p class="aviso">${r.aviso}</p>`;
    $('btnAvancado').classList.add('oculto');
    return;
  }
  let html = `<p class="meta">${r.tokens_cobrados.toLocaleString('pt-BR')} tokens debitados por esta abertura</p>`;
  for (const emp of r.empresas || []) {
    const pj = emp.pj || {};
    const dc = pj.DADOSCADASTRAIS || {};
    const info = pj.INFOEMPRESA || {};
    html += `<div class="bloco"><h4>${dc.RAZAO_SOCIAL || emp.cnpj}</h4><div class="kv">
        <dt>CNPJ</dt><dd>${emp.cnpj || '—'}</dd>
        <dt>Porte</dt><dd>${dc.PORTE || '—'} · ${dc.SITUACAO || '—'}</dd>
        <dt>Abertura</dt><dd>${dc.ABERTURA || '—'}</dd>
        <dt>CNAE</dt><dd>${(pj.CNAE || []).map((x) => `${x.CODIGO} — ${x.DESCRICAO}`).join('; ') || '—'}</dd>
        <dt>Faturamento</dt><dd>${info.FATURAMENTO_PRESUMIDO || '—'}</dd>
        <dt>Capital</dt><dd>${info.CAPITAL_SOCIAL || '—'}</dd>
        <dt>Endereço</dt><dd>${(pj.ENDERECOS || []).map((x) => x.LOGRADOURO).join('; ') || '—'}</dd>
      </div><h4 style="margin-top:10px">Quadro societário</h4><table>
        <tr><th>Nome</th><th>CPF/CNPJ</th><th>Qualificação</th><th>%</th></tr>
        ${(pj.QUADROSOCIETARIO || []).map((s) => `<tr><td>${s.NOME}</td><td>${s.CPF_CNPJ}</td><td>${s.QUALIFICACAO}</td><td>${s.PERCENTUAL || '—'}</td></tr>`).join('')}
      </table></div>`;
  }
  box.innerHTML = html;
  $('btnAvancado').classList.add('oculto');
  carregarSaldo().then(renderSaldo);
}

// ---------------- PAINEL / EXTRATO ----------------
function renderSaldo(s) {
  $('saldoTokens').textContent = (s.saldo_tokens || 0).toLocaleString('pt-BR');
  $('saldoReais').textContent = `R$ ${(s.saldo_reais || 0).toLocaleString('pt-BR')}`;
}

async function verExtrato() {
  const res = await fetch('/api/v1/painel/extrato').then((r) => r.json()).catch(() => ({ transacoes: [] }));
  const box = $('areaExtrato');
  const tx = Array.isArray(res.transacoes) ? res.transacoes : [];
  box.innerHTML = tx.length
    ? '<table><tr><th>Quando</th><th>Tipo</th><th>Descrição</th><th>Tokens</th><th>Saldo após</th></tr>' +
      tx.map((t) => `<tr><td>${t.ts}</td><td>${t.tipo}</td><td>${t.descricao}</td><td>${t.tokens}</td><td>${t.saldo_apos.toLocaleString('pt-BR')}</td></tr>`).join('')
    : '<p class="meta">Nenhuma transação ainda.</p>';
  mostrar('extratoView');
}

// ---------------- NAVEGAÇÃO ----------------
function mostrar(view) {
  for (const v of ['listaView', 'fichaView', 'extratoView']) {
    $(v).classList.toggle('oculto', v !== view);
  }
  $('btnVoltar').classList.toggle('oculto', view === 'listaView');
}

function abrirModal(onConfirm) {
  $('modalSim').onclick = onConfirm;
  $('modalBg').classList.add('aberto');
}
function fecharModal() { $('modalBg').classList.remove('aberto'); }

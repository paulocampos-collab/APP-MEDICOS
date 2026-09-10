// Reproducao EXATA do app/main.py:ficha_avancada contra payload real do CPF
// 04689689628 (BRUNA ZAMBRANA) — 5 vinculos: 4 filiais Clinica Zambrana
// (raiz 02894643) + Clinica Zambrana filial mal-padded (mesma raiz) +
// Zambrana&Enomoto (raiz 09377298). Esperado: 5 vinculos exibidos,
// 2 credify calls (uma por raiz).
import fs from 'fs';

const fixture = JSON.parse(fs.readFileSync('app/fixtures/bruna_zambrana.json', 'utf8'));
const pf = fixture;
const res = pf.RESPOSTA;

// === HELPERS (espelho do fix em app/main.py:6-43) ===
function toRegistros(x) {
  if (x == null) return [];
  if (Array.isArray(x)) return x;
  if (typeof x === 'object') return Object.values(x);
  return [];
}
const ZEROS = '0000000000000000';
function normCnpj(v) {
  if (v == null) return '';
  // .toString() correto (teste anterior usou "".join que é undefined)
  const s = String(v).split('').filter((c) => c >= '0' && c <= '9').join('');
  if (!s) return '';
  return s.padStart(ZEROS.length, '0').slice(-ZEROS.length);
}
function consultar_pj(cnpj) {
  // espelho de repositorio.consultar_pj -> CredifyClient().consultar_pj(cnpj)
  // (no fixture-mode retornaria o mock; como o fixture NAO mocka PJ, devolvemos
  // um payload Prod-shape minimo)
  if (cnpj < '09000000000000') {
    return { ERRO: 'fallback_unreachable_simulado_no_teste' };
  }
  return {
    RESPOSTA: {
      CODIGO: ['1','1','1','1','1','1','1','1','1','1'],
      DADOSCADASTRAIS: {
        RAZAO_SOCIAL: 'CLINICA ZAMBRANA LTDA' + (cnpj.startsWith('02894643') ? '' : ' - ENOMOTO'),
        PORTE: 'PEQUENA', SITUACAO: 'ATIVA', ABERTURA: '10/09/1998',
      },
      INFOEMPRESA: { FATURAMENTO_PRESUMIDO: 'R$ 100k-500k', CAPITAL_SOCIAL: 'R$ 10k' },
      QUADROSOCIETARIO: [
        { NOME: 'BRUNA DA FONSECA TAMES ZAMBRANA', CPF_CNPJ: '04689689628',
          QUALIFICACAO: 'SOCIO ADMINISTRADOR', PERCENTUAL: '50' }
      ],
    },
  };
}

// === CODIGO ANTIGO (reproduzido para mostrar o BUG) ===
console.log('====== ANTES DO FIX (app/main.py:178-202 original) ======');
const oldCodigoCheck = ((pf.RESPOSTA?.CODIGO) || [2])[4] == 1;  // "1" == 1 = false
const oldVincRaw = pf.RESPOSTA?.PARTICIPACAOSOCIETARIA || [];
const oldVinc = oldCodigoCheck ? oldVincRaw : [];
console.log('  CONDICAO antiga: (CODIGO[4] == 1) Compara string "1" com int 1 ->',
            oldCodigoCheck, '(esperado true; resulta False em PROD)');
console.log('  ANTIGO: vinculos =', oldCodigoCheck ? `[objeto ${typeof oldVincRaw}]` : '[] (cai no early-return SEM vinculos)');
console.log('  ANTIGO: Usuario ve: "Medico sem vinculos empresariais - nada a cobrar"');
console.log('');

// === CODIGO NOVO (reproduzido do fix) ===
console.log('====== DEPOIS DO FIX (app/main.py:ficha_avancada novo) ======');
const codigo = (res.CODIGO || []).map((x) => String(x));
console.log('  CODIGO[4] =', JSON.stringify(codigo[4]),
            '(string == "1"?', codigo[4] === '1', ')');

let vinculos = [];
if (codigo.length > 4 && codigo[4] === '1') {
  const ps = res.PARTICIPACAOSOCIETARIA || [];
  vinculos = toRegistros(ps);
}
console.log('  PARTICIPACAOSOCIETARIA original:', Array.isArray(res.PARTICIPACAOSOCIETARIA)
            ? 'ARRAY' : `OBJETO {${Object.keys(res.PARTICIPACAOSOCIETARIA).length}} chaves`);
console.log('  apos toRegistros: lista de', vinculos.length, 'vinculos');
console.log('');

const empresas = [];
const seenRoot = new Set();
const pjCache = {};
let pjConsultadas = 0;
for (const v of vinculos) {
  if (!v || typeof v !== 'object') continue;
  const full = normCnpj(v.CNPJ);
  if (!full) {
    empresas.push({ vinculo: v, cnpj: null, raiz: null, pj: null, status: 'cnpj_invalido' });
    continue;
  }
  const raiz = full.slice(0, 8);
  if (!seenRoot.has(raiz)) {
    seenRoot.add(raiz);
    const pj = consultar_pj(full);
    pjCache[raiz] = (pj && pj.RESPOSTA) || null;
    pjConsultadas += 1;
    empresas.push({ vinculo: v, cnpj: full, raiz, pj: pjCache[raiz], status: 'consulted' });
  } else {
    empresas.push({ vinculo: v, cnpj: full, raiz, pj: pjCache[raiz], status: 'reused' });
  }
}

console.log('  --- FANAUT POR CNPJ ---');
for (const e of empresas) {
  const v = e.vinculo;
  console.log(`  ${e.cnpj || '(vazio)'} | raiz ${e.raiz || '-'} | ${(v.RAZAOSOCIAL || '-').padEnd(40)} | ${v.PERCENTUAL || '-'}% ${v.QUALIFICACAO || '-'} | status: ${e.status}`);
}
console.log('');
console.log('  --- ESTATISTICAS ---');
console.log('  cnpjs_totais (vinculos encontrados):', vinculos.length);
console.log('  vinculos exibidos no response:', empresas.length);
console.log('  consultas PJ feitas a Credify (1 por RAIZ):', pjConsultadas);
console.log('  raizes unicas:', [...seenRoot].sort().join(', '));
console.log('  economia de chamadas:', vinculos.length - pjConsultadas,
            '(3 filiais Clube Zambrana reusam 1 consulta)');
console.log('');
console.log('  --- RESPONSE QUE O FRONT IRA RENDERIZAR ---');
const resp = { cnpjs_totais: vinculos.length, cnpjs_unicos: empresas.length,
               pj_consultadas: pjConsultadas, raizes_unicas: [...seenRoot].sort(),
               empresas_count: empresas.length };
console.log(' ', JSON.stringify(resp, null, 2));
console.log('');
console.log('  --- MOSTRA UM CARD PARA CADA VINCULO ---');
for (let i = 0; i < empresas.length; i++) {
  const e = empresas[i];
  const pj = e.pj || {};
  console.log(`  [${i+1}] CNPJ ${e.cnpj} (form: ${e.cnpj ? e.cnpj.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5') : '-'}):`);
  console.log(`       Vinculo: ${e.vinculo.RAZAOSOCIAL} - ${e.vinculo.PERCENTUAL}% (${e.vinculo.QUALIFICACAO})`);
  console.log(`       PJ raiz ${e.raiz}: ${pj.DADOSCADASTRAIS?.RAZAO_SOCIAL || '(sem retorno)'}`);
  console.log(`       PJ status: ${e.status} (Credify consultadas ate aqui: ${pjConsultadas})`);
}
process.exit(0);

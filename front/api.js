const BASE = '/api/v1';

/** fetch + extração segura do JSON. Nunca lança erro de parse; devolve {ok,status,data}. */
async function get(url) {
  try {
    const r = await fetch(url);
    const data = await r.json().catch(() => ({}));
    return { ok: r.ok, status: r.status, data };
  } catch (e) {
    return { ok: false, status: 0, data: { detalhe: String(e) } };
  }
}

export async function carregarSaldo() {
  const o = await get(`${BASE}/painel/saldo`);
  return o.data || {};
}

export async function buscarMedicos(filtros) {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(filtros)) {
    if (v !== '' && v !== null && v !== undefined && v !== false) q.set(k, v);
  }
  return get(`${BASE}/medicos?${q.toString()}`);
}

export async function fichaBasica(id, confirmar = false) {
  return get(`${BASE}/medicos/${id}/ficha-basica?confirmar=${confirmar}`);
}

export async function fichaAvancada(id, confirmar = false) {
  return get(`${BASE}/medicos/${id}/ficha-avancada?confirmar=${confirmar}`);
}

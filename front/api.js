const BASE = '/api/v1';

export async function carregarSaldo() {
  const r = await fetch(`${BASE}/painel/saldo`);
  return r.json();
}

export async function buscarMedicos(filtros) {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(filtros)) {
    if (v !== '' && v !== null && v !== undefined && v !== false) q.set(k, v);
  }
  const r = await fetch(`${BASE}/medicos?${q.toString()}`);
  return r.json();
}

export async function fichaBasica(id, confirmar = false) {
  const r = await fetch(`${BASE}/medicos/${id}/ficha-basica?confirmar=${confirmar}`);
  return r.json();
}

export async function fichaAvancada(id, confirmar = false) {
  const r = await fetch(`${BASE}/medicos/${id}/ficha-avancada?confirmar=${confirmar}`);
  return r.json();
}

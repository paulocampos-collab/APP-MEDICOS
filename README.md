# cnesfy — MVP de leads de médicos com créditos (tokens)

Fluxo do produto (fechado com o cliente):

1. **Busca grátis** — lista de leads **anonimizada** (nome mascarado; só especialidade,
   cidade/UF/bairro, situação do CRM, faixa etária, sexo), com filtros.
2. **Clique no lead → abre a ficha em nova página → débito por perfil**:
   Generalista **700** / Especialista **2.000** / Sub-especialista **4.000** tokens
   (taxa: 1 token = R$ 0,05; R$ 50.000 = 1.000.000 tokens).
3. **Ficha Básica** = dados do médico (base Oracle) + **Pesquisa PF (Credify)** com
   cadastrais, telefones, e-mails e endereços — **sem quadro societário**.
4. **Ficha Avançada** = desbloqueio por **+300 tokens**: **Pesquisa PJ (Credify)** com
   os vínculos empresariais do médico (quadro societário, CNAE, porte, faturamento).
5. Médico sem PF/PJ disponível → entrega o básico e **avisa, sem debitar** o que não veio.

> **Modo padrão: `USE_MOCK=true`** — roda 100% com dados de exemplo em
> `app/mock_data.py`, sem banco e sem chamadas reais. Ideal para apresentar o MVP.

---

## Como rodar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # USE_MOCK=true já é o default
uvicorn app.main:app --reload --port 8000
```

Abra <http://127.0.0.1:8000> — o front estático chama a API.

## Smoke test (curl)

```bash
curl "http://127.0.0.1:8000/api/v1/medicos"                       # lista anonimizada (grátis)
curl "http://127.0.0.1:8000/api/v1/medicos?uf=SP&situacao_crm=ATIVO"
curl "http://127.0.0.1:8000/api/v1/medicos/1/ficha-basica?confirmar=true"      # débito 2.000 (Especialista)
curl "http://127.0.0.1:8000/api/v1/medicos/1/ficha-avancada?confirmar=true"    # +300 (PJ)
curl "http://127.0.0.1:8000/api/v1/painel/saldo"
curl "http://127.0.0.1:8000/api/v1/painel/extrato"
```

---

## Conectar no Oracle real

No `.env`:
```
USE_MOCK=false
ORACLE_HOST=SEU_HOST        # ou ORACLE_DSN="host:porta/servico"
ORACLE_PORT=1521
ORACLE_SERVICE=SEU_SERVICO
ORACLE_USER=SEU_USUARIO
ORACLE_PASSWORD=SUA_SENHA
```
SQL das tabelas reais fica hardcoded em `app/db/queries.py` (sem ORM).
Tabelas usadas: `credpf.credi01300_new`, `credpf.credi01301`, `credpf.credi01302`,
`credpf.credi01303` e `Paulo.tmp_endereco_medico_principal` (melhor endereço:
tipo de endereço → completude → CEP → menor NU_ADDR).

## Conectar na Credify real (produção)

```
USE_MOCK=false
CREDIFY_CLIENT_ID=SEU_CLIENT_ID
CREDIFY_CLIENT_SECRET=SEU_CLIENT_SECRET
CREDIFY_BASE_URL=https://api.credify.com.br
```
Auth: `POST /auth` com `{ClientID, ClientSecret}` → token JWT no campo `Dados`
(válido 24h; o client guarda em cache e renova sozinho no 401).
Endpoints: `POST /pfpesquisa` (IdConsulta 328) e `POST /pjpesquisa` (IdConsulta 329).

## Estrutura

```
cnesfy/
├─ .env.example            # modelo de variáveis (só placeholders — sem segredos)
├─ .gitignore              # .env nunca vai pro git
├─ requirements.txt
├─ README.md
├─ app/
│  ├─ main.py              # FastAPI (rotas da API) + serve do front estático
│  ├─ config.py            # leitura do .env (pydantic-settings)
│  ├─ repositorio.py       # camada de dados: escolhe mock OU oracle
│  ├─ mock_data.py         # fixtures: médicos, endereços, payloads PF(328)/PJ(329)
│  ├─ db/
│  │  ├─ oracle.py         # pool oracledb (thin mode, sem cliente instalado)
│  │  └─ queries.py        # SQL hardcoded das tabelas reais
│  ├─ credify/
│  │  └─ client.py         # auth (cache 24h + refresh no 401) + chamadas PF/PJ
│  └─ services/
│     ├─ perfil.py         # deriva 700/2.000/4.000 a partir de RQE/SUB
│     ├─ endereco.py       # regra do melhor endereço
│     ├─ anonimizacao.py   # máscara de nome da lista
│     └─ tokens.py         # carteira mock: saldo em memória + extrato
└─ front/
   ├─ index.html
   ├─ style.css
   ├─ api.js
   └─ app.js
```

## Decisões já fechadas com o cliente

- 1 token = R$ 0,05 · R$ 50.000 = 1.000.000 tokens
- Generalista 700 · Especialista 2.000 · Sub-especialista 4.000 · Avançado +300
- Básico = base + PF (sem quadro societário) · Avançado = PJ completa
- Lista anonimizada grátis · débito só ao abrir a ficha (nova página)
- Sem enriquecimento → entrega o básico e avisa (sem débito do que não veio)

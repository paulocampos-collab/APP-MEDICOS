# ============================================================
# Fixtures mockadas (USE_MOCK=true) — espelham as tabelas reais
# e os payloads da Credify (PF IdConsulta 328 / PJ 329).
# Nenhuma credencial real aqui.
# ============================================================

# --- Médicos (credpf.credi01300_new) ---
MEDICOS = [
    {"id_medico": 1, "nome": "Maria Silva Santos", "nome_social": None, "cpf": "12345678901",
     "sexo": "F", "dt_nascimento": "1980-03-15", "ano_conclusao": 2004,
     "instituicao_graduacao": "USP", "nu_peop": 98765, "co_profissional_sus": "7001234"},
    {"id_medico": 2, "nome": "Joao Pereira Lima", "nome_social": None, "cpf": "23456789012",
     "sexo": "M", "dt_nascimento": "1975-08-02", "ano_conclusao": 1999,
     "instituicao_graduacao": "UNICAMP", "nu_peop": 87654, "co_profissional_sus": "7005678"},
    {"id_medico": 3, "nome": "Ana Costa Ribeiro", "nome_social": None, "cpf": "34567890123",
     "sexo": "F", "dt_nascimento": "1988-11-20", "ano_conclusao": 2012,
     "instituicao_graduacao": "UFMG", "nu_peop": 76543, "co_profissional_sus": None},
    {"id_medico": 4, "nome": "Carlos Mendes", "nome_social": None, "cpf": "45678901234",
     "sexo": "M", "dt_nascimento": "1960-02-10", "ano_conclusao": 1985,
     "instituicao_graduacao": "UFRJ", "nu_peop": 65432, "co_profissional_sus": None},
    {"id_medico": 5, "nome": "Fernanda Alves", "nome_social": None, "cpf": "56789012345",
     "sexo": "F", "dt_nascimento": "1992-06-05", "ano_conclusao": 2017,
     "instituicao_graduacao": "UFBA", "nu_peop": 54321, "co_profissional_sus": "7009999"},
    {"id_medico": 6, "nome": "Roberto Nunes", "nome_social": None, "cpf": None,
     "sexo": "M", "dt_nascimento": "1970-12-01", "ano_conclusao": 1994,
     "instituicao_graduacao": "UFRGS", "nu_peop": None, "co_profissional_sus": None},
]

# --- CRMs (credpf.credi01301) ---
CRMS = {
    1: [{"id_crm": 101, "crm": "123456", "uf": "SP", "situacao": "ATIVO", "dt_prim_inscricao_uf": "2005-01-10"}],
    2: [{"id_crm": 201, "crm": "654321", "uf": "RJ", "situacao": "ATIVO", "dt_prim_inscricao_uf": "2000-06-01"},
        {"id_crm": 202, "crm": "987654", "uf": "SP", "situacao": "ATIVO", "dt_prim_inscricao_uf": "2001-02-14"}],
    3: [{"id_crm": 301, "crm": "111222", "uf": "MG", "situacao": "ATIVO", "dt_prim_inscricao_uf": "2013-03-20"}],
    4: [{"id_crm": 401, "crm": "333444", "uf": "PR", "situacao": "SUSPENSO", "dt_prim_inscricao_uf": "1986-08-01"}],
    5: [{"id_crm": 501, "crm": "555666", "uf": "BA", "situacao": "ATIVO", "dt_prim_inscricao_uf": "2018-05-11"}],
    6: [{"id_crm": 601, "crm": "777888", "uf": "RS", "situacao": "ATIVO", "dt_prim_inscricao_uf": "1995-09-09"}],
}

# --- Especialidades (credpf.credi01302) ---
ESPECIALIDADES = {
    101: [{"especialidade": "Cardiologia", "rqe": "12345", "flag_sub": 0, "id_esp_sub": None}],
    201: [{"especialidade": "Cardiologia", "rqe": "23456", "flag_sub": 0, "id_esp_sub": None},
          {"especialidade": "Hemodinamica", "rqe": "23457", "flag_sub": 1, "id_esp_sub": 201}],
    202: [{"especialidade": "Cardiologia", "rqe": "23456", "flag_sub": 0, "id_esp_sub": None}],
    301: [{"especialidade": "Dermatologia", "rqe": "34567", "flag_sub": 0, "id_esp_sub": None}],
    401: [{"especialidade": "Clinica Medica", "rqe": None, "flag_sub": 0, "id_esp_sub": None}],
    501: [{"especialidade": "Pediatria", "rqe": "56789", "flag_sub": 0, "id_esp_sub": None}],
    601: [{"especialidade": "Clinica Medica", "rqe": None, "flag_sub": 0, "id_esp_sub": None}],
}

# --- Residencias (credpf.credi01303) ---
RESIDENCIAS = {
    1: [{"programa": "Cardiologia", "instituicao": "InCor - HC FMUSP", "sg_uf": "SP", "dt_inicio": "2005", "dt_termino": "2008"}],
    2: [{"programa": "Hemodinamica", "instituicao": "InCor - HC FMUSP", "sg_uf": "SP", "dt_inicio": "2008", "dt_termino": "2010"}],
    3: [{"programa": "Dermatologia", "instituicao": "Hospital das Clinicas UFMG", "sg_uf": "MG", "dt_inicio": "2013", "dt_termino": "2015"}],
    5: [{"programa": "Pediatria", "instituicao": "Hospital Martagao Gesteira", "sg_uf": "BA", "dt_inicio": "2018", "dt_termino": "2020"}],
}

# --- Enderecos (Paulo.tmp_endereco_medico_principal) ---
# CO_TYPE_ADDR: 1=residencial, 2=comercial, 3=correspondencia
ENDERECOS = {
    1: [{"nu_addr": 11, "co_type_addr": "1", "ds_name_logr": "Rua dos Pinheiros", "co_numb_logr": "100", "ds_cmpl_logr": "Apto 52", "ds_dist": "Pinheiros", "ds_city": "SAO PAULO", "co_stte": "SP", "co_zipc": "05422000"}],
    2: [{"nu_addr": 21, "co_type_addr": "2", "ds_name_logr": "Av. Atlantica", "co_numb_logr": "500", "ds_cmpl_logr": "Sala 901", "ds_dist": "Copacabana", "ds_city": "RIO DE JANEIRO", "co_stte": "RJ", "co_zipc": "22021001"},
        {"nu_addr": 22, "co_type_addr": "1", "ds_name_logr": "Rua das Laranjeiras", "co_numb_logr": "25", "ds_cmpl_logr": None, "ds_dist": "Laranjeiras", "ds_city": "RIO DE JANEIRO", "co_stte": "RJ", "co_zipc": "22240004"}],
    3: [{"nu_addr": 31, "co_type_addr": "1", "ds_name_logr": "Rua da Serra", "co_numb_logr": "88", "ds_cmpl_logr": None, "ds_dist": "Savassi", "ds_city": "BELO HORIZONTE", "co_stte": "MG", "co_zipc": "30140000"}],
    4: [{"nu_addr": 41, "co_type_addr": "2", "ds_name_logr": "Av. Batel", "co_numb_logr": "1200", "ds_cmpl_logr": "Conj 14", "ds_dist": "Batel", "ds_city": "CURITIBA", "co_stte": "PR", "co_zipc": "80420090"}],
    5: [{"nu_addr": 51, "co_type_addr": "1", "ds_name_logr": "Rua da Graça", "co_numb_logr": "301", "ds_cmpl_logr": None, "ds_dist": "Graça", "ds_city": "SALVADOR", "co_stte": "BA", "co_zipc": "40150060"}],
    6: [{"nu_addr": 61, "co_type_addr": "2", "ds_name_logr": "Av. Ipiranga", "co_numb_logr": "6681", "ds_cmpl_logr": "Sala 703", "ds_dist": "Partenon", "ds_city": "PORTO ALEGRE", "co_stte": "RS", "co_zipc": "90619900"}],
}

# ============================================================
# Payloads da Credify — PF (IdConsulta 328)
# CODIGO posicional: [DADOSCADASTRAIS, MORADORESENDERECO, ENDERECOS,
#   TELEFONES, PARTICIPACAOSOCIETARIA, RENDAIBGE, EMAIL, OBS(BOLSAFAMILIA),
#   PFVINCULO, ESPORTISTA, PEPPARENTESCO]
# ============================================================
def _pf_base():
    return {"CONSULTA": {"IdConsulta": "328", "TipoPessoa": "F"},
            "RESPOSTA": {"CODIGO": [1] * 11}}

SIMULACOES_PF = {
    "12345678901": {**_pf_base(), "RESPOSTA": {
        "CODIGO": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        "DADOSCADASTRAIS": {"NOME": "MARIA SILVA SANTOS", "SEXO": "F", "NASCIMENTO": "15/03/1980", "NOME_MAE": "ANA SILVA"},
        "ENDERECOS": [{"LOGRADOURO": "RUA DOS PINHEIROS 100 AP 52", "BAIRRO": "PINHEIROS", "CIDADE": "SAO PAULO", "UF": "SP", "CEP": "05422000"}],
        "TELEFONES": [{"DDD": "11", "NUMERO": "988881111", "TIPO": "CELULAR"}],
        "EMAIL": [{"ENDERECO": "maria.santos@email.com"}],
        "PARTICIPACAOSOCIETARIA": [{"CNPJ": "11222333000181", "RAZAO_SOCIAL": "CLINICA CORACAO LTDA", "PERCENTUAL": "50.00", "QUALIFICACAO": "Socio-Administrador"}]}},
    "23456789012": {**_pf_base(), "RESPOSTA": {
        "CODIGO": [1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 1],
        "DADOSCADASTRAIS": {"NOME": "JOAO PEREIRA LIMA", "SEXO": "M", "NASCIMENTO": "02/08/1975", "NOME_MAE": "ROSA PEREIRA"},
        "ENDERECOS": [{"LOGRADOURO": "AV ATLANTICA 500 SALA 901", "BAIRRO": "COPACABANA", "CIDADE": "RIO DE JANEIRO", "UF": "RJ", "CEP": "22021001"}],
        "TELEFONES": [{"DDD": "21", "NUMERO": "977772222", "TIPO": "CELULAR"}],
        "EMAIL": [{"ENDERECO": "joao.lima@email.com"}],
        "PARTICIPACAOSOCIETARIA": [{"CNPJ": "11222333000181", "RAZAO_SOCIAL": "CLINICA CORACAO LTDA", "PERCENTUAL": "50.00", "QUALIFICACAO": "Socio"}]}},
    "34567890123": {**_pf_base(), "RESPOSTA": {
        "CODIGO": [1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 1],
        "DADOSCADASTRAIS": {"NOME": "ANA COSTA RIBEIRO", "SEXO": "F", "NASCIMENTO": "20/11/1988", "NOME_MAE": "CLARA COSTA"},
        "ENDERECOS": [{"LOGRADOURO": "RUA DA SERRA 88", "BAIRRO": "SAVASSI", "CIDADE": "BELO HORIZONTE", "UF": "MG", "CEP": "30140000"}],
        "TELEFONES": [{"DDD": "31", "NUMERO": "966663333", "TIPO": "CELULAR"}],
        "EMAIL": [{"ENDERECO": "ana.ribeiro@email.com"}],
        "PARTICIPACAOSOCIETARIA": [{"CNPJ": "44555666000199", "RAZAO_SOCIAL": "DERMACLINICA BH LTDA", "PERCENTUAL": "100.00", "QUALIFICACAO": "Socio-Administrador"}]}},
    "45678901234": {**_pf_base(), "RESPOSTA": {
        "CODIGO": [1, 1, 1, 1, 2, 2, 1, 1, 2, 2, 2],
        "DADOSCADASTRAIS": {"NOME": "CARLOS MENDES", "SEXO": "M", "NASCIMENTO": "10/02/1960", "NOME_MAE": "HELENA MENDES"},
        "ENDERECOS": [{"LOGRADOURO": "AV BATEL 1200 CONJ 14", "BAIRRO": "BATEL", "CIDADE": "CURITIBA", "UF": "PR", "CEP": "80420090"}],
        "TELEFONES": [{"DDD": "41", "NUMERO": "955554444", "TIPO": "FIXO"}],
        "EMAIL": [{"ENDERECO": "carlos.mendes@email.com"}],
        "PARTICIPACAOSOCIETARIA": []}},
    "56789012345": {**_pf_base(), "RESPOSTA": {
        "CODIGO": [1, 1, 1, 1, 1, 2, 1, 1, 2, 2, 2],
        "DADOSCADASTRAIS": {"NOME": "FERNANDA ALVES", "SEXO": "F", "NASCIMENTO": "05/06/1992", "NOME_MAE": "PAULA ALVES"},
        "ENDERECOS": [{"LOGRADOURO": "RUA DA GRACA 301", "BAIRRO": "GRACA", "CIDADE": "SALVADOR", "UF": "BA", "CEP": "40150060"}],
        "TELEFONES": [{"DDD": "71", "NUMERO": "944443333", "TIPO": "CELULAR"}],
        "EMAIL": [{"ENDERECO": "fernanda.alves@email.com"}],
        "PARTICIPACAOSOCIETARIA": [{"CNPJ": "77888999000177", "RAZAO_SOCIAL": "CLINICA PEDIATRICA SALVADOR LTDA", "PERCENTUAL": "33.33", "QUALIFICACAO": "Socio"}]}},
}

CPF_NAO_ENCONTRADO = {"CONSULTA": {"IdConsulta": "328", "TipoPessoa": "F"},
                      "RESPOSTA": {"CODIGO": [2] * 11, "DADOSCADASTRAIS": None,
                                   "ENDERECOS": [], "TELEFONES": [],
                                   "PARTICIPACAOSOCIETARIA": [], "EMAIL": []}}

# ============================================================
# Payloads da Credify — PJ (IdConsulta 329)
# CODIGO posicional: [DADOSCADASTRAIS, ENDERECOS, TELEFONES,
#   QUADROSOCIETARIO, CNAE, PARTICIPACAOSOCIETARIA, INFOEMPRESA,
#   FILIAIS, MATRIZ, EMAIL]
# ============================================================
SIMULACOES_PJ = {
    "11222333000181": {"CONSULTA": {"IdConsulta": "329", "TipoPessoa": "J"},
        "RESPOSTA": {"CODIGO": [1, 1, 1, 1, 1, 1, 1, 2, 2, 1],
            "DADOSCADASTRAIS": {"RAZAO_SOCIAL": "CLINICA CORACAO LTDA", "NOME_FANTASIA": "CORACAO", "PORTE": "ME", "SITUACAO": "ATIVA", "ABERTURA": "10/05/2010"},
            "ENDERECOS": [{"LOGRADOURO": "AV ATLANTICA 500 SALA 901", "BAIRRO": "COPACABANA", "CIDADE": "RIO DE JANEIRO", "UF": "RJ", "CEP": "22021001"}],
            "TELEFONES": [{"DDD": "21", "NUMERO": "999990000", "TIPO": "FIXO"}],
            "QUADROSOCIETARIO": [{"CPF_CNPJ": "12345678901", "NOME": "MARIA SILVA SANTOS", "QUALIFICACAO": "Socio-Administrador", "PERCENTUAL": "50.00"},
                                  {"CPF_CNPJ": "23456789012", "NOME": "JOAO PEREIRA LIMA", "QUALIFICACAO": "Socio", "PERCENTUAL": "50.00"}],
            "CNAE": [{"CODIGO": "8630-5/01", "DESCRICAO": "Atividade medica ambulatorial com restricao"}],
            "INFOEMPRESA": {"FATURAMENTO_PRESUMIDO": "ATE R$ 360.000,00", "CAPITAL_SOCIAL": "R$ 100.000,00"},
            "EMAIL": [{"ENDERECO": "contato@coracao.com.br"}]}},
    "44555666000199": {"CONSULTA": {"IdConsulta": "329", "TipoPessoa": "J"},
        "RESPOSTA": {"CODIGO": [1, 1, 1, 1, 1, 1, 1, 2, 2, 1],
            "DADOSCADASTRAIS": {"RAZAO_SOCIAL": "DERMACLINICA BH LTDA", "NOME_FANTASIA": "DERMACLINICA", "PORTE": "ME", "SITUACAO": "ATIVA", "ABERTURA": "02/03/2015"},
            "ENDERECOS": [{"LOGRADOURO": "RUA DA SERRA 88", "BAIRRO": "SAVASSI", "CIDADE": "BELO HORIZONTE", "UF": "MG", "CEP": "30140000"}],
            "TELEFONES": [{"DDD": "31", "NUMERO": "988880000", "TIPO": "FIXO"}],
            "QUADROSOCIETARIO": [{"CPF_CNPJ": "34567890123", "NOME": "ANA COSTA RIBEIRO", "QUALIFICACAO": "Socio-Administrador", "PERCENTUAL": "100.00"}],
            "CNAE": [{"CODIGO": "8630-5/01", "DESCRICAO": "Atividade medica ambulatorial com restricao"}],
            "INFOEMPRESA": {"FATURAMENTO_PRESUMIDO": "ATE R$ 180.000,00", "CAPITAL_SOCIAL": "R$ 50.000,00"},
            "EMAIL": [{"ENDERECO": "contato@dermaclinica.com.br"}]}},
    "77888999000177": {"CONSULTA": {"IdConsulta": "329", "TipoPessoa": "J"},
        "RESPOSTA": {"CODIGO": [1, 1, 1, 1, 1, 1, 1, 2, 2, 1],
            "DADOSCADASTRAIS": {"RAZAO_SOCIAL": "CLINICA PEDIATRICA SALVADOR LTDA", "NOME_FANTASIA": "PEDISAL", "PORTE": "MEI", "SITUACAO": "ATIVA", "ABERTURA": "20/01/2019"},
            "ENDERECOS": [{"LOGRADOURO": "RUA DA GRACA 301", "BAIRRO": "GRACA", "CIDADE": "SALVADOR", "UF": "BA", "CEP": "40150060"}],
            "TELEFONES": [{"DDD": "71", "NUMERO": "977770000", "TIPO": "FIXO"}],
            "QUADROSOCIETARIO": [{"CPF_CNPJ": "56789012345", "NOME": "FERNANDA ALVES", "QUALIFICACAO": "Socio", "PERCENTUAL": "33.33"}],
            "CNAE": [{"CODIGO": "8630-5/01", "DESCRICAO": "Atividade medica ambulatorial com restricao"}],
            "INFOEMPRESA": {"FATURAMENTO_PRESUMIDO": "ATE R$ 81.000,00", "CAPITAL_SOCIAL": "R$ 10.000,00"},
            "EMAIL": [{"ENDERECO": "contato@pedisal.com.br"}]}},
}

CNPJ_NAO_ENCONTRADO = {"CONSULTA": {"IdConsulta": "329", "TipoPessoa": "J"},
                       "RESPOSTA": {"CODIGO": [2] * 10}}

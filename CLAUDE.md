# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Visão geral

Aplicação de gestão de recursos de uma pequena empresa de construção ("Soluções Inéditas"): viaturas, equipamentos, funcionários, clientes e obras. Foco no **controlo de prazos críticos** (seguros, inspeções, certificados, fichas médicas) através de um dashboard de alertas. Backend Django + DRF (PostgreSQL); frontend React (Vite + TypeScript) em `frontend/`. Os comentários, nomes e mensagens do código estão em **português (pt-PT)** — manter essa convenção.

## Ambiente e comandos

Windows / PowerShell. O `venv` está na raiz; **invocar sempre o Python do venv diretamente** (a ativação não é necessária):

```powershell
# Backend
.\venv\Scripts\python.exe manage.py runserver         # arranca a API em :8000
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py makemigrations <app>
.\venv\Scripts\python.exe manage.py createsuperuser
.\venv\Scripts\python.exe manage.py check

# Testes (correm numa BD de teste isolada no Postgres — não tocam nos dados reais)
.\venv\Scripts\python.exe manage.py test               # toda a suite
.\venv\Scripts\python.exe manage.py test fleet         # uma app
.\venv\Scripts\python.exe manage.py test fleet.tests.ValidacaoApiTests.test_api_normaliza_matricula  # um teste

# Frontend (a partir da raiz; usar --prefix com caminho absoluto se der ENOENT)
npm run dev --prefix frontend                          # Vite dev server em :5173
npm run build --prefix frontend                        # tsc -b && vite build (é o type-check)
npm run lint --prefix frontend                         # oxlint
```

Desenvolvimento local precisa de **dois terminais** (backend em :8000, frontend em :5173).

> Versões fixadas de propósito por causa do Python 3.14: **Django 6.0** (a primeira série a suportá-lo — não baixar abaixo de 6.0) e **DRF 3.17**. Os mínimos (`>=`) no `requirements.txt` marcam correções de segurança — não os baixar. Postgres é instalado à parte (serviço `postgresql-x64-18`, BD `gestao_recursos`).

## Configuração

`config/settings.py` lê todos os valores sensíveis e de ambiente do `.env` via `python-decouple` (`config(...)`). O `.env` **não** é versionado; o `.env.example` é o modelo. Para uma variável nova: adicionar a leitura em settings, e documentá-la em `.env.example` e `.env`.

## Arquitetura

Projeto Django `config/` + apps de domínio. Convenção Django (MVT≈MVC): `models.py` = Model, `views.py` = Controller, e o "template" numa API é o JSON dos serializers.

- **`config/`** — projeto Django (settings, urls raiz). Não é uma app instalada. Os testes das configurações transversais (documentação da API, logs, limite de tentativas de login) vivem em `config/tests.py` (`manage.py test config`).
- **`config/common.py`** — peças partilhadas entre apps. **Ler este ficheiro primeiro** ao mexer em models/serializers; contém os mecanismos transversais (ver abaixo).
- **`accounts/`** — autenticação. `models.py` está vazio de propósito: usa-se o `User`/`Group` do Django. (Sem testes próprios; o fluxo JWT é testado em `fleet/tests.py`.)
- **`fleet/`** — `Viatura` (entidade central) + `SeguroViatura`, `Inspecao`, `DespesaViatura`.
- **`equipment/`** — `Equipamento` + `Certificado`.
- **`employees/`** — `Funcionario` + `DespesaFuncionario`. Valida NIF português (`validar_nif` em `config/common.py`).
- **`projects/`** — `Cliente`, `Obra`, `AlocacaoFuncionario` (M2M com `through` explícito; cada alocação tem o seu período e regras — só funcionários ativos, `data_fim` até ao fim previsto da obra) e `AutoObra` (auto mensal de faturação, único por obra/ano/mês). Não há alocação de equipamentos: os equipamentos de uma obra são **derivados** dos funcionários alocados (`Equipamento.responsavel`; `equipamentos_derivados` no `ObraSerializer`, só leitura).
- **`health_records/`** — `FichaMedica` (dados de saúde, RGPD). **Acesso restrito a staff** (`IsAdminUser`), ao contrário do resto da API. `medico` e `observacoes` são `EncryptedTextField` (`config/encryption.py`, Fernet, chave em `FIELD_ENCRYPTION_KEY`); `aptidao` fica em claro (é usada em filtros). Ver `# TODO RGPD` no model (registo de acessos pendente).
- **`alerts/`** — dashboard de prazos. **Só lê** as outras apps (importa os models mas nunca os altera). Não tem models nem migrações próprias. Junta 4 fontes: seguros, inspeções, certificados e fichas médicas.
- **`reports/`** — relatórios (`APIView`s). **Só lê** as outras apps, como `alerts`; sem models nem migrações.

### Mecanismos transversais (em `config/common.py`)

1. **`RegistoComValidade`** — model abstrato base de todos os registos que expiram (`SeguroViatura`, `Inspecao`, `Certificado`, `FichaMedica`). Centraliza o campo `data_validade` e as properties calculadas `dias_para_expirar` / `expirado`. Qualquer novo tipo de registo com prazo deve herdar daqui — é o que permite o endpoint de alertas tratar todas as fontes por igual.

2. **`RegistoComAuditoria`** — model abstrato com `criado_por`/`atualizado_por` (FK User, `SET_NULL`) **e** `criado_em`/`atualizado_em` (timestamps). Os timestamps estão centralizados aqui (não repetir nos models). Preenchido pelo `AuditoriaViewSetMixin` (na API: `perform_create`/`perform_update`) e pelo `AuditoriaAdminMixin` (no Admin: `save_model`). Os serializers expõem os campos via constante `AUDITORIA_FIELDS` (read-only).

3. **`ModelCleanSerializerMixin`** — faz o serializer DRF correr o `clean()` do model na validação, convertendo erros Django→DRF (resposta 400). **Padrão de validação do projeto:** as regras de negócio vivem UMA vez no model (`clean()` para lógica multi-campo / normalização; field `validators` para limites simples), e este mixin propaga-as para a API. Adicionar o mixin ao `ModelSerializer` de qualquer model que defina `clean()`. O Admin já chama `clean()` automaticamente. (Subtileza: o mixin relê os `attrs` da instância depois do `clean()` para que normalizações — ex.: matrícula em maiúsculas — cheguem a ser persistidas.) **Atenção:** o mixin corre *depois* da validação dos campos, onde o `UniqueValidator` do DRF verifica duplicados com o valor tal como chegou. Uma normalização num campo `unique` tem de acontecer também no `to_internal_value()` do serializer (ver `ViaturaSerializer` + `normalizar_matricula`), senão um duplicado com outra capitalização passa a verificação e dá 500 na BD.

### Relações e regras

- FKs dos filhos para o pai usam **`on_delete=PROTECT`** (não se apaga uma viatura/equipamento com histórico). Considerar isto ao apagar ou testar deletes.
- Validações atuais: `data_validade` posterior a `data_inicio` (seguro) / `data_emissao` (certificado) / `data_inspecao` (inspeção) / `data_exame` (ficha); ano da viatura entre 1950 e ano-atual+1; valor de despesa ≥ 0.01; matrícula normalizada (strip+upper); NIF português válido (funcionário, cliente); auto de obra com mês 1–12 e ano ≤ ano-atual+1.

### API

Todos os endpoints sob `/api/`, exigem autenticação (`IsAuthenticated` global), com paginação (50/página) e filtros via `django-filter` (`filterset_fields` em cada ViewSet, ex.: `?viatura=ID`). Cada app de domínio expõe `serializers.py`, `views.py` (ModelViewSet) e `urls.py` (DefaultRouter), ligados em `config/urls.py`.

- CRUD: `/api/viaturas/`, `/api/seguros/`, `/api/inspecoes/`, `/api/despesas/`, `/api/equipamentos/`, `/api/certificados/`, `/api/funcionarios/`, `/api/despesas-funcionarios/`, `/api/clientes/`, `/api/obras/`, `/api/alocacoes-funcionarios/`, `/api/autos-obras/`, `/api/fichas-medicas/` (só staff).
- Relatórios (`reports/`, `APIView`s, só leitura): `/api/reports/despesas-mensais/?tipo=funcionario|viatura&entidade=ID&ano=YYYY[&mes=N]` (ano entre 2000 e 2100), `/api/reports/faturacao-obra/?obra=ID`, `/api/reports/equipamentos-funcionario/?funcionario=ID`.
- Auth por **JWT** (`djangorestframework-simplejwt`): `POST /api/auth/token/` (username+password → `{access, refresh}`), `POST /api/auth/token/refresh/` (refresh → novo access). Enviar `Authorization: Bearer <access>`. Access curto (5 min) + refresh (1 dia), em `SIMPLE_JWT`.
- **Limite de tentativas de login** (`django-axes`, secção `AXES_*` em settings): 5 falhas seguidas bloqueiam o par utilizador + IP durante 15 min, no login JWT e no Admin. O IP real vem de `ip_do_cliente` (`config/common.py`: último valor do `X-Forwarded-For`, o que o proxy do Railway acrescenta). No DRF o `AxesMiddleware` não vê a marca de bloqueio, por isso o `LoginView` (`config/urls.py`) devolve ele próprio o 429. Desbloquear alguém: Admin → Axes → "Access attempts" → apagar a linha. `/api-auth/` (login da API navegável) só existe com `DEBUG=True`.
- **`/api/alerts/?dias=N&expirados_desde=M`** — não é um ViewSet, é uma `APIView` (paginada manualmente) que junta as 4 fontes de prazo numa lista plana ordenada (mais urgente primeiro). **Só entram prazos pendentes:** um registo com sucessor (mesmo recurso, validade posterior — nos certificados, também o mesmo `tipo`, sem distinguir maiúsculas) conta como renovado e sai; recursos inativos (viatura/equipamento/funcionário) não geram alertas. `dias` (default 60) = janela futura; `expirados_desde` (default 90) = fundo que corta o histórico antigo de expirados. Ambos entre 0 e 3650 (`JANELA_MAXIMA`); fora disso ou inválidos → 400.
- **Swagger/OpenAPI** (`drf-spectacular`): UI em `/api/docs/`, esquema em `/api/schema/`. **Só staff** (`SERVE_PERMISSIONS`); no browser, entrar primeiro no Admin. Vista `SpectacularSwaggerSplitView` (script de arranque à parte) e ficheiros do Swagger servidos pela app via `drf-spectacular-sidecar` — ambos exigidos pela CSP. Tags via `@extend_schema(tags=[...])` só em Frota, Equipamentos, Alertas e Autenticação; as views de `employees`, `projects`, `health_records` e `reports` ainda não têm tag (aparecem no grupo "api").
- **Produção**: `whitenoise` serve os estáticos do Admin; settings de segurança (HSTS, cookies seguros, SSL redirect) ativam quando `DEBUG=False`. `LOGGING` envia os erros (500) para a consola, que o Railway mostra; os 4xx não são registados. Nunca registar o corpo dos pedidos (dados de saúde).
- **CSP** (Content Security Policy nativa do Django 6.0, `POLITICA_CSP` em settings): `script-src 'self'` (nada de scripts embutidos nem de fora), estilos embutidos permitidos. Está em modo **só avisar** (`SECURE_CSP_REPORT_ONLY`): os browsers enviam as violações para `/api/csp-report/` (`relatorio_csp` em `config/urls.py`, público, sem CSRF), que as escreve nos logs como "Violação CSP". Sem avisos durante uns dias → trocar para `SECURE_CSP` (bloquear). Qualquer página nova não pode depender de `<script>` embutido nem de CDNs.
- **Deploy** (Railway, builder **Railpack** → `railpack.json`; o `nixpacks.toml` e o `Procfile` não são usados). O `migrate` corre no **arranque** de cada deploy, sobre os dados reais: **`pg_dump` antes de qualquer push com migrações** (procedimento em `DEPLOY.md`). Plano Hobby, sem backups automáticos.

### Frontend (`frontend/`)

React + TS, CSS próprio (sem framework de UI) — design system em `src/index.css` (custom properties, tokens claro/escuro, layout com sidebar). CORS no backend (`django-cors-headers`) permite o Vite (:5173) chamar a API. Pontos centrais:
- `src/api/client.ts` — instância axios única. Interceptor de **request** injeta `Authorization: Bearer <access>`; interceptor de **response** renova o access via `/auth/token/refresh/` quando um pedido leva 401 e repete-o (usa um `refreshClient` axios separado para evitar loop; retry único). baseURL: `VITE_API_URL` se definida; senão, em dev, o host do browser na porta 8000 (`http://<host>:8000/api`), e no build de produção o caminho relativo `/api` (mesmo domínio).
- `src/pages/Login.tsx` — mostra a mensagem de bloqueio quando o login responde 429 (django-axes).
- `src/auth/tokens.ts` — gere o par de tokens JWT no `localStorage`. `src/auth/AuthContext.tsx` — estado de auth (booleano).
- **Fundação reutilizável** (evita repetir CRUD por página): `src/api/useCrud.ts` (hook list/criar/editar(PATCH)/apagar paginado + `primeiraMensagemErro`), `src/api/useOpcoes.ts` (carrega lista p/ `<select>`), e componentes declarativos `components/{DataTable,CrudForm,CrudPage,ModalForm,BotaoEditar,Modal}.tsx`. As páginas de listagem reduzem-se a declarar campos+colunas.
- Rotas protegidas por `components/ProtectedRoute.tsx`; `App.tsx` tem o mapa de rotas (`/<entidade>` e `/<entidade>/:id` para detalhes); páginas em `src/pages/`.
- `src/api/types.ts` espelha os serializers do backend — manter a par quando a API mudar.

> Padrão de campo opcional no `CrudForm`: vazio vai como `""` para texto/email (no backend `CharField(blank=True)` sem `null=True`), mas como `null` para número/data/select e para campos `vazioComoNull` (texto unique+nullable, ex.: NIF, nº de série).

# Plano de melhorias

Resultado da revisão de código e da verificação de segurança de 25/09/2026. Cada
item descreve o problema, a causa, a correção proposta e como verificar. Os itens
estão agrupados em fases e a ordem importa (ver
[Ordem e dependências](#ordem-e-dependências)). O que foi verificado e já está bem
fica registado no fim, em
[Verificação de segurança](#verificação-de-segurança--o-que-já-está-bem).

**Regras para executar o plano**

- Um commit por item, sempre com um teste que falhava antes da correção.
- Antes de cada push: `manage.py test`, `npm run build --prefix frontend` e
  `npm run lint --prefix frontend`.
- Só precisam de migração o item 3.2 (tabelas do `django-axes`) e as decisões D1 e
  D4. Nesses casos:
  - fazer `pg_dump` da BD de produção antes do push (há dados reais do cliente);
  - ensaiar primeiro: restaurar esse dump numa BD local à parte (ex.:
    `gestao_ensaio`), correr lá o `migrate` e apagá-la no fim, porque tem dados
    reais. Não há ambiente de testes no Railway, por isso é a única forma de
    ensaiar uma migração com dados reais.

## Resumo

"Confirmado" = reproduzido com um teste na BD de teste durante a revisão.

- [x] **0.1** Dependências com vulnerabilidades conhecidas — *alta, pequeno* (falta só ativar o Dependabot no GitHub)
- [x] **0.2** Documentação da API aberta a qualquer pessoa (confirmado) — *média, pequeno*
- [x] **1.1** Erros 500 não aparecem nos logs do Railway — *alta, pequeno*
- [ ] **2.1** Matrícula repetida em minúsculas dá 500 (confirmado) — *média, pequeno*
- [ ] **2.2** Alertas mostram prazos já renovados e recursos inativos (confirmado) — *alta, médio*
- [ ] **2.3** Listas e selects do frontend cortam aos 50 registos — *alta, médio*
- [ ] **2.4** KPIs dos alertas misturam o total geral com contagens da página — *baixa, pequeno*
- [ ] **2.5** Parâmetros com números absurdos dão 500 (confirmado) — *média, pequeno*
- [ ] **3.1** Chave de cifragem errada pode apagar dados médicos — *alta, pequeno*
- [ ] **3.2** Login sem limite de tentativas, nos 3 pontos de entrada — *alta, médio*
- [ ] **3.3** Qualquer utilizador staff lê fichas médicas pela API — *média, pequeno*
- [ ] **3.4** Falta o header Content-Security-Policy — *média, médio*
- [ ] **3.5** Sessão do Admin dura 14 dias — *baixa, pequeno*
- [ ] **3.6** Backups da BD guardados em claro — *média, pequeno*
- [ ] **4.1** Datas calculadas em UTC em vez da hora de Lisboa — *baixa, pequeno*
- [ ] **4.2** Python 3.13 em produção vs 3.14 local; `nixpacks.toml` sem uso — *baixa, pequeno*
- [ ] **4.3** Gunicorn com 1 processo; ligações à BD sem verificação — *baixa, pequeno*
- [ ] **4.4** Rever a configuração de produção no Railway — *média, pequeno*
- [ ] **5.1–5.4** Consistência e documentação — *baixa, pequeno*
- [ ] **D1–D5** Decisões pendentes (precisam de resposta antes de mexer)

## Ordem e dependências

- **Fase 0 primeiro.** São minutos cada e não dependem de nada.
- **1.1 logo a seguir.** Com os logs a funcionar, os outros problemas passam a
  deixar rasto em produção. E o bug 2.1 serve para testar o 1.1: provoca um 500
  de propósito, antes de ser corrigido.
- **3.1 depois de 1.1.** A correção troca uma falha silenciosa por um erro, e esse
  erro tem de ficar visível nos logs.
- **2.2, 2.4 e 2.5 seguidos.** Mexem no mesmo ficheiro (`alerts/views.py`), e o
  2.4 depende do 2.2.
- **3.4 antes da passagem para cookies `HttpOnly`** (ver
  [Reforços para mais tarde](#reforços-para-mais-tarde)).
- **3.2 e 4.3.** Com o `django-axes`, as tentativas de login ficam na BD e o
  número de processos gunicorn não interfere. Só no plano B do 3.2 (throttle do
  DRF) é que o contador passa a ser por processo.

---

## Fase 0 — Correções rápidas de segurança

### 0.1 Dependências com vulnerabilidades conhecidas

**Problema.** O `pip-audit` encontrou 31 vulnerabilidades em 4 pacotes Python, e o
`npm audit` encontrou 4 de gravidade alta no frontend.

| Pacote | Instalado | Corrigido em | Afeta a app? |
|---|---|---|---|
| `djangorestframework` | 3.17.1 | 3.17.2 | **Sim.** Uma falha contorna os limites de tamanho dos pedidos, e o login (`/api/auth/token/`) é público. |
| `cryptography` | 46.0.3 | 50.0.0 | Pouco: a maioria das falhas é em certificados X.509, que a app não usa. Mas o pacote traz um OpenSSL vulnerável (corrigido a partir da 48.0.1). |
| `Django` | 6.0.6 | 6.0.8 | Pouco: cache de páginas, GeoDjango e um validador de domínios, que a app não usa. |
| `sqlparse` | 0.5.5 | 0.6.0 | Não: só o Django o usa internamente, sem input dos utilizadores. |
| `react-router` / `react-router-dom` | 7.12–7.18.1 | `npm audit fix` | Não: só afeta o modo RSC, que a app não usa. |
| `postcss`, `nanoid` | — | `npm audit fix` | Não: só correm na compilação e não chegam ao browser. |

**Causa.** O `cryptography` está fixado à versão exata no `requirements.txt`, por
isso nunca se atualiza sozinho, nem em produção. Já o `Django==6.0.*` e o
`djangorestframework==3.17.*` fazem o Railway instalar o patch mais recente em cada
build: a produção talvez já tenha esses dois corrigidos, mas o `venv` local não.

**Correção.**
- `requirements.txt`: `cryptography` na versão mais recente (≥ 50.0.0),
  `Django>=6.0.8,<6.1`, `djangorestframework>=3.17.2,<3.18`, e acrescentar
  `sqlparse>=0.6.0`. Os mínimos garantem que nenhum build instala uma versão
  vulnerável.
- Local: `.\venv\Scripts\python.exe -m pip install -r requirements.txt --upgrade`.
- Frontend: `npm audit fix --prefix frontend`, sem `--force` (as correções não
  trazem mudanças incompatíveis).
- Ativar o Dependabot no GitHub: em *Settings → Code security*, ligar
  "Dependabot alerts" e "Dependabot security updates". Não é preciso nenhum
  ficheiro no repositório: o GitHub deteta sozinho o `requirements.txt` e o
  `frontend/package-lock.json`, e abre um PR sempre que sai uma correção de
  segurança.

**Atenção.** O formato da cifragem das fichas (Fernet) não muda entre versões do
`cryptography`, por isso as fichas existentes continuam legíveis. Os testes de
`health_records` confirmam-no.

**Ficheiros.** `requirements.txt`, `frontend/package-lock.json`.

**Verificar.** `pip-audit -r requirements.txt` (instalado num ambiente à parte) e
`npm audit` sem vulnerabilidades; testes, build e lint a passar. Depois do deploy,
confirmar as versões instaladas nos logs do build do Railway.

**Feito (25/09/2026).** Instalados Django 6.0.8, DRF 3.17.2, cryptography 50.0.1 e
sqlparse 0.6.0. O `npm audit fix` atualizou 4 pacotes. `pip-audit` e `npm audit`
sem vulnerabilidades; 85 testes, build e lint a passar. Falta ativar o
Dependabot, e confirmar as versões em produção depois do deploy.

### 0.2 Documentação da API aberta a qualquer pessoa (confirmado)

**Problema.** `/api/schema/` e `/api/docs/` respondem 200 sem login. Qualquer
pessoa, ou bot, fica com o mapa completo da API: todos os endpoints e campos,
incluindo os das fichas médicas.

**Causa.** O drf-spectacular serve a documentação com `AllowAny` por defeito
(definição `SERVE_PERMISSIONS`).

**Correção.** Em `SPECTACULAR_SETTINGS`:
`"SERVE_PERMISSIONS": ["rest_framework.permissions.IsAdminUser"]`. Para ver a
documentação, entra-se primeiro no Admin; a sessão do Admin serve de login.

**Ficheiros.** `config/settings.py`, `config/tests.py` (novo: testes das
configurações transversais).

**Verificar.** Teste: anónimo → 401; utilizador normal → 403; staff → 200.

**Feito (25/09/2026).** Testes em `config/tests.py` (`DocumentacaoApiTests`). Com o
`settings.py` antigo, os testes de anónimo e de utilizador normal falham.

---

## Fase 1 — Visibilidade

### 1.1 Logs de erros em produção

**Problema.** Com `DEBUG=False`, os tracebacks dos erros 500 não aparecem em lado
nenhum.

**Causa.** O `settings.py` não define `LOGGING`. Por defeito, o Django só escreve
erros na consola com `DEBUG=True`. Em produção, envia-os por email aos `ADMINS`,
que não estão configurados, e perdem-se.

**Correção.** Definir `LOGGING` com um `StreamHandler` para a consola (o Railway
recolhe o stdout): logger `django` em `INFO`, raiz em `WARNING`. Nunca registar o
corpo dos pedidos, que pode conter dados de saúde.

**Ficheiros.** `config/settings.py`, `config/tests.py`.

**Verificar.** Localmente com `DEBUG=False`, provocar o 500 do item 2.1 e ver o
traceback no terminal. Depois do deploy, confirmar nos logs do Railway.

**Feito (25/09/2026).** Os erros 4xx (login errado, dados inválidos) ficam de fora
de propósito, para os logs não se encherem de ruído. Teste em `config/tests.py`
(`LogsTests`), que falha com o `settings.py` antigo. O 500 do item 2.1 aparece no
terminal com o `IntegrityError` completo. Falta confirmar nos logs do Railway
depois do deploy.

---

## Fase 2 — Bugs

### 2.1 Matrícula repetida em minúsculas dá 500 (confirmado)

**Problema.** Com `AA-00-BB` já registada, `POST /api/viaturas/` com `aa-00-bb`
responde 500. Devia responder 400.

**Causa.** O `UniqueValidator` do DRF corre durante a validação dos campos, com o
valor tal como chegou. O `ModelCleanSerializerMixin` só corre o `clean()` do
model depois, no `validate()`. A matrícula só passa a maiúsculas quando a
verificação de duplicados já passou, e a gravação choca com a constraint `unique`
na BD (`IntegrityError`). No Admin não acontece, porque o Django valida a
unicidade depois do `clean()`.

**Correção.**
- Extrair a normalização para uma função `normalizar_matricula()` em
  `fleet/models.py`, usada pelo `Viatura.clean()` (Admin) e pelo serializer.
- No `ViaturaSerializer`, normalizar a matrícula em `to_internal_value()` antes
  de chamar o `super()` (copiar o `data`, que pode ser um `QueryDict` imutável).
  Assim o `UniqueValidator` já vê o valor final.
- No `CLAUDE.md`, na secção do `ModelCleanSerializerMixin`, registar a regra: uma
  normalização num campo `unique` tem de acontecer no serializer, porque o
  `clean()` corre tarde demais.

**Ficheiros.** `fleet/models.py`, `fleet/serializers.py`, `fleet/tests.py`,
`CLAUDE.md`.

**Verificar.** Teste: criar `AA-00-BB`, enviar `aa-00-bb` → 400 com o erro no campo
`matricula`.

### 2.2 Alertas mostram prazos já renovados e recursos inativos (confirmado)

**Problema.** Quando se regista o seguro novo de uma viatura, o antigo continua no
dashboard como "expirado" durante 90 dias (o `expirados_desde` por defeito). O
mesmo acontece com inspeções e certificados renovados, e com viaturas abatidas,
equipamentos inativos e funcionários que saíram. O dashboard enche-se de falsos
alarmes, e os verdadeiros perdem-se no meio.

**Causa.** A `AlertasView` devolve todos os registos cuja `data_validade` cai na
janela. Não verifica se já existe um registo mais recente para o mesmo recurso,
nem se o recurso está ativo.

**Correção.** Em cada fonte, excluir os registos que já têm sucessor e os de
recursos inativos. Exemplo para os seguros:

```python
sucessor = SeguroViatura.objects.filter(
    viatura=OuterRef("viatura"), data_validade__gt=OuterRef("data_validade")
)
seguros = (
    SeguroViatura.objects.select_related("viatura")
    .filter(viatura__ativa=True, data_validade__range=(piso, teto))
    .exclude(Exists(sucessor))
)
```

O que conta como "o mesmo prazo" muda de fonte para fonte:

| Fonte        | Substituído por um registo mais recente de…                         | Filtro de ativo      |
|--------------|---------------------------------------------------------------------|----------------------|
| Seguro       | a mesma viatura                                                     | `viatura__ativa`     |
| Inspeção     | a mesma viatura                                                     | `viatura__ativa`     |
| Certificado  | o mesmo equipamento **e** o mesmo tipo (`tipo__iexact`: texto livre) | `equipamento__ativo` |
| Ficha médica | — (OneToOne: só há uma por funcionário)                             | `funcionario__ativo` |

O tipo conta nos certificados porque um equipamento pode ter vários tipos de
certificado. Renovar um não deve esconder o prazo de outro.

**Ficheiros.** `alerts/views.py`, `alerts/tests.py`, `CLAUDE.md` (descrição do
endpoint de alertas).

**Verificar.** Testes: um seguro renovado não aparece; uma viatura inativa não
aparece; um certificado de tipo diferente continua a aparecer. O cenário da
revisão (seguro expirado há 5 dias + seguro novo válido por um ano) passa a
devolver uma lista vazia.

Ver também as decisões D3 e D5.

### 2.3 Listas e selects do frontend cortam aos 50 registos

**Problema.** A API devolve 50 registos por página, mas o frontend só pede a
primeira página e não tem controlos de paginação. A partir do 51.º registo:
- as listas (viaturas, funcionários, despesas de uma viatura, …) deixam de mostrar
  o resto, sem aviso. As despesas vêm das mais recentes para as mais antigas, por
  isso as antigas desaparecem primeiro;
- os `<select>` (responsável, cliente, funcionário a alocar, relatórios) ficam sem
  as opções a mais, e não há forma de as escolher.

**Causa.** O `useCrud` e o `useOpcoes` só usam o `results` do primeiro pedido.

**Correção.**
- **Backend:** criar uma classe de paginação do projeto em `config/common.py`
  (`PageNumberPagination` com `page_size = 50`, `page_size_query_param =
  "page_size"`, `max_page_size = 1000`) e ligá-la em `DEFAULT_PAGINATION_CLASS`.
  A `AlertasView` passa a usar a mesma classe. O `max_page_size` é o que impede
  alguém de pedir a BD inteira de uma vez.
- **`useOpcoes`:** pedir `page_size=1000` através dos `params` do axios, porque
  alguns caminhos já trazem `?ativo=true`.
- **`useCrud`:** guardar a página atual (`pagina`, `setPagina`, `temProxima`,
  `total`). Voltar à página 1 quando a `query` muda, e recuar uma página quando se
  apaga o último item da página atual.
- **Novo componente `Paginacao.tsx`:** reaproveita o CSS `.paginacao` que já
  existe. Usá-lo no `CrudPage`, nas páginas de detalhe e no `Alertas.tsx`, que hoje
  tem a paginação escrita à mão.

**Ficheiros.** `config/common.py`, `config/settings.py`, `alerts/views.py`,
`frontend/src/api/useCrud.ts`, `frontend/src/api/useOpcoes.ts`,
`frontend/src/components/CrudPage.tsx`, `frontend/src/components/Paginacao.tsx`
(novo), páginas de detalhe, `frontend/src/pages/Alertas.tsx`.

**Verificar.** Teste backend: `?page_size=1000` devolve mais de 50 registos, e um
`page_size` acima do máximo é limitado a 1000. No browser, com mais de 50
registos na BD local: a lista mostra "Seguinte" e o select mostra todas as opções.

### 2.4 KPIs dos alertas misturam o total geral com contagens da página

**Problema.** No dashboard, o KPI "Total" conta os alertas de todas as páginas,
mas "Críticos" e "A vigiar" contam só a página visível.

**Correção.** O backend passa a calcular a severidade, com os limites de 7 e 30
dias como constantes em `alerts/views.py`. Devolve-a em cada alerta
(`severidade`) e junta à resposta um `resumo` com `criticos` e `avisos` calculados
sobre a lista completa. O frontend deixa de calcular a severidade e usa estes
campos, e os limites passam a estar definidos num só sítio. A pesquisa e a
ordenação continuam a atuar só na página visível; depois do 2.2, os alertas devem
caber numa página.

**Ficheiros.** `alerts/views.py`, `alerts/serializers.py`, `alerts/tests.py`,
`frontend/src/api/types.ts`, `frontend/src/pages/Alertas.tsx`.

**Verificar.** Teste com mais de 50 alertas: `resumo.criticos` conta-os todos, não
só os da página.

### 2.5 Parâmetros com números absurdos dão 500 (confirmado)

**Problema.** Três pedidos com números absurdos respondem 500 em vez de 400:
- `/api/alerts/?dias=99999999`
- `/api/alerts/?expirados_desde=99999999`
- `/api/reports/despesas-mensais/?tipo=viatura&entidade=1&ano=99999`

**Causa.** Estes parâmetros só são validados como inteiros, sem valor máximo. Em
`hoje + timedelta(days=99999999)`, a data passa do ano 9999 e o Python levanta
`OverflowError`. Com `ano=99999`, o Django tenta construir uma data inválida
(`ValueError`).

**Correção.**
- Alertas: acrescentar um `maximo` ao `_parse_inteiro_nao_negativo` e limitar
  `dias` e `expirados_desde` a 3650 (10 anos).
- Relatórios: aceitar `ano` só entre 2000 e 2100 (2000 é o mesmo mínimo dos autos
  de obra).
- Fora dos limites → 400, com a mensagem no campo.

**Ficheiros.** `alerts/views.py`, `reports/views.py`, `alerts/tests.py`,
`reports/tests.py`.

**Verificar.** Testes: os três pedidos acima respondem 400.

---

## Fase 3 — Segurança e proteção de dados

### 3.1 Chave de cifragem errada pode apagar dados médicos

**Problema.** Se a `FIELD_ENCRYPTION_KEY` estiver errada (troca de chave, erro ao
copiá-la para o Railway), o `from_db_value` devolve o texto `"[dados cifrados
ilegíveis]"` em vez do valor real. Se alguém gravar essa ficha a seguir, por
exemplo só para mudar a aptidão, o Django grava todos os campos: esse texto é
cifrado com a chave errada e fica por cima do original. O dado médico perde-se
para sempre.

**Correção.**
- Em `from_db_value`, levantar um erro em vez de devolver o texto de substituição.
  Uma chave errada passa a dar um erro 500 visível nos logs (por isso vem depois do
  1.1), em vez de corromper dados.
- Na `AlertasView`, carregar as fichas com `.defer("medico", "observacoes")`. Os
  alertas não usam esses campos, por isso deixam de os decifrar: toca-se em menos
  dados de saúde, e o dashboard não falha se a chave estiver errada.
- *Opcional:* aceitar várias chaves separadas por vírgula, com `MultiFernet` (a
  primeira cifra, todas decifram). Permite trocar de chave sem perder dados.
  Documentar no `.env.example`.

**Ficheiros.** `config/encryption.py`, `alerts/views.py`,
`health_records/tests.py` (e `.env.example`, se se fizer o opcional).

**Verificar.** Teste: criar uma ficha com uma chave, trocar a chave com
`mock.patch.dict(os.environ, ...)` e ler → erro. Confirmar que o valor na BD não
mudou e que os alertas continuam a responder com a chave errada.

### 3.2 Login sem limite de tentativas, nos 3 pontos de entrada

**Problema.** Há três sítios onde se pode tentar adivinhar passwords sem limite:
- `/api/auth/token/` — o login da app;
- `/admin/login/` — o login do Admin, que vê tudo, incluindo as fichas médicas;
- `/api-auth/login/` — o login da API navegável.

Como a app é pública, qualquer pessoa pode tentar à vontade.

**Correção.** Usar o `django-axes`, que bloqueia depois de N tentativas falhadas.
Cobre os três pontos de uma vez, porque atua na função de autenticação do Django,
que todos usam (o simplejwt incluído).
- Confirmar primeiro que a versão atual do axes suporta o Django 6.0.
- Instalação: app `axes` nas `INSTALLED_APPS`, `AxesStandaloneBackend` em
  primeiro lugar nos `AUTHENTICATION_BACKENDS`, e `AxesMiddleware` no fim do
  `MIDDLEWARE`.
- Bloquear pela combinação utilizador + IP
  (`AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]`). Bloquear só pelo
  IP trancava o escritório inteiro, que sai para a internet pelo mesmo IP.
- Limites sugeridos: 5 tentativas falhadas → bloqueio de 15 minutos
  (`AXES_FAILURE_LIMIT`, `AXES_COOLOFF_TIME`).
- Indicar ao axes que a app está atrás do proxy do Railway. Sem isso, vê sempre o
  IP do proxy (ver as definições de IP do cliente na documentação do axes).
- Tirar o `/api-auth/` das rotas em produção: só serve a API navegável, e fica
  menos uma porta aberta.
- `Login.tsx`: mostrar uma mensagem própria quando a conta está bloqueada, em vez
  do erro genérico.

**Migração.** O axes cria tabelas próprias. A migração só acrescenta, mas segue as
regras do topo (`pg_dump` e ensaio antes do push).

**Testes.** As tentativas ficam gravadas na BD de teste e são desfeitas no fim de
cada teste, por isso não passam de um teste para o outro. Nenhum teste atual usa
`client.login()`, que o axes recusa por não receber o `request`.

**Plano B**, se o axes não suportar o Django 6.0: throttle do DRF no `LoginView`
(`throttle_classes = [ScopedRateThrottle]`, `throttle_scope = "login"`,
`DEFAULT_THROTTLE_RATES = {"login": "10/min"}` e `NUM_PROXIES = 1`, para o DRF
ver o IP real atrás do proxy). Limitações deste plano B:
- o `/admin/login/` fica sem limite até haver alternativa;
- o contador fica na cache em memória de cada processo gunicorn, por isso com 3
  processos (item 4.3) o limite efetivo triplica;
- o contador persiste entre testes, por isso os testes que fazem login precisam de
  `cache.clear()` no `setUp`.

**Ficheiros.** `requirements.txt`, `config/settings.py`, `config/urls.py`,
`frontend/src/pages/Login.tsx`, `fleet/tests.py`.

**Verificar.** Testes: depois de 5 falhas seguidas, a 6.ª tentativa é recusada
mesmo com a password certa, e outro utilizador continua a conseguir entrar. Repetir
o mesmo teste à mão no `/admin/login/`.

### 3.3 Qualquer utilizador staff lê fichas médicas pela API

**Problema.** A API das fichas médicas usa `IsAdminUser`, que só exige
`is_staff`. O Admin, pelo contrário, exige a permissão do model. Quem receber
`is_staff` só para gerir viaturas no Admin consegue ler dados de saúde pela API.

**Correção.** Criar em `config/common.py` uma classe
`PermissoesDoModelo(DjangoModelPermissions)` que exige também a permissão `view_`
nos GET, coisa que o `DjangoModelPermissions` do DRF não faz por defeito. Usá-la
no `FichaMedicaViewSet` em vez de `IsAdminUser`.
- Os superutilizadores não são afetados, porque têm todas as permissões.
- Aos outros utilizadores, dá-se a permissão no Admin, de preferência através de um
  grupo (ex.: "Saúde ocupacional").
- Esta classe é também o primeiro passo para as permissões por perfil previstas
  no `settings.py`.

**Ficheiros.** `config/common.py`, `health_records/views.py`,
`health_records/tests.py`.

**Verificar.** Testes: staff sem permissão → 403; com `view_fichamedica` → GET 200 e
POST 403; superutilizador → tudo permitido. O `FichaMedicaSeccao.tsx` já se esconde
quando recebe 403, por isso não precisa de mudar.

### 3.4 Falta o header Content-Security-Policy

**Problema.** A app já envia HSTS, `X-Content-Type-Options`,
`X-Frame-Options: DENY`, `Referrer-Policy` e `Cross-Origin-Opener-Policy`
(confirmado), mas não envia a `Content-Security-Policy`. É o header que mais
protege contra XSS: diz ao browser de onde pode carregar scripts. Sem ele, um
script injetado corre sem entraves, e como os tokens JWT estão no `localStorage`,
levava-os.

**Correção.**
- Ligar o `django.middleware.csp.ContentSecurityPolicyMiddleware`, que o Django
  6.0 já traz.
- Começar com `SECURE_CSP_REPORT_ONLY`: nesse modo, o browser só avisa na consola,
  sem bloquear nada. Política inicial, com as constantes de
  `django.utils.csp.CSP`: `default-src 'self'`, `script-src 'self'`,
  `style-src 'self'`, `img-src 'self' data:`, `connect-src 'self'`,
  `object-src 'none'`, `base-uri 'self'`, `frame-ancestors 'none'`.
- O Swagger UI (`/api/docs/`) carrega ficheiros de um CDN. Instalar o
  `drf-spectacular-sidecar`, que os serve a partir da própria app, em vez de abrir
  a política a esse CDN.
- Percorrer a app, o Admin e o `/api/docs/` com a consola do browser aberta.
  Quando não houver avisos, trocar `SECURE_CSP_REPORT_ONLY` por `SECURE_CSP`
  (modo que bloqueia).

**Ficheiros.** `config/settings.py`, `requirements.txt` (sidecar).

**Verificar.** Teste: as respostas trazem o header
`Content-Security-Policy-Report-Only` (e, depois da troca,
`Content-Security-Policy`). No browser: nenhum aviso de CSP na consola.

### 3.5 Sessão do Admin dura 14 dias

**Problema.** O cookie de sessão do Admin vale 14 dias, o valor por defeito do
Django. O Admin vê tudo, incluindo as fichas médicas. Quem roubar o cookie, ou
usar um computador onde a sessão ficou aberta, entra sem password durante esse
tempo todo.

**Correção.** `SESSION_COOKIE_AGE = 8 * 3600` (um dia de trabalho). O login da app
React não é afetado, porque usa tokens JWT (refresh de 1 dia).

**Ficheiros.** `config/settings.py`.

### 3.6 Backups da BD guardados em claro

**Problema.** Os ficheiros `pg_dump` de produção ficam no PC sem proteção. Têm
dados reais do cliente: NIFs, contactos e a aptidão médica dos funcionários (só
`medico` e `observacoes` vão cifrados). Quem aceda ao PC, ou a uma cópia do
ficheiro, lê tudo.

**Correção.** Não é código, é processo:
- guardar cada backup num ficheiro 7-Zip cifrado (AES-256), com a password no
  gestor de passwords;
- apagar os ficheiros de dump em claro depois de os cifrar;
- guardar a `FIELD_ENCRYPTION_KEY` de produção num sítio diferente dos backups.
  Sem ela, os campos cifrados de um backup ficam ilegíveis; guardada ao lado do
  backup, a cifragem deixa de proteger o que quer que seja.
- documentar o procedimento de backup no `DEPLOY.md`, que hoje não o descreve.

**Ficheiros.** `DEPLOY.md`.

---

## Fase 4 — Afinações de produção

### 4.1 Datas calculadas em UTC em vez da hora de Lisboa

**Problema.** `date.today()` usa o relógio do servidor, e no Railway esse relógio
está em UTC. Entre a meia-noite e a 1h de Lisboa (hora de verão), os
`dias_para_expirar` e a janela dos alertas ficam errados por um dia.

**Correção.** Trocar por `django.utils.timezone.localdate()`, que usa o
`TIME_ZONE = "Europe/Lisbon"`. Onde:
- `config/common.py` — `dias_para_expirar`;
- `alerts/views.py` — `hoje` na `AlertasView`;
- `fleet/models.py` — `_ano_maximo()`;
- `projects/models.py` — `AutoObra.clean()`;
- `reports/views.py` — ano por defeito em `DespesasMensaisView`.

Os testes podem continuar a usar `date.today()`.

### 4.2 Versão do Python e ficheiros de deploy sem uso

**Problema.** O `railpack.json` usa Python 3.13, mas localmente usa-se o 3.14, e o
`CLAUDE.md` justifica as versões do Django e do DRF com o 3.14. Além disso, o
Railway usa o Railpack e ignora o `nixpacks.toml`, mas esse ficheiro e o
`DEPLOY.md` ainda descrevem o Nixpacks como se estivesse em uso.

**Correção.**
- Pôr `"python": "3.14"` no `railpack.json`, num commit à parte, e acompanhar o
  build no Railway. Se o Railpack ainda não suportar o 3.14, reverter e registar
  no `CLAUDE.md` que a produção corre 3.13 (o Django 6.0 suporta as duas).
- Apagar o `nixpacks.toml`. O `Procfile` repete o `startCommand` do
  `railpack.json`; apagá-lo também deixa o comando de arranque num só sítio.
- Atualizar o `DEPLOY.md` para o Railpack.

**Ficheiros.** `railpack.json`, `nixpacks.toml`, `Procfile`, `DEPLOY.md`.

### 4.3 Gunicorn com 1 processo; ligações à BD sem verificação

**Problema.** Por defeito, o gunicorn arranca com 1 processo, e um pedido lento
(relatório, alertas) bloqueia todos os outros. Além disso, com `conn_max_age=600`,
uma ligação à BD que caia (por exemplo, num reinício do Postgres) só dá erro no
pedido seguinte.

**Correção.**
- No `startCommand`: `gunicorn config.wsgi --workers 3 ...`. Em alternativa,
  definir a variável `WEB_CONCURRENCY` no Railway, que o gunicorn lê sozinho.
  Vigiar a memória no plano Hobby.
- Em `settings.py`: `dj_database_url.parse(..., conn_health_checks=True)`.

**Ficheiros.** `railpack.json`, `config/settings.py`.

### 4.4 Rever a configuração de produção no Railway

- [ ] **CORS.** O `CORS_ALLOWED_ORIGINS` não constava das variáveis definidas no
  Railway, por isso a produção usa o valor por defeito, que é o de dev
  (`localhost:5173`). Aqui é inofensivo, porque o CORS não envia credenciais, mas
  é um valor de dev a correr em produção. Correção no `settings.py`: usar o default
  de `localhost` só quando `DEBUG=True`.
- [ ] **Acesso público ao Postgres.** Ver no Railway se o Postgres tem o TCP Proxy
  (acesso pela internet) ligado. Se tiver, a password da BD é a única proteção.
  Desligar se não for preciso; se o `railway connect` dos backups precisar dele,
  ligar só durante o backup.
- [ ] **Chaves.** Confirmar que a `SECRET_KEY` e a `FIELD_ENCRYPTION_KEY` de
  produção são diferentes das de dev e estão guardadas no gestor de passwords.
- [ ] **Versões.** Depois do 0.1, confirmar as versões instaladas nos logs do
  build.

**Ficheiros.** `config/settings.py` (CORS); o resto é no painel do Railway.

---

## Fase 5 — Consistência e documentação

### 5.1 Validação das datas da inspeção

A `Inspecao` não tem `clean()` e aceita uma próxima inspeção anterior à data da
própria inspeção. Acrescentar a regra `data_validade > data_inspecao`, como já
existe nos seguros, certificados e fichas. O serializer já tem o mixin, por isso a
regra passa para a API sem mais nada. Teste em `fleet/tests.py`.

### 5.2 Grupos no Swagger

As views de `employees`, `projects`, `health_records` e `reports` não têm
`@extend_schema(tags=[...])`, por isso aparecem no grupo genérico "api" do
`/api/docs/`. Acrescentar as tags Funcionários, Clientes, Obras, Fichas médicas e
Relatórios.

### 5.3 Endpoint duplicado (opcional)

`/api/reports/equipamentos-funcionario/` devolve o mesmo que
`/api/equipamentos/?responsavel=ID`, mais o nome do funcionário. Se o
`Relatorios.tsx` passar a usar o filtro, a view e os respetivos testes podem ser
removidos.

### 5.4 Documentação desatualizada

- **`readme.md`:**
  - a secção "Planeado" ainda lista a cifragem das fichas, que já está feita;
  - "Obra aloca … Equipamentos" já não é verdade: os equipamentos derivam dos
    funcionários;
  - a estrutura do projeto não lista `employees`, `projects`, `health_records` e
    `reports`.
- **`CLAUDE.md`:**
  - ainda descreve `AlocacaoEquipamento` e `/api/alocacoes-equipamentos/`, que foram
    removidos;
  - faltam `/api/autos-obras/` e os endpoints `/api/reports/…`;
  - depois deste plano, acrescentar a regra do 2.1, o novo comportamento dos
    alertas (2.2 e 2.4) e as novas regras de segurança (documentação só para staff,
    `django-axes`, CSP).
- **`DEPLOY.md`:** ver 3.6 e 4.2.

---

## Decisões pendentes

Estas dependem de como a empresa trabalha. Responder antes de mexer.

### D1 — Voltar a alocar o mesmo funcionário à mesma obra

Hoje, `unique_together = ("obra", "funcionario")` impede alocar o mesmo
funcionário duas vezes à mesma obra, mesmo em períodos diferentes (sai em março,
volta em junho). Se isto acontece na empresa, a constraint é substituída por uma
validação no `clean()` que só recusa períodos sobrepostos. **Precisa de migração**
(remove a constraint): seguir as regras do topo.

### D2 — Equipamentos de uma obra

Os `equipamentos_derivados` juntam os equipamentos de todos os funcionários que
alguma vez estiveram alocados à obra, incluindo os que já saíram (`data_fim` no
passado). Devem mostrar só os das alocações em curso (`data_fim` vazia ou igual ou
posterior a hoje)? Não precisa de migração.

### D3 — Alertas de recursos inativos

O item 2.2 propõe esconder os alertas de viaturas, equipamentos e funcionários
inativos. Se for útil continuar a vê-los (por exemplo, para cancelar o seguro de
uma viatura vendida), mantém-se o filtro de "renovado" e retira-se o de "ativo".

### D4 — Cifrar a aptidão médica

A `aptidao` ("apto", "apto com restrições", "não apto") está em claro na BD, e é o
dado de saúde mais revelador da ficha. Não foi cifrada porque é usada em filtros:
`?aptidao=` na API e o filtro lateral do Admin. Cifrá-la faz perder esses filtros.
**Precisa de migração**, porque o tipo da coluna muda. Os valores antigos continuam
legíveis, porque o `EncryptedTextField` aceita texto em claro, e ficam cifrados
quando cada ficha voltar a ser gravada.

### D5 — Fichas médicas no dashboard de alertas

Hoje, qualquer utilizador autenticado vê no dashboard "Ficha médica de X" e a data
de validade. Não revela dados clínicos, mas revela quando o exame de cada pessoa
expira. Proposta: depois do 3.3, mostrar os alertas de fichas só a quem tiver a
permissão `view_fichamedica`. Não precisa de migração.

---

## Reforços para mais tarde

Não são urgentes, mas ficam registados para não se perderem.

- **Sessão por cookie `HttpOnly` em vez de tokens no `localStorage`.** Hoje,
  qualquer JavaScript da página consegue ler os tokens. Se entrar um script
  malicioso (XSS), leva-os: o access vale 5 minutos, mas o refresh vale 1 dia. Um
  cookie `HttpOnly` não pode ser lido por JavaScript. Como em produção o React e a
  API estão no mesmo domínio, a mudança é viável. Custo: tratar o CSRF, mudar
  `client.ts`, `tokens.ts` e `AuthContext.tsx`, e pôr o Vite a encaminhar os
  pedidos da API em dev. Fazer depois do 3.4, que já trava a maioria dos XSS.
- **Permissões por perfil (roles)**, com filtragem por registo no `get_queryset`
  de cada ViewSet. É o equivalente, nesta arquitetura, ao RLS de uma base de
  dados: o browser nunca fala com a BD, por isso toda a autorização vive no Django.
  Hoje qualquer utilizador autenticado vê e altera tudo. O 3.3 é o primeiro passo.
- **Argon2 para as passwords** (`argon2-cffi`), mais resistente do que o PBKDF2
  atual. Os hashes antigos convertem-se sozinhos no login seguinte.
- **Header `Permissions-Policy`**, a desligar câmara, microfone, geolocalização,
  etc. O Django não o traz de origem; é um middleware de poucas linhas.
- Auditoria (`criado_por` / `atualizado_por`) nos inlines do Admin.
- Registo de acessos às fichas médicas (`# TODO RGPD` no model).

---

## Verificação de segurança — o que já está bem

Verificado a 25/09/2026, com a app em modo produção (`DEBUG=False`) numa BD de
teste.

| Tema | Estado | Como foi verificado |
|---|---|---|
| Chaves privadas | O `.env` nunca entrou no git; o frontend não tem segredos; a app não arranca sem `SECRET_KEY` e `FIELD_ENCRYPTION_KEY` | Histórico completo do git e pesquisa de padrões de segredos |
| Separação dev/produção | Feita por variáveis de ambiente; o `check --deploy` não dá avisos de segurança | `manage.py check --deploy` com `DEBUG=False` (com a `SECRET_KEY` local) |
| HTTPS | Redirecionamento para HTTPS, HSTS de 1 ano, cookies só por HTTPS, TLS até à BD | Headers da resposta e settings |
| Mass assignment | Campos listados à mão em todos os serializers (nenhum `__all__`); nenhum endpoint de utilizadores | `POST` com `id`, `criado_por` e `criado_em` forjados: os três foram ignorados |
| Cookies | `Secure`, `HttpOnly`, `SameSite=Lax` | Settings e valores por defeito do Django |
| Passwords | Hash PBKDF2-SHA256 com 1,2 milhões de iterações; 4 validadores de força | Settings e valores por defeito do Django |
| Queries SQL | Só ORM; o único SQL escrito à mão está num teste; nos relatórios, os nomes dos campos vêm de uma lista fixa | Pesquisa por `raw`, `extra`, `cursor` e `RawSQL` |
| Tamanho dos pedidos e respostas | Páginas de 50; `page_size` não é aceite; campos de texto com tamanho máximo; pedidos até 2,5 MB (mas ver 0.1) | Configuração da paginação; descrição com 5000 caracteres → 400 |
| Acesso às fichas médicas | Anónimo → 401; utilizador normal → 403 | Pedidos de teste |
| Fugas de informação | Sem tracebacks em produção; erro de login genérico (não revela se o utilizador existe); build do frontend sem source maps | Settings, resposta do login e `vite.config.ts` |
| RLS | Não se aplica: o browser nunca fala com a BD e a autorização está no Django | Arquitetura (ver também "Reforços para mais tarde") |

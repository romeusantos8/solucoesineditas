# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Visão geral

Aplicação de gestão de recursos de uma pequena empresa (viaturas, equipamentos), com foco no **controlo de prazos críticos** (seguros, inspeções, certificados) através de um dashboard de alertas. Backend Django + DRF (PostgreSQL); frontend React (Vite + TypeScript) em `frontend/`. Os comentários, nomes e mensagens do código estão em **português (pt-PT)** — manter essa convenção.

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

> Versões fixadas de propósito por causa do Python 3.14: **Django 6.0** (a primeira série a suportá-lo — não baixar abaixo de 6.0) e **DRF 3.17**. Postgres é instalado à parte (serviço `postgresql-x64-18`, BD `gestao_recursos`).

## Configuração

`config/settings.py` lê todos os valores sensíveis e de ambiente do `.env` via `python-decouple` (`config(...)`). O `.env` **não** é versionado; o `.env.example` é o modelo. Para uma variável nova: adicionar a leitura em settings, e documentá-la em `.env.example` e `.env`.

## Arquitetura

Projeto Django `config/` + apps de domínio. Convenção Django (MVT≈MVC): `models.py` = Model, `views.py` = Controller, e o "template" numa API é o JSON dos serializers.

- **`config/`** — projeto Django (settings, urls raiz). Não é uma app instalada.
- **`config/common.py`** — peças partilhadas entre apps. **Ler este ficheiro primeiro** ao mexer em models/serializers; contém os dois mecanismos transversais (ver abaixo).
- **`accounts/`** — autenticação. `models.py` está vazio de propósito: usa-se o `User`/`Group` do Django.
- **`fleet/`** — `Viatura` (entidade central) + `SeguroViatura`, `Inspecao`, `DespesaViatura`.
- **`equipment/`** — `Equipamento` + `Certificado`.
- **`alerts/`** — dashboard de prazos. **Só lê** as outras apps (importa os models de fleet/equipment mas nunca os altera). Não tem models nem migrações próprias.

### Dois mecanismos transversais (em `config/common.py`)

1. **`RegistoComValidade`** — model abstrato base de todos os registos que expiram (`SeguroViatura`, `Inspecao`, `Certificado`). Centraliza o campo `data_validade` e as properties calculadas `dias_para_expirar` / `expirado`. Qualquer novo tipo de registo com prazo deve herdar daqui — é o que permite o endpoint de alertas tratar as 3 fontes por igual.

2. **`ModelCleanSerializerMixin`** — faz o serializer DRF correr o `clean()` do model na validação, convertendo erros Django→DRF (resposta 400). **Padrão de validação do projeto:** as regras de negócio vivem UMA vez no model (`clean()` para lógica multi-campo / normalização; field `validators` para limites simples), e este mixin propaga-as para a API. Adicionar o mixin ao `ModelSerializer` de qualquer model que defina `clean()`. O Admin já chama `clean()` automaticamente. (Subtileza: o mixin relê os `attrs` da instância depois do `clean()` para que normalizações — ex.: matrícula em maiúsculas — cheguem a ser persistidas.)

### Relações e regras

- FKs dos filhos para o pai usam **`on_delete=PROTECT`** (não se apaga uma viatura/equipamento com histórico). Considerar isto ao apagar ou testar deletes.
- Validações atuais: `data_validade` posterior a `data_inicio`/`data_emissao`; ano da viatura entre 1950 e ano-atual+1; valor de despesa ≥ 0.01; matrícula normalizada (strip+upper).

### API

Todos os endpoints sob `/api/`, exigem autenticação (`IsAuthenticated` global), com paginação (50/página) e filtros via `django-filter` (`filterset_fields` em cada ViewSet, ex.: `?viatura=ID`). Cada app de domínio expõe `serializers.py`, `views.py` (ModelViewSet) e `urls.py` (DefaultRouter), ligados em `config/urls.py`.

- CRUD: `/api/viaturas/`, `/api/seguros/`, `/api/inspecoes/`, `/api/despesas/`, `/api/equipamentos/`, `/api/certificados/`.
- Auth por **Token**: `POST /api/auth/token/` (username+password → token), depois `Authorization: Token <token>`.
- **`/api/alerts/?dias=N`** — não é um ViewSet, é uma `APIView` que junta as 3 fontes de prazo numa lista plana ordenada (mais urgente primeiro, inclui já expirados). Default 60 dias; `dias` inválido/negativo → 400.

### Frontend (`frontend/`)

React + TS, CSS simples (sem framework de UI). CORS no backend (`django-cors-headers`) permite o Vite (:5173) chamar a API. Pontos centrais:
- `src/api/client.ts` — instância axios única; um interceptor injeta o token (do `localStorage`) em todos os pedidos. baseURL vem de `VITE_API_URL` (default `http://127.0.0.1:8000/api`).
- `src/auth/AuthContext.tsx` — estado de auth global; token persistido no `localStorage`.
- Rotas protegidas por `components/ProtectedRoute.tsx`; `App.tsx` tem o mapa de rotas; páginas em `src/pages/`.
- `src/api/types.ts` espelha os serializers do backend — manter a par quando a API mudar.

# Deploy no Railway

Guia para pôr a aplicação online no Railway (site acessível por HTTPS, um só
serviço: o Django serve a API **e** o frontend React já compilado).

> **Antes de começar:** o Railway faz deploy a partir do teu repositório GitHub.
> Confirma que fizeste **commit + push** de tudo para a `main`. A configuração do
> build e do arranque está no `railpack.json`. O `.env` **não** vai (tem segredos —
> está no `.gitignore`); os segredos definem-se no painel do Railway (passo 3).

---

## Passo 1 — Criar o projeto e ligar o GitHub

1. Entra em https://railway.app e faz login.
2. **New Project** → **Deploy from GitHub repo** → escolhe este repositório.
3. O Railway usa o builder **Railpack**, que lê o `railpack.json` (o
   `nixpacks.toml` e o `Procfile` são ignorados). O primeiro build vai **falhar**
   por ainda não haver base de dados nem variáveis — é esperado, continua.

## Passo 2 — Adicionar a base de dados PostgreSQL

1. No projeto, **New** → **Database** → **Add PostgreSQL**.
2. A `DATABASE_URL` **não** passa sozinha para o serviço da app: no passo 3,
   cria-a como referência à da BD.

## Passo 3 — Definir as variáveis de ambiente

No serviço da **app** (não da BD), abre **Variables** e adiciona:

| Variável | Valor |
|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (referência à variável do serviço da BD) |
| `SECRET_KEY` | (a chave gerada — ver secção "Chaves" abaixo) |
| `FIELD_ENCRYPTION_KEY` | (a chave guardada no gestor de passwords — ver "Chaves"; **nunca gerar outra**) |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `127.0.0.1,localhost` |
| `CSRF_TRUSTED_ORIGINS` | (deixa vazio — o domínio Railway é adicionado sozinho) |

> Não precisas de definir `RAILWAY_PUBLIC_DOMAIN` — o Railway injeta-a
> automaticamente, e o `settings.py` junta esse domínio ao `ALLOWED_HOSTS` e ao
> CSRF por si.

## Passo 4 — Gerar o domínio público

1. No serviço da app → **Settings** → **Networking** → **Generate Domain**.
2. Ficas com algo como `nome-da-app.up.railway.app`. É este o endereço do site.

## Passo 5 — Redeploy e primeiro arranque

1. Depois de definires as variáveis, faz **Deploy** (ou espera pelo redeploy
   automático). O **build** instala as dependências, compila o React e corre o
   `collectstatic`. No **arranque**, antes do gunicorn, corre o `migrate`: as
   migrações são aplicadas sozinhas em cada deploy.
2. Quando ficar verde, abre o domínio do passo 4 no browser. Deves ver o login.

## Passo 6 — Criar o utilizador administrador

A base de dados de produção começa vazia — não há utilizadores. Cria o superuser:

1. No serviço da app → separador **Deployments** (ou o ícone de terminal/CLI) →
   abre uma **shell/console** no serviço.
2. Corre:
   ```
   python manage.py createsuperuser
   ```
   Escolhe username e password fortes (esta é a conta do teu pai / admin).

> Alternativa (se não houver console fácil no painel): instala a Railway CLI
> (`npm i -g @railway/cli`), `railway link` ao projeto, e depois
> `railway run python manage.py createsuperuser`.

Pronto — o site está online. O pai acede ao domínio, faz login com essa conta.

---

## Atualizar a app

Fazes commit + push para a `main`; o Railway redeploya automaticamente.

> ⚠️ **Se o push trouxer migrações, faz backup da BD ANTES do push** (ver
> "Backup da base de dados"). As migrações correm sozinhas no arranque, sobre os
> dados reais, sem pedir confirmação. Um push traz migrações quando tem ficheiros
> novos numa pasta `migrations/` ou uma app nova em `INSTALLED_APPS` (ex.: o
> `django-axes`). Na dúvida, faz backup.

Para ensaiar a migração antes, com dados reais, restaura o backup numa BD local à
parte e corre lá o `migrate` (ver "Ensaiar uma migração").

---

## Backup da base de dados

O plano Hobby do Railway **não faz backups automáticos**. O backup faz-se **no
teu PC**, que liga à BD do Railway por um túnel e grava um ficheiro local. (O
`railway run pg_dump` **não funciona**: tenta ligar ao endereço interno da BD.)

Pré-requisitos: Railway CLI com sessão iniciada (`railway login`) e ligada ao
projeto (`railway link`, na pasta do projeto); PostgreSQL instalado no PC (dá o
`pg_dump`); 7-Zip para cifrar o backup.

1. Numa janela do PowerShell, **na pasta do projeto**, abre só o túnel e **deixa
   a janela aberta**:
   ```powershell
   railway connect Postgres --tunnel-only
   ```
   O comando mostra os dados da ligação: host (`127.0.0.1`), porta, utilizador,
   password e nome da BD. (Sem `--tunnel-only`, abre a consola `psql` em vez do
   túnel.)
2. Noutra janela, vai para uma pasta **fora do projeto** (ex.: `Documentos\Backups`)
   e faz o dump com os dados do passo 1. O `pg_dump` pede a password; cola-a:
   ```powershell
   & "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -h 127.0.0.1 -p PORTA -U UTILIZADOR -d NOME_BD -F c -f "backup-AAAA-MM-DD.dump"
   ```
   Confirma que o ficheiro se lê (lista o conteúdo sem restaurar nada):
   ```powershell
   & "C:\Program Files\PostgreSQL\18\bin\pg_restore.exe" --list "backup-AAAA-MM-DD.dump" | Select-Object -First 10
   ```
   Depois fecha o túnel: `Ctrl+C` na primeira janela.
3. **Cifra o backup:** tem dados reais do cliente (NIFs, contactos, aptidão médica).
   Com o 7-Zip: botão direito no ficheiro → 7-Zip → "Adicionar ao arquivo…" →
   formato 7z, define uma password (cifragem AES-256) e marca "Cifrar nomes de
   ficheiros". Guarda a password no gestor de passwords e **apaga o `.dump` em
   claro**.
4. Guarda a `FIELD_ENCRYPTION_KEY` **num sítio diferente** do backup. Sem ela, os
   campos cifrados das fichas médicas ficam ilegíveis; guardada ao lado do backup,
   a cifragem deixa de proteger o que quer que seja.

### Ensaiar uma migração

Com o backup (decifrado temporariamente), numa BD local à parte:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\createdb.exe" -U postgres gestao_ensaio
& "C:\Program Files\PostgreSQL\18\bin\pg_restore.exe" -U postgres -d gestao_ensaio --no-owner --no-privileges "backup-AAAA-MM-DD.dump"
$env:POSTGRES_DB = "gestao_ensaio"; .\venv\Scripts\python.exe manage.py migrate; Remove-Item Env:POSTGRES_DB
& "C:\Program Files\PostgreSQL\18\bin\dropdb.exe" -U postgres gestao_ensaio   # no fim: tem dados reais
```

Na BD de ensaio, as fichas médicas aparecem como "[dados cifrados ilegíveis]",
porque a chave local é diferente da de produção. É esperado; não edites fichas aí.

### Repor um backup em produção

Só em caso de desastre, e confirmando duas vezes: é **destrutivo** (substitui os
dados atuais). Com o túnel do passo 1 aberto:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\pg_restore.exe" -h 127.0.0.1 -p PORTA -U PGUSER -d PGDATABASE --clean --if-exists --no-owner --no-privileges "backup-AAAA-MM-DD.dump"
```

---

## Chaves (gera as tuas — NÃO uses exemplos de outros sítios)

Gera cada uma UMA vez e cola no painel do Railway (passo 3). Comandos:

```powershell
# SECRET_KEY
.\venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# FIELD_ENCRYPTION_KEY (cifra as fichas médicas — RGPD)
.\venv\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

> ⚠️ **A `FIELD_ENCRYPTION_KEY` é crítica.** É a chave que cifra os dados de
> saúde. Se a perderes ou trocares, as fichas médicas já guardadas ficam
> **ilegíveis para sempre**. Guarda-a num sítio seguro (gestor de passwords),
> além do painel do Railway. NUNCA a metas no git.
>
> A de produção **já existe**: gera-se uma única vez. Ao recriar o serviço ou
> mudar de alojamento, cola a mesma a partir do gestor de passwords — nunca gerar
> uma nova.
>
> Em produção usa uma chave DIFERENTE da de desenvolvimento (a do `.env` local).

---

## Notas / resolução de problemas

- **RGPD**: o Railway tem região UE. Ao criar o projeto/BD, escolhe uma região
  europeia (ex.: `europe-west4`) — obrigatório por causa dos dados de saúde.
- **Erros da app**: os erros 500 aparecem com o traceback nos **Deploy Logs** do
  serviço (níveis `ERROR`). Os pedidos recusados (400, 401, 403) não são
  registados, exceto as falhas de login, que aparecem como avisos `AXES`.
- **Conta bloqueada no login**: 5 falhas seguidas bloqueiam o par utilizador + IP
  durante 15 minutos. Para desbloquear antes: Admin → Axes → "Access attempts" →
  apagar a linha dessa pessoa.
- **Avisos "Violação CSP" nos logs**: a Content Security Policy está em modo "só
  avisar". Cada aviso indica algo que ela bloquearia. Ao fim de uns dias sem
  avisos, troca `SECURE_CSP_REPORT_ONLY` por `SECURE_CSP` no `settings.py` para
  passar a bloquear.
- **Erro "DisallowedHost"**: falta o domínio no `ALLOWED_HOSTS`. Normalmente o
  Railway injeta `RAILWAY_PUBLIC_DOMAIN` (domínio público) e `RAILWAY_PRIVATE_DOMAIN`
  (rede interna / health check) e o settings trata dos dois automaticamente; se
  usares um domínio próprio, acrescenta-o ao `ALLOWED_HOSTS` nas Variables.
- **CSS/JS não carregam**: confirma que o build correu (`collectstatic` no log do
  deploy) e que o `WhiteNoiseMiddleware` está ativo (está).

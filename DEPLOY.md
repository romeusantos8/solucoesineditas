# Deploy no Railway

Guia para pôr a aplicação online no Railway (site acessível por HTTPS, um só
serviço: o Django serve a API **e** o frontend React já compilado).

> **Antes de começar:** o Railway faz deploy a partir do teu repositório GitHub.
> Confirma que fizeste **commit + push** de tudo para a `main` (incluindo
> `Procfile`, `nixpacks.toml`, e as alterações a `config/settings.py`,
> `config/urls.py`, `requirements.txt`). O `.env` **não** vai (tem segredos —
> está no `.gitignore`); os segredos definem-se no painel do Railway (passo 3).

---

## Passo 1 — Criar o projeto e ligar o GitHub

1. Entra em https://railway.app e faz login.
2. **New Project** → **Deploy from GitHub repo** → escolhe este repositório.
3. O Railway deteta o `nixpacks.toml` e começa a construir. (Vai **falhar** nesta
   fase por ainda não haver base de dados nem variáveis — é esperado, continua.)

## Passo 2 — Adicionar a base de dados PostgreSQL

1. No projeto, **New** → **Database** → **Add PostgreSQL**.
2. O Railway cria a BD e injeta automaticamente a variável `DATABASE_URL` no
   serviço da app. (O `settings.py` já a lê.)

## Passo 3 — Definir as variáveis de ambiente

No serviço da **app** (não da BD), abre **Variables** e adiciona:

| Variável | Valor |
|---|---|
| `SECRET_KEY` | (a chave gerada — ver secção "Chaves" abaixo) |
| `FIELD_ENCRYPTION_KEY` | (a chave gerada — ver "Chaves"; **guarda-a bem!**) |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `127.0.0.1,localhost` |
| `CSRF_TRUSTED_ORIGINS` | (deixa vazio — o domínio Railway é adicionado sozinho) |

> Não precisas de definir `DATABASE_URL` nem `RAILWAY_PUBLIC_DOMAIN` — o Railway
> injeta-as automaticamente. O `settings.py` junta o domínio do Railway ao
> `ALLOWED_HOSTS` e ao CSRF por si.

## Passo 4 — Gerar o domínio público

1. No serviço da app → **Settings** → **Networking** → **Generate Domain**.
2. Ficas com algo como `nome-da-app.up.railway.app`. É este o endereço do site.

## Passo 5 — Redeploy e primeiro arranque

1. Depois de definires as variáveis, faz **Deploy** (ou espera pelo redeploy
   automático). O build corre: instala deps, compila o React, `collectstatic`,
   `migrate`.
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
> Em produção usa uma chave DIFERENTE da de desenvolvimento (a do `.env` local).

---

## Notas / resolução de problemas

- **RGPD**: o Railway tem região UE. Ao criar o projeto/BD, escolhe uma região
  europeia (ex.: `europe-west4`) — obrigatório por causa dos dados de saúde.
- **Erro "DisallowedHost"**: falta o domínio no `ALLOWED_HOSTS`. Normalmente o
  Railway injeta `RAILWAY_PUBLIC_DOMAIN` (domínio público) e `RAILWAY_PRIVATE_DOMAIN`
  (rede interna / health check) e o settings trata dos dois automaticamente; se
  usares um domínio próprio, acrescenta-o ao `ALLOWED_HOSTS` nas Variables.
- **CSS/JS não carregam**: confirma que o build correu (`collectstatic` no log do
  deploy) e que o `WhiteNoiseMiddleware` está ativo (está).
- **Atualizar a app**: fazes commit + push para a `main`; o Railway redeploya
  automaticamente.

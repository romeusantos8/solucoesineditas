# Gestão de Recursos

Aplicação web para gestão dos recursos de uma pequena empresa: viaturas, equipamentos,
funcionários, obras, clientes e respetivas despesas, seguros e certificados.

O foco da aplicação é o **controlo de prazos críticos** — validade de seguros de
viaturas, inspeções, certificados de equipamentos e fichas médicas — através de um
dashboard de alertas que avisa antes de cada prazo expirar.

## Estado do projeto

Em produção no Railway (região UE). Os módulos planeados estão implementados; as
melhorias em curso estão em [PLANO_MELHORIAS.md](PLANO_MELHORIAS.md).

## Funcionalidades

### Implementado
- Gestão de viaturas com seguros, inspeções, despesas e funcionário responsável
- Gestão de equipamentos com certificados e funcionário responsável
- Gestão de funcionários e respetivas despesas
- Gestão de clientes e obras: alocação de funcionários (cada um com o seu período)
  e autos mensais de faturação. Os equipamentos de uma obra são os dos
  funcionários alocados
- Fichas médicas dos funcionários (dados de saúde — ver [Privacidade e RGPD](#privacidade-e-rgpd))
- Dashboard de alertas: prazos a expirar e expirados recentes (por defeito, próximos
  60 dias e últimos 90) de seguros, inspeções, certificados e fichas médicas. Só
  mostra o que ainda precisa de atenção: prazos já renovados e recursos inativos
  ficam de fora
- Relatórios: despesas mensais por funcionário ou viatura, faturação por obra e
  equipamentos por funcionário
- Autenticação por JWT (access + refresh), com bloqueio temporário após várias
  tentativas de login falhadas
- Frontend React completo

### Planeado
- Sistema de permissões por perfil (role) — o "gancho" já está no settings
- Registo de acessos às fichas médicas (quem consultou o quê e quando)
- Correções da revisão de código e da verificação de segurança de setembro de
  2026 — ver [PLANO_MELHORIAS.md](PLANO_MELHORIAS.md)

## Stack tecnológica

| Camada          | Tecnologia                        |
|-----------------|-----------------------------------|
| Backend         | Django + Django REST Framework    |
| Base de dados   | PostgreSQL                        |
| Frontend        | React (Vite + TypeScript)         |
| Alojamento      | Railway (região UE)               |

## Modelo de dados

As entidades centrais e as suas relações:

- **Cliente** tem várias **Obras**
- **Obra** aloca vários **Funcionários** (cada alocação com o seu período) e tem
  **Autos** mensais de faturação
- **Funcionário** tem uma **Ficha Médica**, **Despesas** e alocações a obras
- **Viatura** tem **Seguros**, **Inspeções**, **Despesas** e um **Funcionário** responsável
- **Equipamento** tem **Certificados** e um **Funcionário** responsável; os
  equipamentos de uma obra derivam dos funcionários alocados
- **Utilizador** (login) é separado da lógica de negócio

Todas as entidades com campo de validade (seguros, inspeções, certificados, fichas
médicas) alimentam o dashboard de alertas.

## Como correr localmente

> As instruções abaixo são para **Windows / PowerShell**. O desenvolvimento precisa
> de **dois terminais**: backend (Django, porta 8000) e frontend (Vite, porta 5173).

### Estrutura do projeto
```
config/          Projeto Django (settings, urls, peças partilhadas, testes transversais)
accounts/        Autenticação / utilizadores (separado da lógica de negócio)
fleet/           Viaturas, seguros, inspeções, despesas
equipment/       Equipamentos e certificados
employees/       Funcionários e despesas
projects/        Clientes, obras, alocações e autos
health_records/  Fichas médicas (acesso restrito, campos cifrados)
alerts/          Dashboard de prazos a expirar (só lê as outras apps)
reports/         Relatórios (só lê as outras apps)
frontend/        Aplicação React (Vite + TypeScript)
```
> Nota (Django MVT ≈ MVC): `models.py` = **Model**, `views.py` = **Controller** (a
> lógica), e os Templates seriam a **View** — numa API, o "template" é o JSON dos
> serializers. Os nomes são convenção obrigatória do Django.

### 0. Pré-requisito: PostgreSQL instalado
Instala o PostgreSQL e **anota a password do utilizador `postgres`** e a **porta**
(por defeito `5432`). Cria a base de dados uma vez (no pgAdmin, ou no terminal se o
`psql` estiver no PATH):
```powershell
createdb -U postgres gestao_recursos   # vai pedir a password do postgres
```

### 1. Ambiente virtual (venv)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
> Se o PowerShell bloquear a ativação, corre uma vez:
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

### 2. Dependências
```powershell
pip install -r requirements.txt
npm install --prefix frontend
```

### 3. Variáveis de ambiente
Copia o modelo e preenche-o: `Copy-Item .env.example .env`. No `.env`, ajusta
`POSTGRES_PASSWORD` para a password da tua instalação do Postgres e gera uma
`SECRET_KEY` e uma `FIELD_ENCRYPTION_KEY` (os comandos estão no próprio ficheiro).
Para desenvolvimento, mete `DEBUG=True`.
> O `.env` tem segredos e **não** vai para o git. O `.env.example` é o modelo
> partilhável, sem segredos.

### 4. Migrações e arranque
```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver              # terminal 1: backend
npm run dev --prefix frontend           # terminal 2: frontend
```
- App: http://localhost:5173/
- Admin: http://127.0.0.1:8000/admin/
- API: http://127.0.0.1:8000/api/ (documentação em `/api/docs/`, só para staff:
  entra primeiro no Admin)

### 5. Testes
```powershell
python manage.py test                   # backend (BD de teste isolada)
npm run build --prefix frontend         # frontend: type-check + build
npm run lint --prefix frontend
```

## Deploy

O deploy é feito no Railway a partir da `main` no GitHub. Guia completo, incluindo
**backups da base de dados antes de pushes com migrações**, em [DEPLOY.md](DEPLOY.md).

## Privacidade e RGPD

A aplicação trata **dados de saúde** (fichas médicas dos funcionários), que são
dados de categoria especial ao abrigo do RGPD. Medidas em vigor:

- Acesso às fichas médicas restrito a staff (na API e no Admin)
- Campos de texto livre das fichas (médico e observações) cifrados na base de dados,
  com a chave fora do código
- Minimização: o dashboard de alertas identifica só o funcionário e a data, sem
  dados clínicos
- Comunicação sempre por HTTPS (com HSTS), dados alojados na UE
- Login com bloqueio após várias tentativas falhadas; política de segurança de
  conteúdo (CSP) contra scripts injetados

## Licença

Projeto privado. Todos os direitos reservados.

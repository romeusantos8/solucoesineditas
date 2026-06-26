# Gestão de Recursos

Aplicação web para gestão dos recursos de uma pequena empresa: viaturas, equipamentos,
funcionários, obras, clientes e respetivas despesas, seguros e certificados.

O foco da aplicação é o **controlo de prazos críticos** — validade de seguros de
viaturas, inspeções, certificados de equipamentos e fichas médicas — através de um
dashboard de alertas que avisa antes de cada prazo expirar.

## Estado do projeto

Em desenvolvimento. O MVP cobre **gestão de viaturas e equipamentos com alertas de
prazos**. Os restantes módulos serão adicionados por fases.

## Funcionalidades

### MVP (em curso)
- Gestão de viaturas (CRUD) com seguros, inspeções e despesas associadas
- Gestão de equipamentos (CRUD) com certificados associados
- Dashboard de alertas: prazos a expirar nos próximos 30 e 60 dias
- Autenticação de utilizadores

### Planeado
- Gestão de funcionários e respetivas despesas
- Gestão de clientes e obras, com alocação de funcionários e equipamentos
- Fichas médicas dos funcionários (dados sensíveis — ver nota de RGPD)
- Sistema de permissões por perfil (role)

## Stack tecnológica

| Camada          | Tecnologia                        |
|-----------------|-----------------------------------|
| Backend         | Django + Django REST Framework    |
| Base de dados   | PostgreSQL                        |
| Frontend        | React (Vite)                      |
| Alojamento      | Railway / Render (região UE)      |

## Modelo de dados

As entidades centrais e as suas relações:

- **Cliente** tem várias **Obras**
- **Obra** aloca vários **Funcionários** e **Equipamentos**
- **Funcionário** tem uma **Ficha Médica**, **Despesas** e alocações a obras
- **Viatura** tem **Seguros**, **Inspeções** e **Despesas**
- **Equipamento** tem **Certificados**
- **Utilizador** (login) e **Perfil/Role** são separados da lógica de negócio

Todas as entidades com campo de validade (seguros, inspeções, certificados, fichas
médicas) alimentam o dashboard de alertas.

## Como correr localmente

> Estado: **Passo 1 (Setup)** concluído. A API e o endpoint de alertas chegam nos
> passos seguintes. As instruções abaixo são para **Windows / PowerShell**.

### Estrutura do projeto
```
config/      Projeto Django (settings, urls, wsgi/asgi)
accounts/    Autenticação / utilizadores (separado da lógica de negócio)
fleet/       Viaturas, seguros, inspeções, despesas
equipment/   Equipamentos e certificados
alerts/      Dashboard de prazos a expirar (só lê as outras apps)
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
```

### 3. Variáveis de ambiente
Já existe um `.env` pré-preenchido (a partir do `.env.example`). **Abre o `.env` e
ajusta `POSTGRES_PASSWORD`** para a password da tua instalação do Postgres.
> O `.env` tem segredos e **não** vai para o git. O `.env.example` é o modelo
> partilhável, sem segredos. Para recriá-lo: `Copy-Item .env.example .env`

### 4. Migrações e arranque
```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
- Admin: http://127.0.0.1:8000/admin/
- API: http://127.0.0.1:8000/api/  *(a partir do Passo 3)*

## Privacidade e RGPD

A aplicação irá tratar **dados de saúde** (fichas médicas dos funcionários), que são
dados de categoria especial ao abrigo do RGPD. O desenho do sistema tem isto em conta:

- Acesso restrito a esses dados, controlado por perfil
- Cifragem dos campos sensíveis em base de dados
- Minimização: guardar apenas o estritamente necessário
- Comunicação sempre por HTTPS e dados alojados na UE

## Licença

Projeto privado. Todos os direitos reservados.
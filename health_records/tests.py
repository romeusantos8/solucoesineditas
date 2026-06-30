r"""
Testes da Ficha Médica.

O ponto crítico é o ACESSO RESTRITO: um utilizador normal (não-staff) não pode
ver/criar fichas médicas; só staff/admin.

Correr: .\venv\Scripts\python.exe manage.py test health_records
"""

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from employees.models import Funcionario

from .models import FichaMedica

User = get_user_model()


class AcessoRestritoTests(APITestCase):
    def setUp(self):
        self.func = Funcionario.objects.create(
            nome="Ana", funcao="Operadora", data_admissao=date.today()
        )
        self.normal = User.objects.create_user(username="normal", password="x123456789")
        self.admin = User.objects.create_user(
            username="admin", password="x123456789", is_staff=True
        )

    def _dados(self):
        return {
            "funcionario": self.func.id,
            "aptidao": "apto",
            "data_exame": date.today().isoformat(),
            "data_validade": (date.today() + timedelta(days=365)).isoformat(),
        }

    def test_utilizador_normal_nao_acede(self):
        self.client.force_authenticate(self.normal)
        self.assertEqual(self.client.get("/api/fichas-medicas/").status_code, 403)
        self.assertEqual(
            self.client.post("/api/fichas-medicas/", self._dados()).status_code, 403
        )

    def test_anonimo_nao_acede(self):
        self.assertEqual(self.client.get("/api/fichas-medicas/").status_code, 401)

    def test_admin_cria_e_le(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post("/api/fichas-medicas/", self._dados())
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(self.client.get("/api/fichas-medicas/").json()["count"], 1)


class ValidacaoTests(APITestCase):
    def setUp(self):
        self.func = Funcionario.objects.create(
            nome="Ana", funcao="Operadora", data_admissao=date.today()
        )
        self.admin = User.objects.create_user(
            username="admin", password="x123456789", is_staff=True
        )
        self.client.force_authenticate(self.admin)

    def test_validade_antes_do_exame_rejeitada(self):
        resp = self.client.post("/api/fichas-medicas/", {
            "funcionario": self.func.id, "aptidao": "apto",
            "data_exame": date.today().isoformat(),
            "data_validade": (date.today() - timedelta(days=1)).isoformat(),
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn("data_validade", resp.json())

    def test_uma_ficha_por_funcionario(self):
        dados = {
            "funcionario": self.func.id, "aptidao": "apto",
            "data_exame": date.today().isoformat(),
            "data_validade": (date.today() + timedelta(days=365)).isoformat(),
        }
        self.assertEqual(self.client.post("/api/fichas-medicas/", dados).status_code, 201)
        # OneToOne: segunda ficha para o mesmo funcionário → erro
        self.assertEqual(self.client.post("/api/fichas-medicas/", dados).status_code, 400)


class AlertasIncluiFichaTests(APITestCase):
    def test_ficha_a_expirar_aparece_nos_alertas(self):
        func = Funcionario.objects.create(
            nome="Ana", funcao="Operadora", data_admissao=date.today()
        )
        FichaMedica.objects.create(
            funcionario=func, aptidao="apto", data_exame=date.today(),
            data_validade=date.today() + timedelta(days=20),
        )
        # alertas são acessíveis a qualquer autenticado (não precisa de staff)
        user = User.objects.create_user(username="u", password="x123456789")
        self.client.force_authenticate(user)
        dados = self.client.get("/api/alerts/").json()["results"]
        tipos = {d["tipo"] for d in dados}
        self.assertIn("ficha_medica", tipos)

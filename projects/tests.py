r"""
Testes da app de Clientes e Obras (com alocações).

Correr: .\venv\Scripts\python.exe manage.py test projects
"""

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from employees.models import Funcionario
from equipment.models import Equipamento

from .models import Cliente, Obra

User = get_user_model()
NIF_VALIDO = "123456789"


class ClienteObraApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u", password="segredo123")
        self.client.force_authenticate(self.user)

    def test_exige_autenticacao(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/clientes/").status_code, 401)

    def test_criar_cliente_e_auditoria(self):
        resp = self.client.post("/api/clientes/", {"nome": "Acme"})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["criado_por"], self.user.id)

    def test_cliente_nif_invalido_rejeitado(self):
        resp = self.client.post("/api/clientes/", {"nome": "X", "nif": "111111111"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("nif", resp.json())

    def test_obra_fim_antes_do_inicio_rejeitado(self):
        cliente = Cliente.objects.create(nome="Acme")
        resp = self.client.post("/api/obras/", {
            "cliente": cliente.id, "nome": "Obra 1",
            "data_inicio": date.today().isoformat(),
            "data_fim_prevista": (date.today() - timedelta(days=1)).isoformat(),
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn("data_fim_prevista", resp.json())

    def test_obra_mostra_alocacoes_aninhadas(self):
        cliente = Cliente.objects.create(nome="Acme")
        obra = Obra.objects.create(
            cliente=cliente, nome="Obra 1", data_inicio=date.today()
        )
        resp = self.client.get(f"/api/obras/{obra.id}/")
        body = resp.json()
        self.assertIn("alocacoes_funcionarios", body)
        self.assertIn("alocacoes_equipamentos", body)


class AlocacaoTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u", password="segredo123")
        self.client.force_authenticate(self.user)
        self.cliente = Cliente.objects.create(nome="Acme")
        self.obra = Obra.objects.create(
            cliente=self.cliente, nome="Obra 1", data_inicio=date.today()
        )
        self.func = Funcionario.objects.create(
            nome="João", funcao="Operador", data_admissao=date.today()
        )
        self.equip = Equipamento.objects.create(nome="Berbequim")

    def test_alocar_funcionario_ativo(self):
        resp = self.client.post("/api/alocacoes-funcionarios/", {
            "obra": self.obra.id, "funcionario": self.func.id,
            "data_inicio": date.today().isoformat(),
        })
        self.assertEqual(resp.status_code, 201)
        # passa a aparecer na obra
        obra = self.client.get(f"/api/obras/{self.obra.id}/").json()
        self.assertEqual(len(obra["alocacoes_funcionarios"]), 1)

    def test_nao_aloca_funcionario_inativo(self):
        self.func.ativo = False
        self.func.save()
        resp = self.client.post("/api/alocacoes-funcionarios/", {
            "obra": self.obra.id, "funcionario": self.func.id,
            "data_inicio": date.today().isoformat(),
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn("funcionario", resp.json())

    def test_nao_aloca_equipamento_inativo(self):
        self.equip.ativo = False
        self.equip.save()
        resp = self.client.post("/api/alocacoes-equipamentos/", {
            "obra": self.obra.id, "equipamento": self.equip.id,
            "data_inicio": date.today().isoformat(),
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn("equipamento", resp.json())

    def test_nao_duplica_alocacao_do_mesmo_funcionario(self):
        dados = {
            "obra": self.obra.id, "funcionario": self.func.id,
            "data_inicio": date.today().isoformat(),
        }
        self.assertEqual(
            self.client.post("/api/alocacoes-funcionarios/", dados).status_code, 201
        )
        # segunda vez na mesma obra → erro (unique_together)
        self.assertEqual(
            self.client.post("/api/alocacoes-funcionarios/", dados).status_code, 400
        )

    def test_data_fim_antes_do_inicio_rejeitada(self):
        resp = self.client.post("/api/alocacoes-funcionarios/", {
            "obra": self.obra.id, "funcionario": self.func.id,
            "data_inicio": date.today().isoformat(),
            "data_fim": (date.today() - timedelta(days=1)).isoformat(),
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn("data_fim", resp.json())

    def test_filtra_alocacoes_por_obra(self):
        self.client.post("/api/alocacoes-funcionarios/", {
            "obra": self.obra.id, "funcionario": self.func.id,
            "data_inicio": date.today().isoformat(),
        })
        resp = self.client.get(f"/api/alocacoes-funcionarios/?obra={self.obra.id}")
        self.assertEqual(resp.json()["count"], 1)

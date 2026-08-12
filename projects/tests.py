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

    def test_criar_cliente_so_com_nome_campos_texto_vazios(self):
        # Reproduz o que o frontend envia (JSON): campos de texto opcionais como
        # "" (não null) e o NIF (unique+nullable) como null.
        resp = self.client.post(
            "/api/clientes/",
            {"nome": "MotaEngil", "email": "", "telefone": "", "nif": None},
            format="json",
        )
        self.assertEqual(resp.status_code, 201)

    def test_dois_clientes_sem_nif_nao_colidem(self):
        # NIF vazio tem de ir como null: dois nulos não violam o unique.
        self.assertEqual(
            self.client.post(
                "/api/clientes/", {"nome": "A", "nif": None}, format="json"
            ).status_code,
            201,
        )
        self.assertEqual(
            self.client.post(
                "/api/clientes/", {"nome": "B", "nif": None}, format="json"
            ).status_code,
            201,
        )

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
        self.assertIn("equipamentos_derivados", body)


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

    def test_equipamentos_da_obra_derivam_dos_funcionarios(self):
        # O equipamento é do funcionário (responsavel). Ao alocar o funcionário
        # à obra, o equipamento dele aparece nos equipamentos_derivados.
        self.equip.responsavel = self.func
        self.equip.save()
        self.client.post("/api/alocacoes-funcionarios/", {
            "obra": self.obra.id, "funcionario": self.func.id,
            "data_inicio": date.today().isoformat(),
        })
        obra = self.client.get(f"/api/obras/{self.obra.id}/").json()
        derivados = obra["equipamentos_derivados"]
        self.assertEqual(len(derivados), 1)
        self.assertEqual(derivados[0]["nome"], "Berbequim")
        self.assertEqual(derivados[0]["funcionario_id"], self.func.id)

    def test_obra_sem_funcionarios_nao_tem_equipamentos(self):
        self.equip.responsavel = self.func
        self.equip.save()
        # funcionário existe e tem equipamento, mas NÃO está alocado à obra
        obra = self.client.get(f"/api/obras/{self.obra.id}/").json()
        self.assertEqual(obra["equipamentos_derivados"], [])

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

    def test_fim_alocacao_nao_ultrapassa_fim_da_obra(self):
        obra_com_fim = Obra.objects.create(
            cliente=self.cliente, nome="Com fim", data_inicio=date.today(),
            data_fim_prevista=date.today() + timedelta(days=10),
        )
        # data_fim depois do fim previsto da obra → erro
        resp = self.client.post("/api/alocacoes-funcionarios/", {
            "obra": obra_com_fim.id, "funcionario": self.func.id,
            "data_inicio": date.today().isoformat(),
            "data_fim": (date.today() + timedelta(days=20)).isoformat(),
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn("data_fim", resp.json())

    def test_fim_alocacao_dentro_do_fim_da_obra_ok(self):
        obra_com_fim = Obra.objects.create(
            cliente=self.cliente, nome="Com fim", data_inicio=date.today(),
            data_fim_prevista=date.today() + timedelta(days=10),
        )
        resp = self.client.post("/api/alocacoes-funcionarios/", {
            "obra": obra_com_fim.id, "funcionario": self.func.id,
            "data_inicio": date.today().isoformat(),
            "data_fim": (date.today() + timedelta(days=5)).isoformat(),
        })
        self.assertEqual(resp.status_code, 201)

    def test_filtra_alocacoes_por_obra(self):
        self.client.post("/api/alocacoes-funcionarios/", {
            "obra": self.obra.id, "funcionario": self.func.id,
            "data_inicio": date.today().isoformat(),
        })
        resp = self.client.get(f"/api/alocacoes-funcionarios/?obra={self.obra.id}")
        self.assertEqual(resp.json()["count"], 1)


class AutoObraApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u", password="segredo123")
        self.client.force_authenticate(self.user)
        self.cliente = Cliente.objects.create(nome="Acme")
        self.obra = Obra.objects.create(
            cliente=self.cliente, nome="Obra 1", data_inicio=date(2026, 1, 1)
        )

    def test_criar_auto(self):
        resp = self.client.post("/api/autos-obras/", {
            "obra": self.obra.id, "ano": 2026, "mes": 3, "valor": "1500.00",
        })
        self.assertEqual(resp.status_code, 201)
        # Estado default = por faturar.
        self.assertEqual(resp.json()["estado"], "por_faturar")

    def test_mes_invalido_rejeitado(self):
        resp = self.client.post("/api/autos-obras/", {
            "obra": self.obra.id, "ano": 2026, "mes": 13, "valor": "100.00",
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn("mes", resp.json())

    def test_valor_zero_rejeitado(self):
        resp = self.client.post("/api/autos-obras/", {
            "obra": self.obra.id, "ano": 2026, "mes": 1, "valor": "0.00",
        })
        self.assertEqual(resp.status_code, 400)

    def test_nao_duplica_auto_do_mesmo_mes(self):
        dados = {"obra": self.obra.id, "ano": 2026, "mes": 5, "valor": "200.00"}
        self.assertEqual(self.client.post("/api/autos-obras/", dados).status_code, 201)
        # Segundo auto para o mesmo mês/ano/obra colide (unique_together).
        self.assertEqual(self.client.post("/api/autos-obras/", dados).status_code, 400)

    def test_filtra_autos_por_obra(self):
        self.client.post("/api/autos-obras/", {
            "obra": self.obra.id, "ano": 2026, "mes": 6, "valor": "300.00",
        })
        resp = self.client.get(f"/api/autos-obras/?obra={self.obra.id}")
        self.assertEqual(resp.json()["count"], 1)

r"""
Testes do endpoint de relatórios de despesas mensais.

Correr: .\venv\Scripts\python.exe manage.py test reports
"""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from employees.models import DespesaFuncionario, Funcionario
from fleet.models import DespesaViatura, Viatura

User = get_user_model()

URL = "/api/reports/despesas-mensais/"


class DespesasMensaisTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u", password="segredo123")
        self.client.force_authenticate(self.user)
        self.func = Funcionario.objects.create(
            nome="João", funcao="Op", data_admissao=date(2026, 1, 1)
        )
        # Duas despesas em janeiro/2026, uma em março/2026, uma em 2025.
        DespesaFuncionario.objects.create(
            funcionario=self.func, descricao="A", valor=Decimal("100.00"),
            data=date(2026, 1, 10),
        )
        DespesaFuncionario.objects.create(
            funcionario=self.func, descricao="B", valor=Decimal("50.00"),
            data=date(2026, 1, 20),
        )
        DespesaFuncionario.objects.create(
            funcionario=self.func, descricao="C", valor=Decimal("30.00"),
            data=date(2026, 3, 5),
        )
        DespesaFuncionario.objects.create(
            funcionario=self.func, descricao="Velha", valor=Decimal("999.00"),
            data=date(2025, 6, 1),
        )

    def test_exige_autenticacao(self):
        self.client.force_authenticate(None)
        resp = self.client.get(f"{URL}?tipo=funcionario&entidade={self.func.id}&ano=2026")
        self.assertEqual(resp.status_code, 401)

    def test_totais_por_mes(self):
        resp = self.client.get(
            f"{URL}?tipo=funcionario&entidade={self.func.id}&ano=2026"
        )
        self.assertEqual(resp.status_code, 200)
        dados = resp.json()
        self.assertEqual(len(dados["meses"]), 12)
        # janeiro = 150, março = 30, resto = 0; ano = 180 (a de 2025 fica fora)
        jan = next(m for m in dados["meses"] if m["mes"] == 1)
        mar = next(m for m in dados["meses"] if m["mes"] == 3)
        fev = next(m for m in dados["meses"] if m["mes"] == 2)
        self.assertEqual(jan["total"], "150.00")
        self.assertEqual(mar["total"], "30.00")
        self.assertEqual(fev["total"], "0.00")
        self.assertEqual(dados["total_ano"], "180.00")

    def test_detalhe_de_um_mes(self):
        resp = self.client.get(
            f"{URL}?tipo=funcionario&entidade={self.func.id}&ano=2026&mes=1"
        )
        dados = resp.json()
        self.assertEqual(dados["mes"], 1)
        self.assertEqual(len(dados["detalhe"]), 2)
        descricoes = {d["descricao"] for d in dados["detalhe"]}
        self.assertEqual(descricoes, {"A", "B"})

    def test_tipo_invalido_da_400(self):
        resp = self.client.get(f"{URL}?tipo=xpto&entidade=1")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo", resp.json())

    def test_entidade_em_falta_da_400(self):
        resp = self.client.get(f"{URL}?tipo=funcionario")
        self.assertEqual(resp.status_code, 400)

    def test_ano_default_e_atual(self):
        # Sem ?ano, usa o ano atual — não deve rebentar.
        resp = self.client.get(f"{URL}?tipo=funcionario&entidade={self.func.id}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(dados_ano := resp.json()["ano"], date.today().year)

    def test_viaturas_tambem_funciona(self):
        v = Viatura.objects.create(matricula="00-AA-00", marca="VW", modelo="Caddy")
        DespesaViatura.objects.create(
            viatura=v, descricao="Pneus", valor=Decimal("200.00"),
            data=date(2026, 2, 1),
        )
        resp = self.client.get(
            f"{URL}?tipo=viatura&entidade={v.id}&ano=2026"
        )
        fev = next(m for m in resp.json()["meses"] if m["mes"] == 2)
        self.assertEqual(fev["total"], "200.00")

r"""
Testes do endpoint de alertas (Passo 4).

Correr: .\venv\Scripts\python.exe manage.py test alerts
"""

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from equipment.models import Certificado, Equipamento
from fleet.models import Inspecao, SeguroViatura, Viatura

User = get_user_model()


class AlertasTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u", password="segredo123")
        self.client.force_authenticate(self.user)

        self.viatura = Viatura.objects.create(
            matricula="00-AA-00", marca="VW", modelo="Caddy"
        )
        self.equip = Equipamento.objects.create(nome="Berbequim")

        hoje = date.today()
        # seguro já expirado (-5 dias) — deve aparecer e vir primeiro
        SeguroViatura.objects.create(
            viatura=self.viatura, seguradora="S", apolice="1",
            data_inicio=hoje, data_validade=hoje - timedelta(days=5),
        )
        # inspeção a expirar em 25 dias — dentro de 30 e 60
        Inspecao.objects.create(
            viatura=self.viatura, data_inspecao=hoje,
            data_validade=hoje + timedelta(days=25),
        )
        # certificado a expirar em 50 dias — dentro de 60, fora de 30
        Certificado.objects.create(
            equipamento=self.equip, tipo="CE", data_emissao=hoje,
            data_validade=hoje + timedelta(days=50),
        )
        # certificado a expirar em 200 dias — fora de qualquer janela testada
        Certificado.objects.create(
            equipamento=self.equip, tipo="CE2", data_emissao=hoje,
            data_validade=hoje + timedelta(days=200),
        )
        # seguro expirado há MUITO (200 dias) — fora do fundo default (90 dias)
        SeguroViatura.objects.create(
            viatura=self.viatura, seguradora="Velho", apolice="2",
            data_inicio=hoje - timedelta(days=400),
            data_validade=hoje - timedelta(days=200),
        )

    def test_exige_autenticacao(self):
        self.client.force_authenticate(None)
        resp = self.client.get("/api/alerts/")
        self.assertEqual(resp.status_code, 401)

    def test_janela_default_60_dias(self):
        resp = self.client.get("/api/alerts/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        # resposta paginada
        self.assertIn("results", body)
        dados = body["results"]
        # esperado: expirado(-5), inspeção(25), certificado(50) = 3. Ficam de fora
        # o de +200 dias (futuro) e o expirado há 200 dias (abaixo do fundo de 90).
        self.assertEqual(body["count"], 3)
        # ordenado do mais urgente: o primeiro é o expirado há 5 dias
        self.assertEqual(dados[0]["tipo"], "seguro")
        self.assertTrue(dados[0]["expirado"])
        self.assertEqual(dados[0]["dias_para_expirar"], -5)

    def test_fundo_da_janela_exclui_expirados_antigos(self):
        # Com fundo grande, o seguro expirado há 200 dias passa a aparecer.
        resp = self.client.get("/api/alerts/?expirados_desde=300")
        self.assertEqual(resp.json()["count"], 4)

    def test_expirados_desde_zero_so_mostra_futuros(self):
        # Sem fundo, nada de expirados: só inspeção(25) e certificado(50).
        resp = self.client.get("/api/alerts/?expirados_desde=0")
        tipos = {d["tipo"] for d in resp.json()["results"]}
        self.assertEqual(tipos, {"inspecao", "certificado"})

    def test_janela_30_dias_exclui_o_de_50(self):
        resp = self.client.get("/api/alerts/?dias=30")
        dados = resp.json()["results"]
        # esperado: expirado(-5) e inspeção(25); o certificado de 50 fica de fora
        self.assertEqual(len(dados), 2)
        tipos = {d["tipo"] for d in dados}
        self.assertEqual(tipos, {"seguro", "inspecao"})

    def test_dias_invalido_da_400(self):
        resp = self.client.get("/api/alerts/?dias=abc")
        self.assertEqual(resp.status_code, 400)

    def test_dias_negativo_da_400(self):
        resp = self.client.get("/api/alerts/?dias=-1")
        self.assertEqual(resp.status_code, 400)

    def test_formato_do_alerta(self):
        resp = self.client.get("/api/alerts/?dias=30")
        item = resp.json()["results"][1]  # a inspeção (índice 1 após o expirado)
        for chave in (
            "tipo", "descricao", "data_validade", "dias_para_expirar",
            "expirado", "recurso", "recurso_id", "registo_id",
        ):
            self.assertIn(chave, item)
        self.assertEqual(item["recurso"], "viatura")
        self.assertEqual(item["recurso_id"], self.viatura.id)

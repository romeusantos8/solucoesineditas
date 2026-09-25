r"""
Testes do endpoint de alertas (Passo 4).

Correr: .\venv\Scripts\python.exe manage.py test alerts
"""

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from employees.models import Funcionario
from equipment.models import Certificado, Equipamento
from fleet.models import Inspecao, SeguroViatura, Viatura
from health_records.models import FichaMedica

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
        # seguro expirado há MUITO (200 dias) — fora do fundo default (90 dias).
        # Noutra viatura: na mesma, o seguro de -5 dias contava como renovação
        # deste, e ele saía do dashboard por essa razão, não pelo fundo.
        outra_viatura = Viatura.objects.create(
            matricula="11-BB-11", marca="Ford", modelo="Transit"
        )
        SeguroViatura.objects.create(
            viatura=outra_viatura, seguradora="Velho", apolice="2",
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

    def test_janela_acima_do_maximo_da_400(self):
        # Sem teto, a data calculada passava do ano 9999 e o pedido dava 500.
        for param in ("dias", "expirados_desde"):
            resp = self.client.get(f"/api/alerts/?{param}=99999999")
            self.assertEqual(resp.status_code, 400, param)
            self.assertIn(param, resp.json())

    def test_janela_no_maximo_e_aceite(self):
        resp = self.client.get("/api/alerts/?dias=3650&expirados_desde=3650")
        self.assertEqual(resp.status_code, 200)

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


class AlertasSoPendentesTests(APITestCase):
    """
    O dashboard só mostra prazos que ainda precisam de atenção: não renovados
    e de recursos ativos.
    """

    def setUp(self):
        self.client.force_authenticate(
            User.objects.create_user(username="u", password="segredo123")
        )
        self.hoje = date.today()
        self.viatura = Viatura.objects.create(
            matricula="00-AA-00", marca="VW", modelo="Caddy"
        )
        self.equip = Equipamento.objects.create(nome="Grua")

    def _dias(self, n):
        return self.hoje + timedelta(days=n)

    def _alertas(self):
        return self.client.get("/api/alerts/").json()["results"]

    def _seguro(self, viatura, validade):
        return SeguroViatura.objects.create(
            viatura=viatura, seguradora="S", apolice="1",
            data_inicio=validade - timedelta(days=365), data_validade=validade,
        )

    def _certificado(self, tipo, validade):
        return Certificado.objects.create(
            equipamento=self.equip, tipo=tipo,
            data_emissao=validade - timedelta(days=365), data_validade=validade,
        )

    def test_seguro_renovado_sai_do_dashboard(self):
        self._seguro(self.viatura, self._dias(-5))   # expirou...
        self._seguro(self.viatura, self._dias(360))  # ...mas já foi renovado
        self.assertEqual(self._alertas(), [])

    def test_renovacao_tambem_a_expirar_so_mostra_a_mais_recente(self):
        self._seguro(self.viatura, self._dias(-5))
        novo = self._seguro(self.viatura, self._dias(20))
        alertas = self._alertas()
        self.assertEqual([a["registo_id"] for a in alertas], [novo.id])

    def test_inspecao_renovada_sai_do_dashboard(self):
        Inspecao.objects.create(
            viatura=self.viatura, data_inspecao=self._dias(-370),
            data_validade=self._dias(-5),
        )
        Inspecao.objects.create(
            viatura=self.viatura, data_inspecao=self._dias(-5),
            data_validade=self._dias(360),
        )
        self.assertEqual(self._alertas(), [])

    def test_certificado_so_e_renovado_pelo_mesmo_tipo(self):
        self._certificado("CE", self._dias(-5))
        self._certificado("ce", self._dias(360))  # mesmo tipo, outra capitalização
        pendente = self._certificado("Elevação", self._dias(10))
        alertas = self._alertas()
        # O CE está renovado; o de elevação (outro tipo) continua pendente.
        self.assertEqual([a["registo_id"] for a in alertas], [pendente.id])

    def test_viatura_inativa_nao_gera_alertas(self):
        self._seguro(self.viatura, self._dias(10))
        Inspecao.objects.create(
            viatura=self.viatura, data_inspecao=self._dias(-355),
            data_validade=self._dias(10),
        )
        self.viatura.ativa = False
        self.viatura.save()
        self.assertEqual(self._alertas(), [])

    def test_equipamento_inativo_nao_gera_alertas(self):
        self._certificado("CE", self._dias(10))
        self.equip.ativo = False
        self.equip.save()
        self.assertEqual(self._alertas(), [])

    def test_funcionario_inativo_nao_gera_alerta_da_ficha(self):
        func = Funcionario.objects.create(
            nome="Ana", funcao="Operadora", data_admissao=self._dias(-1000),
            ativo=False,
        )
        FichaMedica.objects.create(
            funcionario=func, aptidao="apto", data_exame=self._dias(-355),
            data_validade=self._dias(10),
        )
        self.assertEqual(self._alertas(), [])

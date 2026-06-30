r"""
Testes da API da Frota (Passo 3).

Correm numa base de dados de teste isolada (criada e destruída pelo Django),
por isso não tocam nos teus dados reais. Para correr:
    .\venv\Scripts\python.exe manage.py test
"""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APITestCase

from .models import DespesaViatura, SeguroViatura, Viatura

User = get_user_model()


class APIAuthTests(APITestCase):
    def test_lista_exige_autenticacao(self):
        resp = self.client.get("/api/viaturas/")
        self.assertEqual(resp.status_code, 401)

    def test_login_jwt_devolve_par_de_tokens_e_acede(self):
        User.objects.create_user(username="u", password="segredo123")
        resp = self.client.post(
            "/api/auth/token/", {"username": "u", "password": "segredo123"}
        )
        self.assertEqual(resp.status_code, 200)
        # JWT devolve access + refresh (já não um único "token")
        self.assertIn("access", resp.json())
        self.assertIn("refresh", resp.json())

        # o access autentica os pedidos via cabeçalho Bearer
        access = resp.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        self.assertEqual(self.client.get("/api/viaturas/").status_code, 200)

    def test_refresh_devolve_novo_access(self):
        User.objects.create_user(username="u", password="segredo123")
        login = self.client.post(
            "/api/auth/token/", {"username": "u", "password": "segredo123"}
        )
        refresh = login.json()["refresh"]
        resp = self.client.post("/api/auth/token/refresh/", {"refresh": refresh})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access", resp.json())

    def test_credenciais_erradas_dao_401(self):
        User.objects.create_user(username="u", password="segredo123")
        resp = self.client.post(
            "/api/auth/token/", {"username": "u", "password": "errada"}
        )
        self.assertEqual(resp.status_code, 401)


class ViaturaCrudTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u", password="segredo123")
        self.client.force_authenticate(self.user)

    def test_criar_e_listar_viatura(self):
        resp = self.client.post(
            "/api/viaturas/",
            {"matricula": "00-AA-00", "marca": "VW", "modelo": "Caddy"},
        )
        self.assertEqual(resp.status_code, 201)

        resp = self.client.get("/api/viaturas/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        # paginação ativa: resposta tem count/results
        self.assertIn("count", body)
        self.assertIn("results", body)
        self.assertEqual(body["count"], 1)

    def test_seguro_expoe_dias_para_expirar(self):
        viatura = Viatura.objects.create(
            matricula="11-BB-11", marca="Ford", modelo="Transit"
        )
        validade = date.today() + timedelta(days=20)
        resp = self.client.post(
            "/api/seguros/",
            {
                "viatura": viatura.id,
                "seguradora": "Fidelidade",
                "apolice": "AP1",
                "data_inicio": date.today().isoformat(),
                "data_validade": validade.isoformat(),
            },
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["dias_para_expirar"], 20)


class FiltroFkTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u", password="segredo123")
        self.client.force_authenticate(self.user)
        self.v1 = Viatura.objects.create(matricula="A", marca="X", modelo="Y")
        self.v2 = Viatura.objects.create(matricula="B", marca="X", modelo="Y")
        SeguroViatura.objects.create(
            viatura=self.v1, seguradora="S", apolice="1",
            data_inicio=date.today(), data_validade=date.today(),
        )

    def test_filtra_seguros_por_viatura(self):
        resp = self.client.get(f"/api/seguros/?viatura={self.v1.id}")
        self.assertEqual(resp.json()["count"], 1)

    def test_filtro_viatura_sem_resultados(self):
        resp = self.client.get(f"/api/seguros/?viatura={self.v2.id}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 0)


class ValidacaoModelTests(TestCase):
    """Regras de negócio ao nível do model (o que o Admin também aplica)."""

    def test_matricula_normalizada(self):
        v = Viatura(matricula="  aa-00-bb ", marca="X", modelo="Y")
        v.full_clean()
        self.assertEqual(v.matricula, "AA-00-BB")

    def test_ano_demasiado_recente_rejeitado(self):
        v = Viatura(matricula="11-CC-11", marca="X", modelo="Y", ano=date.today().year + 5)
        with self.assertRaises(ValidationError):
            v.full_clean()

    def test_ano_demasiado_antigo_rejeitado(self):
        v = Viatura(matricula="22-DD-22", marca="X", modelo="Y", ano=1900)
        with self.assertRaises(ValidationError):
            v.full_clean()

    def test_seguro_validade_antes_do_inicio_rejeitado(self):
        v = Viatura.objects.create(matricula="33-EE-33", marca="X", modelo="Y")
        s = SeguroViatura(
            viatura=v, seguradora="S", apolice="1",
            data_inicio=date.today(), data_validade=date.today() - timedelta(days=1),
        )
        with self.assertRaises(ValidationError):
            s.full_clean()

    def test_despesa_valor_zero_rejeitado(self):
        v = Viatura.objects.create(matricula="44-FF-44", marca="X", modelo="Y")
        d = DespesaViatura(viatura=v, descricao="X", valor=Decimal("0.00"), data=date.today())
        with self.assertRaises(ValidationError):
            d.full_clean()


class AuditoriaTests(APITestCase):
    """criado_por/atualizado_por preenchidos com o utilizador do pedido."""

    def setUp(self):
        self.user = User.objects.create_user(username="autor", password="segredo123")
        self.client.force_authenticate(self.user)

    def test_criar_preenche_criado_por(self):
        resp = self.client.post(
            "/api/viaturas/",
            {"matricula": "88-JJ-88", "marca": "X", "modelo": "Y"},
        )
        self.assertEqual(resp.status_code, 201)
        viatura = Viatura.objects.get(id=resp.json()["id"])
        self.assertEqual(viatura.criado_por, self.user)
        self.assertEqual(viatura.atualizado_por, self.user)
        # também aparece (read-only) na resposta
        self.assertEqual(resp.json()["criado_por"], self.user.id)

    def test_atualizar_muda_so_atualizado_por(self):
        outro = User.objects.create_user(username="editor", password="segredo123")
        viatura = Viatura.objects.create(
            matricula="99-KK-99", marca="X", modelo="Y",
            criado_por=outro, atualizado_por=outro,
        )
        resp = self.client.patch(f"/api/viaturas/{viatura.id}/", {"marca": "Z"})
        self.assertEqual(resp.status_code, 200)
        viatura.refresh_from_db()
        self.assertEqual(viatura.criado_por, outro)       # inalterado
        self.assertEqual(viatura.atualizado_por, self.user)  # quem editou


class ValidacaoApiTests(APITestCase):
    """As mesmas regras têm de valer na API (resposta 400)."""

    def setUp(self):
        self.user = User.objects.create_user(username="u", password="segredo123")
        self.client.force_authenticate(self.user)

    def test_api_rejeita_ano_invalido(self):
        resp = self.client.post(
            "/api/viaturas/",
            {"matricula": "55-GG-55", "marca": "X", "modelo": "Y", "ano": 3000},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("ano", resp.json())

    def test_api_normaliza_matricula(self):
        resp = self.client.post(
            "/api/viaturas/",
            {"matricula": " zz-99-zz ", "marca": "X", "modelo": "Y"},
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["matricula"], "ZZ-99-ZZ")

    def test_api_rejeita_seguro_com_validade_anterior(self):
        v = Viatura.objects.create(matricula="66-HH-66", marca="X", modelo="Y")
        resp = self.client.post("/api/seguros/", {
            "viatura": v.id, "seguradora": "S", "apolice": "1",
            "data_inicio": date.today().isoformat(),
            "data_validade": (date.today() - timedelta(days=1)).isoformat(),
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn("data_validade", resp.json())

    def test_api_rejeita_despesa_valor_negativo(self):
        v = Viatura.objects.create(matricula="77-II-77", marca="X", modelo="Y")
        resp = self.client.post("/api/despesas/", {
            "viatura": v.id, "descricao": "X", "valor": "-10.00",
            "data": date.today().isoformat(),
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn("valor", resp.json())

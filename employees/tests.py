r"""
Testes da app de Funcionários.

NIF de exemplo válido: 123456789 (dígito de controlo confere).
Correr: .\venv\Scripts\python.exe manage.py test employees
"""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APITestCase

from .models import DespesaFuncionario, Funcionario, validar_nif

User = get_user_model()

NIF_VALIDO = "123456789"


class ValidarNifTests(TestCase):
    def test_nif_valido_passa(self):
        validar_nif(NIF_VALIDO)  # não deve levantar

    def test_nif_com_checksum_errado_falha(self):
        with self.assertRaises(ValidationError):
            validar_nif("123456780")  # último dígito devia ser 9

    def test_nif_com_menos_de_9_digitos_falha(self):
        with self.assertRaises(ValidationError):
            validar_nif("12345")

    def test_nif_com_letras_falha(self):
        with self.assertRaises(ValidationError):
            validar_nif("12345678X")


class FuncionarioModelTests(TestCase):
    def test_clean_aceita_sem_nif(self):
        f = Funcionario(nome="Ana", funcao="Operadora", data_admissao=date.today())
        f.full_clean()  # nif vazio é permitido

    def test_clean_rejeita_nif_invalido(self):
        f = Funcionario(
            nome="Ana", funcao="X", data_admissao=date.today(), nif="111111111"
        )
        with self.assertRaises(ValidationError):
            f.full_clean()


class FuncionarioApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u", password="segredo123")
        self.client.force_authenticate(self.user)

    def test_exige_autenticacao(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/funcionarios/").status_code, 401)

    def test_criar_e_listar(self):
        resp = self.client.post(
            "/api/funcionarios/",
            {"nome": "João", "funcao": "Operador", "data_admissao": date.today().isoformat()},
        )
        self.assertEqual(resp.status_code, 201)
        # auditoria preenchida
        self.assertEqual(resp.json()["criado_por"], self.user.id)

        lista = self.client.get("/api/funcionarios/").json()
        self.assertIn("results", lista)  # paginado
        self.assertEqual(lista["count"], 1)

    def test_api_rejeita_nif_invalido(self):
        resp = self.client.post("/api/funcionarios/", {
            "nome": "X", "funcao": "Y", "data_admissao": date.today().isoformat(),
            "nif": "111111111",
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn("nif", resp.json())

    def test_api_aceita_nif_valido(self):
        resp = self.client.post("/api/funcionarios/", {
            "nome": "X", "funcao": "Y", "data_admissao": date.today().isoformat(),
            "nif": NIF_VALIDO,
        })
        self.assertEqual(resp.status_code, 201)

    def test_despesa_valor_negativo_rejeitado(self):
        f = Funcionario.objects.create(
            nome="Z", funcao="W", data_admissao=date.today()
        )
        resp = self.client.post("/api/despesas-funcionarios/", {
            "funcionario": f.id, "descricao": "X", "valor": "-5.00",
            "data": date.today().isoformat(),
        })
        self.assertEqual(resp.status_code, 400)

    def test_filtra_despesas_por_funcionario(self):
        f = Funcionario.objects.create(
            nome="Z", funcao="W", data_admissao=date.today()
        )
        DespesaFuncionario.objects.create(
            funcionario=f, descricao="Formação", valor=Decimal("100.00"),
            data=date.today(),
        )
        resp = self.client.get(f"/api/despesas-funcionarios/?funcionario={f.id}")
        self.assertEqual(resp.json()["count"], 1)


class PortalFuncionarioTests(APITestCase):
    """Conta de funcionário: só vê o portal (as suas despesas), nada mais."""

    def setUp(self):
        self.gestor = User.objects.create_user(username="gestor", password="segredo123")
        self.conta = User.objects.create_user(username="ana", password="segredo123")
        self.ana = Funcionario.objects.create(
            nome="Ana", funcao="Operadora", data_admissao=date.today(),
            utilizador=self.conta,
        )
        self.rui = Funcionario.objects.create(
            nome="Rui", funcao="Operador", data_admissao=date.today()
        )
        DespesaFuncionario.objects.create(
            funcionario=self.rui, descricao="Do Rui", valor=Decimal("10.00"),
            data=date.today(),
        )
        self.client.force_authenticate(self.conta)

    def test_funcionario_nao_acede_a_gestao(self):
        for url in ["/api/funcionarios/", "/api/despesas-funcionarios/",
                    "/api/viaturas/", "/api/alerts/",
                    "/api/reports/equipamentos-funcionario/?funcionario=1"]:
            self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_regista_despesa_em_seu_nome(self):
        resp = self.client.post("/api/minhas-despesas/", {
            "descricao": "Gasóleo", "valor": "40.00",
            "data": date.today().isoformat(),
            "funcionario": self.rui.id,  # ignorado: é sempre o próprio
        })
        self.assertEqual(resp.status_code, 201)
        despesa = DespesaFuncionario.objects.get(pk=resp.json()["id"])
        self.assertEqual(despesa.funcionario, self.ana)
        self.assertEqual(despesa.criado_por, self.conta)

    def test_so_lista_as_proprias(self):
        DespesaFuncionario.objects.create(
            funcionario=self.ana, descricao="Da Ana", valor=Decimal("5.00"),
            data=date.today(),
        )
        lista = self.client.get("/api/minhas-despesas/").json()
        self.assertEqual([d["descricao"] for d in lista["results"]], ["Da Ana"])

    def test_portal_valida_valor(self):
        resp = self.client.post("/api/minhas-despesas/", {
            "descricao": "X", "valor": "0", "data": date.today().isoformat(),
        })
        self.assertEqual(resp.status_code, 400)

    def test_funcionario_inativo_sem_portal(self):
        self.ana.ativo = False
        self.ana.save()
        self.assertEqual(self.client.get("/api/minhas-despesas/").status_code, 403)
        self.assertEqual(self.client.get("/api/eu/").json()["perfil"], "sem_acesso")

    def test_gestor_nao_usa_portal(self):
        self.client.force_authenticate(self.gestor)
        self.assertEqual(self.client.get("/api/minhas-despesas/").status_code, 403)
        self.assertEqual(self.client.get("/api/funcionarios/").status_code, 200)

    def test_staff_ligado_a_funcionario_mantem_gestao(self):
        self.conta.is_staff = True
        self.conta.save()
        self.assertEqual(self.client.get("/api/funcionarios/").status_code, 200)
        self.assertEqual(self.client.get("/api/minhas-despesas/").status_code, 200)

    def test_eu_indica_perfil(self):
        dados = self.client.get("/api/eu/").json()
        self.assertEqual(dados["perfil"], "funcionario")
        self.assertEqual(dados["funcionario"]["id"], self.ana.id)
        self.client.force_authenticate(self.gestor)
        self.assertEqual(self.client.get("/api/eu/").json()["perfil"], "gestao")


class AcessoFuncionarioTests(APITestCase):
    """Gestão da conta do portal a partir da app (/funcionarios/{id}/acesso/)."""

    def setUp(self):
        self.gestor = User.objects.create_user(username="gestor", password="segredo123")
        self.client.force_authenticate(self.gestor)
        self.func = Funcionario.objects.create(
            nome="Ana", funcao="Operadora", data_admissao=date.today()
        )
        self.url = f"/api/funcionarios/{self.func.id}/acesso/"

    def criar_acesso(self, password="Obra-Segura-2026"):
        return self.client.post(self.url, {"username": "ana", "password": password})

    def test_criar_acesso_e_fazer_login(self):
        resp = self.criar_acesso()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["acesso"], {"username": "ana", "ativo": True})
        self.client.force_authenticate(None)
        login = self.client.post(
            "/api/auth/token/", {"username": "ana", "password": "Obra-Segura-2026"}
        )
        self.assertEqual(login.status_code, 200)

    def test_password_fraca_rejeitada(self):
        resp = self.criar_acesso(password="123")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("password", resp.json())
        self.func.refresh_from_db()
        self.assertIsNone(self.func.utilizador)

    def test_username_duplicado_rejeitado(self):
        resp = self.client.post(self.url, {"username": "GESTOR", "password": "Obra-Segura-2026"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("username", resp.json())

    def test_trocar_password_mantem_a_mesma_conta(self):
        self.criar_acesso()
        conta = Funcionario.objects.get(pk=self.func.pk).utilizador
        resp = self.criar_acesso(password="Outra-Senha-Forte-9")
        self.assertEqual(resp.status_code, 200)
        conta.refresh_from_db()
        self.assertTrue(conta.check_password("Outra-Senha-Forte-9"))
        self.assertEqual(User.objects.filter(username="ana").count(), 1)

    def test_revogar_desativa_mas_mantem_ligacao(self):
        self.criar_acesso()
        resp = self.client.delete(self.url)
        self.assertEqual(resp.json()["acesso"], {"username": "ana", "ativo": False})
        self.func.refresh_from_db()
        self.assertFalse(self.func.utilizador.is_active)

    def test_apagar_funcionario_desativa_conta(self):
        self.criar_acesso()
        conta = Funcionario.objects.get(pk=self.func.pk).utilizador
        self.client.delete(f"/api/funcionarios/{self.func.id}/")
        conta.refresh_from_db()
        self.assertFalse(conta.is_active)

    def test_funcionario_nao_gere_acessos(self):
        self.criar_acesso()
        conta = Funcionario.objects.get(pk=self.func.pk).utilizador
        self.client.force_authenticate(conta)
        resp = self.client.post(self.url, {"username": "ana", "password": "X-Nova-Senha-77"})
        self.assertEqual(resp.status_code, 403)

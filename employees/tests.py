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

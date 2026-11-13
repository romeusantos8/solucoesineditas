r"""
Testes da app de Funcionários.

NIF de exemplo válido: 123456789 (dígito de controlo confere).
Correr: .\venv\Scripts\python.exe manage.py test employees
"""

import re
import time
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from rest_framework.test import APITestCase
from rest_framework.throttling import ScopedRateThrottle

from .models import DespesaFuncionario, Funcionario, validar_nif
from .notificacoes import token_pagamento

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


class ThreadImediata:
    """Substitui a Thread nos testes: corre logo, para se poder ver o resultado."""

    def __init__(self, target, args, daemon):
        self.target, self.args = target, args

    def start(self):
        self.target(*self.args)


@override_settings(NOTIFICACAO_DESPESAS_EMAILS=["pagamentos@example.com"])
@patch("employees.notificacoes.threading.Thread", ThreadImediata)
class NotificacaoDespesaTests(APITestCase):
    """Email de nova despesa e link para a marcar como paga."""

    def setUp(self):
        # O contador do limite de pedidos vive na cache e sobrevive entre testes.
        cache.clear()
        self.conta = User.objects.create_user(username="ana", password="segredo123")
        self.ana = Funcionario.objects.create(
            nome="Ana", funcao="Operadora", data_admissao=date.today(),
            utilizador=self.conta,
        )
        self.gestor = User.objects.create_user(username="gestor", password="segredo123")

    def registar(self, **extra):
        self.client.force_authenticate(self.conta)
        return self.client.post("/api/minhas-despesas/", {
            "descricao": "Gasóleo", "valor": "40.00",
            "data": date.today().isoformat(), **extra,
        })

    def despesa(self):
        return DespesaFuncionario.objects.create(
            funcionario=self.ana, descricao="Almoço", valor=Decimal("12.50"),
            data=date.today(), atualizado_por=self.conta,
        )

    def url(self, despesa):
        return f"/api/confirmar-pagamento/{token_pagamento(despesa)}/"

    def test_portal_envia_email_com_link(self):
        self.assertEqual(self.registar().status_code, 201)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ["pagamentos@example.com"])
        self.assertIn("Ana", email.subject)
        self.assertIn("Gasóleo", email.body)
        html = email.alternatives[0][0]
        self.assertIn("Marcar como paga", html)
        # O link do email abre a página de confirmação.
        link = re.search(r'href="([^"]+)"', html).group(1)
        self.assertEqual(self.client.get(link).status_code, 200)

    def test_gestao_nao_envia_email(self):
        self.client.force_authenticate(self.gestor)
        resp = self.client.post("/api/despesas-funcionarios/", {
            "funcionario": self.ana.id, "descricao": "X", "valor": "1.00",
            "data": date.today().isoformat(),
        })
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(mail.outbox, [])

    def test_falha_no_envio_nao_impede_o_registo(self):
        with patch(
            "django.core.mail.EmailMultiAlternatives.send", side_effect=OSError("sem rede")
        ), self.assertLogs("employees.notificacoes", level="ERROR"):
            resp = self.registar()
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(DespesaFuncionario.objects.filter(pk=resp.json()["id"]).exists())

    def test_funcionario_nao_marca_a_propria_despesa_como_paga(self):
        resp = self.registar(paga=True)
        self.assertEqual(resp.status_code, 201)
        self.assertFalse(resp.json()["paga"])
        self.assertFalse(DespesaFuncionario.objects.get(pk=resp.json()["id"]).paga)

    def test_abrir_o_link_nao_marca_como_paga(self):
        despesa = self.despesa()
        resp = self.client.get(self.url(despesa))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Confirmar pagamento")
        despesa.refresh_from_db()
        self.assertFalse(despesa.paga)

    def test_confirmar_marca_como_paga_sem_sessao(self):
        despesa = self.despesa()
        resp = self.client.post(self.url(despesa))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "marcada como paga")
        self.assertNotContains(resp, "Confirmar pagamento")
        despesa.refresh_from_db()
        self.assertTrue(despesa.paga)
        self.assertIsNone(despesa.atualizado_por)
        # Repetir (refresh da página) não dá erro.
        self.assertEqual(self.client.post(self.url(despesa)).status_code, 200)

    def test_token_invalido_da_404(self):
        despesa = self.despesa()
        for metodo in (self.client.get, self.client.post):
            resp = metodo("/api/confirmar-pagamento/adulterado/")
            self.assertEqual(resp.status_code, 404)
        adulterado = f"{token_pagamento(despesa)}x"
        self.assertEqual(
            self.client.post(f"/api/confirmar-pagamento/{adulterado}/").status_code, 404
        )
        despesa.refresh_from_db()
        self.assertFalse(despesa.paga)

    def url_com_dias(self, despesa, dias):
        """Link gerado há `dias` dias: o relógio só recua enquanto se assina."""
        with patch("time.time", return_value=time.time() - dias * 86400):
            return self.url(despesa)

    def test_link_expirado_da_404(self):
        despesa = self.despesa()
        url = self.url_com_dias(despesa, 31)
        for metodo in (self.client.get, self.client.post):
            self.assertEqual(metodo(url).status_code, 404)
        despesa.refresh_from_db()
        self.assertFalse(despesa.paga)

    def test_link_dentro_do_prazo_funciona(self):
        despesa = self.despesa()
        self.assertEqual(self.client.get(self.url_com_dias(despesa, 29)).status_code, 200)

    def test_despesa_apagada_da_404(self):
        despesa = self.despesa()
        url = self.url(despesa)
        despesa.delete()
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_gestao_altera_e_filtra_por_paga(self):
        despesa = self.despesa()
        self.client.force_authenticate(self.gestor)
        resp = self.client.patch(
            f"/api/despesas-funcionarios/{despesa.id}/", {"paga": True}, format="json"
        )
        self.assertTrue(resp.json()["paga"])
        lista = self.client.get("/api/despesas-funcionarios/?paga=false").json()
        self.assertEqual(lista["results"], [])

    def test_portal_limita_registos_mas_nao_listagem(self):
        # Limite reduzido só neste teste, para não fazer 30 pedidos.
        with patch.object(ScopedRateThrottle, "THROTTLE_RATES", {"despesas_portal": "2/hour"}):
            self.assertEqual(self.registar().status_code, 201)
            self.assertEqual(self.registar().status_code, 201)
            self.assertEqual(self.registar().status_code, 429)
            self.assertEqual(DespesaFuncionario.objects.filter(funcionario=self.ana).count(), 2)
            self.assertEqual(self.client.get("/api/minhas-despesas/").status_code, 200)


class PortalFuncionarioTests(APITestCase):
    """Conta de funcionário: só vê o portal (as suas despesas), nada mais."""

    def setUp(self):
        # O contador do limite de pedidos vive na cache e sobrevive entre testes.
        cache.clear()
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

    def test_nao_gere_conta_de_staff_ligada_a_funcionario(self):
        # Um staff pode estar ligado a um funcionário (ex.: o dono). Sem esta
        # proteção, um gestor comum podia trocar-lhe a palavra-passe e entrar
        # como administrador.
        dono = User.objects.create_user(username="dono", password="segredo123", is_staff=True)
        self.func.utilizador = dono
        self.func.save()
        resp = self.client.post(self.url, {"username": "dono", "password": "Nova-Senha-Forte-1"})
        self.assertEqual(resp.status_code, 403)
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, 403)
        dono.refresh_from_db()
        self.assertTrue(dono.check_password("segredo123"))
        self.assertTrue(dono.is_active)

    def test_trocar_password_expulsa_as_sessoes_abertas(self):
        # Sessão aberta: o funcionário fez login com a password antiga.
        self.criar_acesso()
        self.client.force_authenticate(None)
        login = self.client.post(
            "/api/auth/token/", {"username": "ana", "password": "Obra-Segura-2026"}
        ).json()
        access, refresh = login["access"], login["refresh"]

        # A gestão troca a password.
        self.client.force_authenticate(self.gestor)
        self.criar_acesso(password="Outra-Senha-Forte-9")

        # O access antigo deixa de valer, mesmo dentro dos 5 minutos.
        self.client.force_authenticate(None)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        self.assertEqual(self.client.get("/api/minhas-despesas/").status_code, 401)

        # O refresh antigo não serve: se der um access novo, esse também é recusado.
        resp = self.client.post("/api/auth/token/refresh/", {"refresh": refresh}, format="json")
        if resp.status_code == 200:
            self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['access']}")
            self.assertEqual(self.client.get("/api/minhas-despesas/").status_code, 401)
        else:
            self.assertEqual(resp.status_code, 401)

    def test_login_com_password_nova_funciona(self):
        self.criar_acesso()
        self.client.force_authenticate(self.gestor)
        self.criar_acesso(password="Outra-Senha-Forte-9")
        self.client.force_authenticate(None)
        resp = self.client.post(
            "/api/auth/token/", {"username": "ana", "password": "Outra-Senha-Forte-9"}
        )
        self.assertEqual(resp.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['access']}")
        self.assertEqual(self.client.get("/api/minhas-despesas/").status_code, 200)

    def test_funcionario_nao_gere_acessos(self):
        self.criar_acesso()
        conta = Funcionario.objects.get(pk=self.func.pk).utilizador
        self.client.force_authenticate(conta)
        resp = self.client.post(self.url, {"username": "ana", "password": "X-Nova-Senha-77"})
        self.assertEqual(resp.status_code, 403)

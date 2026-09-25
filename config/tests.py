r"""
Testes das configurações transversais do projeto (settings e urls), que não
pertencem a nenhuma app de domínio.

Correm numa base de dados de teste isolada. Para correr só estes:
    .\venv\Scripts\python.exe manage.py test config
"""

import io
import json
import logging
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework.test import APITestCase

from fleet.views import ViaturaViewSet

User = get_user_model()


class DocumentacaoApiTests(APITestCase):
    """O esquema OpenAPI e o Swagger só estão acessíveis a staff."""

    URLS = ("/api/schema/", "/api/docs/")

    def test_anonimo_nao_ve_documentacao(self):
        for url in self.URLS:
            self.assertEqual(self.client.get(url).status_code, 401, url)

    def test_utilizador_normal_nao_ve_documentacao(self):
        self.client.force_authenticate(
            User.objects.create_user(username="u", password="segredo123")
        )
        for url in self.URLS:
            self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_staff_ve_documentacao(self):
        self.client.force_authenticate(
            User.objects.create_user(
                username="s", password="segredo123", is_staff=True
            )
        )
        # Só a página do Swagger: gerar o esquema completo aqui encheria a saída
        # dos testes com os avisos do drf-spectacular.
        self.assertEqual(self.client.get("/api/docs/").status_code, 200)


class LogsTests(APITestCase):
    """Um erro 500 tem de aparecer na consola também com DEBUG=False."""

    def test_erro_500_aparece_na_consola(self):
        self.client.force_authenticate(
            User.objects.create_user(username="u", password="segredo123")
        )
        # Devolver o 500 em vez de o test client relançar a exceção.
        self.client.raise_request_exception = False

        # Os testes correm sempre com DEBUG=False, como em produção. Desvia a
        # saída da consola para um buffer (e repõe-na no fim do teste).
        saida = io.StringIO()
        for handler in logging.getLogger("django").handlers:
            if isinstance(handler, logging.StreamHandler):
                self.addCleanup(handler.setStream, handler.setStream(saida))

        with mock.patch.object(
            ViaturaViewSet, "list", side_effect=RuntimeError("falha de teste")
        ):
            resp = self.client.get("/api/viaturas/")

        self.assertEqual(resp.status_code, 500)
        self.assertIn("RuntimeError: falha de teste", saida.getvalue())


class LimiteTentativasLoginTests(APITestCase):
    """
    django-axes: 5 falhas seguidas bloqueiam o par utilizador + IP durante 15
    minutos, em todos os sítios de login. O `assertLogs` apanha os avisos que o
    axes escreve a cada falha (em produção vão para os logs; aqui só sujavam a
    saída dos testes).
    """

    def setUp(self):
        User.objects.create_user(username="u", password="segredo123", is_staff=True)

    def _login(self, password, ip="1.1.1.1"):
        # Em produção, o IP real chega no X-Forwarded-For (proxy do Railway).
        return self.client.post(
            "/api/auth/token/",
            {"username": "u", "password": password},
            HTTP_X_FORWARDED_FOR=ip,
        )

    def _falhar(self, vezes, ip="1.1.1.1"):
        for _ in range(vezes):
            self._login("errada", ip)

    def test_bloqueia_apos_5_falhas_mesmo_com_password_certa(self):
        with self.assertLogs("axes", "WARNING"):
            self._falhar(5)
            resp = self._login("segredo123")
        # 429 com a mensagem de bloqueio, e não o 401 de credenciais erradas.
        self.assertEqual(resp.status_code, 429)
        self.assertIn("Tenta novamente", resp.json()["detail"])

    def test_4_falhas_ainda_nao_bloqueiam(self):
        with self.assertLogs("axes", "WARNING"):
            self._falhar(4)
        self.assertEqual(self._login("segredo123").status_code, 200)

    def test_outro_ip_nao_fica_bloqueado(self):
        with self.assertLogs("axes", "WARNING"):
            self._falhar(5, ip="1.1.1.1")
        self.assertEqual(self._login("segredo123", ip="2.2.2.2").status_code, 200)

    def test_forjar_o_ip_nao_contorna_o_bloqueio(self):
        # O cliente pode pôr o que quiser à esquerda do X-Forwarded-For; o
        # proxy acrescenta o IP real no fim, e é esse que conta.
        with self.assertLogs("axes", "WARNING"):
            self._falhar(5, ip="1.1.1.1")
            resp = self._login("segredo123", ip="9.9.9.9, 1.1.1.1")
        self.assertEqual(resp.status_code, 429)

    def test_admin_tambem_bloqueia(self):
        navegador = Client(HTTP_X_FORWARDED_FOR="1.1.1.1")
        with self.assertLogs("axes", "WARNING"):
            for _ in range(5):
                navegador.post(
                    "/admin/login/", {"username": "u", "password": "errada"}
                )
            resp = navegador.post(
                "/admin/login/", {"username": "u", "password": "segredo123"}
            )
        self.assertEqual(resp.status_code, 429)
        self.assertNotIn("_auth_user_id", navegador.session)

    def test_login_da_api_navegavel_nao_existe_em_producao(self):
        # Os testes correm com DEBUG=False, como em produção.
        self.assertEqual(self.client.get("/api-auth/login/").status_code, 404)


class CspTests(APITestCase):
    """
    Content Security Policy: as páginas trazem a política, nenhuma página
    depende de scripts embutidos ou de sites externos, e os relatórios de
    violação dos browsers chegam aos logs.
    """

    def _politica(self, resp):
        # Vale para as duas fases (só avisar / bloquear).
        return resp.headers.get("Content-Security-Policy") or resp.headers.get(
            "Content-Security-Policy-Report-Only", ""
        )

    def test_paginas_trazem_a_politica(self):
        for url in ("/", "/admin/login/"):
            politica = self._politica(self.client.get(url))
            self.assertIn("script-src 'self'", politica, url)
            self.assertIn("report-uri /api/csp-report/", politica, url)

    def test_documentacao_sem_scripts_embutidos_nem_cdn(self):
        self.client.force_authenticate(
            User.objects.create_user(
                username="s", password="segredo123", is_staff=True
            )
        )
        resp = self.client.get("/api/docs/")
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertNotIn("<script>", html)  # script de arranque vem à parte
        self.assertNotIn("cdn.jsdelivr.net", html)  # ficheiros servidos pela app
        # O script de arranque, pedido à parte, existe.
        script = self.client.get("/api/docs/?script=")
        self.assertEqual(script.status_code, 200)
        self.assertIn("SwaggerUIBundle", script.content.decode())

    def test_relatorio_de_violacao_vai_para_os_logs(self):
        # Como um browser: sem login e sem token CSRF.
        browser = Client(enforce_csrf_checks=True)
        relatorio = {
            "csp-report": {
                "blocked-uri": "https://mau.example/x.js",
                "violated-directive": "script-src",
                "document-uri": "https://app.example/obras/3",
            }
        }
        with self.assertLogs("config.csp", "WARNING") as logs:
            resp = browser.post(
                "/api/csp-report/",
                data=json.dumps(relatorio),
                content_type="application/csp-report",
            )
        self.assertEqual(resp.status_code, 204)
        self.assertIn("https://mau.example/x.js", logs.output[0])

    def test_relatorio_invalido_e_recusado(self):
        browser = Client(enforce_csrf_checks=True)
        resp = browser.post(
            "/api/csp-report/", data="lixo", content_type="application/csp-report"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(browser.get("/api/csp-report/").status_code, 405)

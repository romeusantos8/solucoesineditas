r"""
Testes das configurações transversais do projeto (settings e urls), que não
pertencem a nenhuma app de domínio.

Correm numa base de dados de teste isolada. Para correr só estes:
    .\venv\Scripts\python.exe manage.py test config
"""

import io
import logging
from unittest import mock

from django.contrib.auth import get_user_model
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

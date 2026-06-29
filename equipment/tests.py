r"""
Testes de Equipamentos: validação do certificado (Passo 4 / validações).

Correr: .\venv\Scripts\python.exe manage.py test equipment
"""

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APITestCase

from .models import Certificado, Equipamento

User = get_user_model()


class CertificadoValidacaoModelTests(TestCase):
    def test_validade_antes_da_emissao_rejeitada(self):
        e = Equipamento.objects.create(nome="Berbequim")
        c = Certificado(
            equipamento=e, tipo="CE", data_emissao=date.today(),
            data_validade=date.today() - timedelta(days=1),
        )
        with self.assertRaises(ValidationError):
            c.full_clean()


class CertificadoValidacaoApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u", password="segredo123")
        self.client.force_authenticate(self.user)

    def test_api_rejeita_validade_anterior_a_emissao(self):
        e = Equipamento.objects.create(nome="Berbequim")
        resp = self.client.post("/api/certificados/", {
            "equipamento": e.id, "tipo": "CE",
            "data_emissao": date.today().isoformat(),
            "data_validade": (date.today() - timedelta(days=1)).isoformat(),
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn("data_validade", resp.json())

    def test_api_aceita_certificado_valido(self):
        e = Equipamento.objects.create(nome="Compressor")
        resp = self.client.post("/api/certificados/", {
            "equipamento": e.id, "tipo": "CE",
            "data_emissao": date.today().isoformat(),
            "data_validade": (date.today() + timedelta(days=365)).isoformat(),
        })
        self.assertEqual(resp.status_code, 201)

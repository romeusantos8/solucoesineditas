"""
Models da app de utilizadores.

Por agora está VAZIO de propósito: usamos o User e os Groups que já vêm com o
Django (django.contrib.auth), por isso não precisamos de criar models aqui.

GANCHO PARA O FUTURO (não construir agora):
  - Um modelo `Perfil` (OneToOne com User) para guardar dados extra do funcionário.
  - Os papéis/roles serão feitos com Django Groups (criados no Admin), não com
    código novo nesta fase.
  - ⚠️ RGPD: dados de saúde (fichas médicas) NÃO virão para aqui. Ficarão numa
    app própria e separada (ex.: `medical`), com acesso restrito e cifragem.
    Manter esta app livre desses dados é parte do desenho de privacidade.
"""

# (Sem models por agora — ver explicação acima.)

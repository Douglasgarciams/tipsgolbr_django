# tips_core/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Rotas Públicas
    path('', views.public_tips_list, name='home'),
    path('acesso-negado/', views.access_denied, name='access_denied'),
    path('register/', views.register, name='register'),
    path('analysis/dashboard/', views.analysis_dashboard, name='analysis_dashboard'),

    # Navbar Premium
    path('premium/', views.go_to_premium, name='premium_link'),

    # Conteúdo Premium
    path('premium/content/', views.premium_tips, name='premium_tips_content'),

    # --------------------------------------------------------------------
    # NOVO FLUXO DE PAGAMENTO
    # --------------------------------------------------------------------

    # 1. Página para escolher o plano
    path('checkout/planos/', views.choose_plan, name='choose_plan'),

    # 2. Rota correta que manda para o PagSeguro
    path('checkout/pagseguro/<int:plan_id>/', views.redirect_pagseguro, name='redirect_pagseguro'),

    # 3. Rota de confirmação do pagamento
    path('checkout/confirmar/<str:username>/', views.confirm_payment, name='confirm_payment'),
]

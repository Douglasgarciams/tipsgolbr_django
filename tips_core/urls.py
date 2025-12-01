# tips_core/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Rotas Públicas
    path('', views.public_tips_list, name='home'),
    path('acesso-negado/', views.access_denied, name='access_denied'),
    path('register/', views.register, name='register'),
    
    # Rota de Análise de Desempenho (NOVA IMPLEMENTAÇÃO)
    path('dashboard-analise/', views.analysis_dashboard, name='analysis_dashboard'),

    # Rota da Calculadora (CORRIGIDA)
    path('calculadora-dutching/', views.calculator_page, name='calculator_page'),
    
    # Rota do Botão 'Premium' no Navbar (Go-to-Premium)
    path('premium/', views.go_to_premium, name='premium_link'), 
    
    # Rota de CONTEÚDO Premium (Protegida pelo @login_required na view)
    path('premium/content/', views.premium_tips, name='premium_tips_content'), 
    
    # NOVO FLUXO DE PAGAMENTO:
    
    # 1. Rota para a página de escolha de planos
    path('checkout/planos/', views.choose_plan, name='choose_plan'),
    
    # 2. Rota de Simulação de Pagamento
    #path('checkout/pagar/<int:plan_id>/', views.simulate_checkout_with_plan, name='simulate_checkout_with_plan'),
    
    # 3. Rota de Confirmação/Webhook
    path('checkout/confirmar/<str:username>/', views.confirm_payment, name='confirm_payment'),

    # Rota de Ação de Desativação (Admin)
    path('desativar-tip/<int:tip_id>/', views.deactivate_tip, name='deactivate_tip'),
    # Rota para a nova página de Jogos & Odds
    path("jogos-flashscore/", views.jogos_flashscore, name="jogos_flashscore"),
]
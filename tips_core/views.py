# tips_core/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction 
from django.contrib import messages
from datetime import datetime, timedelta 
import pytz 
from django.contrib.auth import get_user_model, update_session_auth_hash 
from .models import Tip, Noticia, Assinatura 
from .forms import CustomUserCreationForm 

# --- VIEWS DE CONTEÚDO ---

def public_tips_list(request):
    """
    Exibe a lista de tips gratuitas E as notícias na página principal.
    """
    free_tips = Tip.objects.filter(access_level='FREE').order_by('-match_date')
    noticias_recentes = Noticia.objects.all().order_by('-data_publicacao')[:6]
    
    context = {
        'tips': free_tips,
        'noticias': noticias_recentes,
        'title': 'Tips e Análises do Dia' 
    }
    return render(request, 'tips_core/tip_list.html', context)

def access_denied(request):
    """
    Página de acesso negado.
    """
    return render(request, 'tips_core/access_denied.html', {})


# --- VIEWS DE AUTENTICAÇÃO E PREMIUM ---

def register(request):
    """
    View para lidar com o registro de novos usuários.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('home')
    else:
        form = CustomUserCreationForm()
        
    return render(request, 'registration/register.html', {'form': form})


def go_to_premium(request):
    """
    Rota que o link 'Premium' no Navbar aponta. 
    Redireciona para o conteúdo (se Premium) ou para a página de escolha de planos.
    """
    if request.user.is_authenticated:
        # Se logado, checa o status Premium
        return redirect('premium_tips_content') 
    else:
        # Se não logado, redireciona para a página de login
        return redirect('login') 


@login_required
def premium_tips(request):
    """
    Página de tips premium. Acessível apenas para membros premium.
    """
    # FORÇA O RECARREGAMENTO DO OBJETO USUÁRIO DO BANCO DE DADOS
    try:
        user = request.user.__class__.objects.get(pk=request.user.pk)
    except Exception:
        user = request.user 
        
    # Verifica o status atual
    if not user.is_premium_member:
        messages.error(request, "Você precisa ser um membro Premium para acessar este conteúdo.")
        return redirect('access_denied')
        
    premium_tips = Tip.objects.filter(access_level='PREMIUM').order_by('-match_date')
    
    return render(request, 'tips_core/premium_tips.html', {
        'title': 'Tips Premium Exclusivas',
        'tips': premium_tips,
    })


def choose_plan(request):
    """
    Página que permite ao usuário escolher entre 3 planos de assinatura.
    """
    plans = [
        {'id': 1, 'name': 'Plano Mensal', 'duration': 1, 'price': 'R$ 50,00'},
        {'id': 3, 'name': 'Plano Trimestral', 'duration': 3, 'price': 'R$ 120,00'},
        {'id': 6, 'name': 'Plano Semestral', 'duration': 6, 'price': 'R$ 185,00'},
    ]
    
    context = {
        'title': 'Escolha seu Plano Premium',
        'plans': plans
    }
    return render(request, 'tips_core/choose_plan.html', context)


@login_required
def simulate_checkout_with_plan(request, plan_id):
    """
    NOVA FUNÇÃO: Recebe o ID do plano e redireciona o usuário para o PagSeguro/PagBank.
    """
    if request.method == 'GET':
        user = request.user
        
        # Simula a URL de pagamento REAL que receberia o plan_id
        PAGSEGURO_URL = f"https://pagseguro.uol.com.br/checkout?user={user.username}&plan={plan_id}"
        
        messages.info(request, f"Simulando redirecionamento para PagSeguro com Plano ID {plan_id}.")
        return redirect(PAGSEGURO_URL)

    return redirect('choose_plan')


def confirm_payment(request, username):
    """
    Simula o Webhook/Retorno do PagBank e ativa/desativa o Premium.
    """
    User = get_user_model()
    
    try:
        user = User.objects.get(username=username) 
    except User.DoesNotExist:
        messages.error(request, "Erro: Usuário não encontrado para ativar a assinatura.")
        return redirect('home')
        
    if user.is_premium_member:
        messages.info(request, "Sua assinatura já está ativa!")
        return redirect('premium_tips_content')

    try:
        with transaction.atomic():
            user.is_premium_member = True
            user.premium_expiration_date = datetime.now().date() + timedelta(days=30)
            user.save()
            
            update_session_auth_hash(request, user) 

            Assinatura.objects.update_or_create(user=user, defaults={'is_active': True})
            
        messages.success(request, f"Assinatura Premium ativada! Bem-vindo, {user.username}.")
        return redirect('premium_tips_content')

    except Exception as e:
        messages.error(request, f"Erro ao processar ativação: {e}")
        return redirect('home')
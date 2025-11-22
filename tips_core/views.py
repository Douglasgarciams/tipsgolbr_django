from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction 
from django.contrib import messages
from datetime import datetime, timedelta 
import pytz 
from django.contrib.auth import get_user_model, update_session_auth_hash 
# IMPORTAÇÕES ESSENCIAIS PARA O CÁLCULO DE ANÁLISE
from django.db.models import Sum, Count, F, Case, When, DecimalField 
from .models import Tip, Noticia, Assinatura, METHOD_CHOICES 
from .forms import CustomUserCreationForm 

# --- VIEWS DE CONTEÚDO ---

def public_tips_list(request):
    """
    Exibe a lista de tips gratuitas E as notícias na página principal.
    Filtra as tips para serem exibidas APENAS se o usuário estiver logado E a aposta estiver ATIVA.
    """
    free_tips = None # Inicia como None

    # Filtra as tips gratuitas APENAS se o usuário estiver autenticado
    if request.user.is_authenticated:
        free_tips = Tip.objects.filter(access_level='FREE', is_active=True).order_by('-match_date')
        
    # CORREÇÃO: Aumentado o limite de notícias de 6 para 12
    noticias_recentes = Noticia.objects.all().order_by('-data_publicacao')[:12]
    
    context = {
        'tips': free_tips,
        'noticias': noticias_recentes,
        'title': 'Tips e Análises do Dia' 
    }
    return render(request, 'tips_core/tip_list.html', context)


def deactivate_tip(request, tip_id):
    """
    Muda o status 'is_active' de uma aposta para False (oculta), 
    mantendo-a no banco de dados para o histórico de desempenho.
    """
    # É crucial que o método seja POST para segurança E que seja um superusuário.
    if request.method == 'POST' and request.user.is_superuser:
        try:
            # 1. Busca a aposta pelo ID (pk)
            tip = get_object_or_404(Tip, pk=tip_id)
            
            # 2. Desativa a aposta
            tip.is_active = False
            tip.save()
            messages.success(request, f"Aposta '{tip.match_title}' ocultada com sucesso (mantida no histórico).")
            
        except Exception as e:
            messages.error(request, f"Erro ao ocultar aposta: {e}")
            
    # Redireciona de volta para a página inicial (ou para onde for mais útil)
    return redirect('home')


def access_denied(request):
    """
    Página de acesso negado.
    """
    return render(request, 'tips_core/access_denied.html', {})


# --- VIEW DE ANÁLISE DE DESEMPENHO (Cálculo Corrigido) ---

@login_required
def analysis_dashboard(request):
    """
    Calcula e exibe o resumo de ganhos e perdas por Método de Aposta.
    """
    
    # 1. Filtra apenas as apostas CONCLUÍDAS (WIN, LOSS)
    concluded_tips = Tip.objects.filter(status__in=['WIN', 'LOSS'])
    
    # 2. Define o Lucro Líquido
    # CORREÇÃO APLICADA: SE WIN, usa F('valor_ganho') (o lucro líquido já registrado)
    net_profit_case = Case(
        When(status='WIN', then=F('valor_ganho')), # <-- CORREÇÃO AQUI
        When(status='LOSS', then=F('valor_perda') * -1), 
        default=0,
        output_field=DecimalField()
    )

    # 3. Agrupa as apostas por MÉTODO e calcula as métricas por grupo
    summary_data = concluded_tips.values('method').annotate(
        total_aposta=Sum('valor_aposta'),
        lucro_liquido_total=Sum(net_profit_case),
        total_apostas=Count('id'),
        total_wins=Count(Case(When(status='WIN', then=1))),
        total_losses=Count(Case(When(status='LOSS', then=1))),
    ).order_by('-lucro_liquido_total')

    # 4. CALCULA OS TOTAIS GLOBAIS DIRETAMENTE NO DATABASE
    global_totals = concluded_tips.aggregate(
        total_stakes=Sum('valor_aposta'),
        total_net_profit=Sum(net_profit_case)
    )

    # 5. Formata os dados para o template e adiciona o nome legível do método
    analysis_summary = []
    method_dict = dict(METHOD_CHOICES)
    
    for item in summary_data:
        # Garante que total_aposta não seja None ou zero antes de dividir
        total_aposta_decimal = item['total_aposta']
        lucro_liquido_total_decimal = item['lucro_liquido_total']
        
        if total_aposta_decimal and total_aposta_decimal != 0:
            yield_percent = (lucro_liquido_total_decimal / total_aposta_decimal) * 100
        else:
            yield_percent = 0.0

        analysis_summary.append({
            'method_code': item['method'],
            'method_name': method_dict.get(item['method'], 'Desconhecido'),
            'total_aposta': item['total_aposta'],
            'lucro_liquido_total': item['lucro_liquido_total'],
            'total_apostas': item['total_apostas'],
            'total_wins': item['total_wins'],
            'total_losses': item['total_losses'],
            'yield_percent': yield_percent
        })

    context = {
        'title': 'Dashboard de Análise de Desempenho',
        'summary': analysis_summary,
        'global_stakes': global_totals.get('total_stakes') or 0,
        'global_net_profit': global_totals.get('total_net_profit') or 0,
    }
    return render(request, 'tips_core/analysis_dashboard.html', context)


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
        
    # AQUI: Filtro adicionado para garantir que só tips ativas (is_active=True) sejam mostradas
    premium_tips = Tip.objects.filter(access_level='PREMIUM', is_active=True).order_by('-match_date')
    
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
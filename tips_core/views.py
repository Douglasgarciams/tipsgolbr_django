from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction 
from django.contrib import messages
from datetime import datetime, timedelta, date # Adicionado 'date'
import pytz 
from django.contrib.auth import get_user_model, update_session_auth_hash 
# IMPORTAÇÕES ESSENCIAIS PARA O CÁLCULO DE ANÁLISE
from django.db.models import Sum, Count, F, Case, When, DecimalField, Max, functions, Q # Adicionado Max e functions
from django.conf import settings 
from .models import Tip, Noticia, Assinatura, METHOD_CHOICES, PromocaoBanner, Team
from .forms import CustomUserCreationForm
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests 
import xml.etree.ElementTree as ET
from django.utils import timezone
import json # Necessário para serializar dados do gráfico
from .models import Team

# --- VIEWS DE CONTEÚDO ---

def jogos_flashscore(request):
    """
    Renderiza a página de jogos usando o widget Scores24 (Estilo FlashScore).
    """
    return render(request, 'analysis/jogos_flashscore.html')

def public_tips_list(request):
    """
    Exibe a lista de tips gratuitas, separando-as corretamente por data local.
    """
    noticias_recentes = None
    promo_banners = None

    # CORREÇÃO 1: Pega a data de HOJE baseada no fuso horário local (Brasil)
    # Isso evita que o jogo mude de bloco antes da meia-noite real.
    today = timezone.localtime(timezone.now()).date()
    
    tips_categorias = {
        'hoje': [],
        'proximos': [],
        'passados': [], # Passados com status PENDING
        'concluidos': [], # Passados com status WIN/LOSS/VOID
    }

    # 1. VISUALIZAÇÃO PÚBLICA (Usuário NÃO logado)
    if not request.user.is_authenticated:
        noticias_recentes = Noticia.objects.all().order_by('-data_publicacao')[:12]
        promo_banners = PromocaoBanner.objects.filter(ativo=True).order_by('ordem')
        
    # 2. VISUALIZAÇÃO DE MEMBRO (Usuário logado)
    else:
        # Filtra tips ativas e gratuitas
        all_free_tips = Tip.objects.filter(
            access_level='FREE', 
            is_active=True
        ).order_by('match_date')
        
        for tip in all_free_tips:
            # CORREÇÃO 2: Converte a data da Tip para o horário local antes de comparar
            tip_date = timezone.localtime(tip.match_date).date()
            
            # --- Regras de Classificação Corrigidas ---
            if tip_date == today:
                # Se a data for EXATAMENTE igual a hoje (ex: 05/01)
                tips_categorias['hoje'].append(tip)
                
            elif tip_date > today:
                # Se a data for no FUTURO (ex: 06/01 em diante)
                tips_categorias['proximos'].append(tip)
                
            else: 
                # Se a data for no PASSADO (ex: 04/01 para trás)
                if tip.status in ['WIN', 'LOSS', 'VOID']:
                    tips_categorias['concluidos'].append(tip)
                else:
                    tips_categorias['passados'].append(tip)

    context = {
        'tips_categorias': tips_categorias, 
        'noticias': noticias_recentes,
        'promo_banners': promo_banners,
        'title': 'Tips e Análises do Dia' 
    }
    return render(request, 'tips_core/tip_list.html', context)


def deactivate_tip(request, tip_id):
    """
    Muda o status 'is_active' de uma aposta para False (oculta).
    """
    if request.method == 'POST' and request.user.is_superuser:
        try:
            tip = get_object_or_404(Tip, pk=tip_id)
            tip.is_active = False
            tip.save()
            messages.success(request, f"Aposta '{tip.match_title}' ocultada com sucesso (mantida no histórico).")
        except Exception as e:
            messages.error(request, f"Erro ao ocultar aposta: {e}")
            
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
    Calcula e exibe o resumo de ganhos e perdas por Método de Aposta,
    incluindo dados históricos mensais para o gráfico de linha.
    """
    
    # 1. Filtra apenas as apostas CONCLUÍDAS (WIN, LOSS)
    concluded_tips = Tip.objects.filter(status__in=['WIN', 'LOSS'])
    
    # 2. Define o Lucro Líquido (USADO EM MÚLTIPLAS CONSULTAS)
    net_profit_case = Case(
        When(status='WIN', then=F('valor_ganho')), 
        When(status='LOSS', then=F('valor_perda') * -1), 
        default=0,
        output_field=DecimalField()
    )

    # --- CONSULTA 1: DETALHES POR MÉTODO (Tabela) ---
    summary_data = concluded_tips.values('method').annotate(
        total_aposta=Sum('valor_aposta'),
        lucro_liquido_total=Sum(net_profit_case),
        total_apostas=Count('id'),
        total_wins=Count(Case(When(status='WIN', then=1))),
        total_losses=Count(Case(When(status='LOSS', then=1))),
        # ADICIONADO: Data da última partida para a coluna da tabela
        match_date=Max('match_date'), 
    ).order_by('-lucro_liquido_total')

    # -----------------------------------------------------
    # --- CONSULTA 2: EVOLUÇÃO MENSAL (Gráfico de Linha) ---
    # -----------------------------------------------------
    # Agrupa por Ano e Mês para obter o lucro líquido por período.
    monthly_summary = concluded_tips.annotate(
        year=functions.ExtractYear('match_date'),
        month=functions.ExtractMonth('match_date')
    ).values('year', 'month').annotate(
        monthly_profit=Sum(net_profit_case)
    ).order_by('year', 'month')
    
    
    # -----------------------------------------------------
    # --- FORMATAÇÃO DOS DADOS MENSAIS PARA O CHART.JS ---
    # -----------------------------------------------------
    monthly_labels = []
    monthly_profits = []
    
    # Gera os nomes dos meses
    MONTH_NAMES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    
    # Calcula o lucro ACUMULADO (necessário para o gráfico de linha)
    cumulative_profit = 0
    
    for entry in monthly_summary:
        month_name = MONTH_NAMES[entry['month'] - 1] # -1 porque JS é 0-indexed
        label = f"{month_name}/{entry['year']}"
        
        # Lucro líquido do mês
        profit_of_month = entry['monthly_profit'] or 0 
        
        # Lucro ACUMULADO até o final daquele mês
        cumulative_profit += profit_of_month
        
        monthly_labels.append(label)
        monthly_profits.append(float(cumulative_profit)) # O JS precisa de float

    # Dicionário final que será serializado para o JavaScript
    monthly_data_for_chart = {
        'labels': monthly_labels,
        'data': monthly_profits
    }
    
    # -----------------------------------------------------
    # --- FORMATAÇÃO FINAL PARA O CONTEXTO ---
    # -----------------------------------------------------

    global_totals = concluded_tips.aggregate(
        total_stakes=Sum('valor_aposta'),
        total_net_profit=Sum(net_profit_case)
    )

    analysis_summary = []
    method_dict = dict(METHOD_CHOICES)

    for item in summary_data:
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
            'yield_percent': yield_percent,
            # Passa a data corrigida para o template
            'match_date': item['match_date'], 
        })

    context = {
        'title': 'Dashboard de Análise de Desempenho',
        'summary': analysis_summary,
        'global_stakes': global_totals.get('total_stakes') or 0,
        'global_net_profit': global_totals.get('total_net_profit') or 0,
        # NOVO: Dados mensais reais para o Gráfico de Linha
        'monthly_data_json': json.dumps(monthly_data_for_chart),
    }
    return render(request, 'tips_core/analysis_dashboard.html', context)


# --- VIEW DA CALCULADORA (NOVA) ---
def calculator_page(request):
    """Renderiza a página da Calculadora Dutching."""
    return render(request, 'tips_core/dutching_calculator.html', {
        'title': 'Calculadora Dutching',
    })


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
    AGORA: Adiciona as URLs do PagSeguro do settings.py.
    """
    plans = [
        {'id': 1, 'name': 'Plano Mensal', 'duration': 1, 'price': 'R$ 50,00'},
        {'id': 3, 'name': 'Plano Trimestral', 'duration': 3, 'price': 'R$ 120,00'},
        {'id': 6, 'name': 'Plano Semestral', 'duration': 6, 'price': 'R$ 185,00'},
    ]
    
    # PASSO CHAVE: Acessa o dicionário de URLs do PagSeguro
    pagseguro_urls = settings.PAGSEGURO_PLAN_URLS 
    
    # Itera sobre os planos e adiciona a URL correspondente
    for plan in plans:
        # Usa o 'id' do plano (1, 3, ou 6) para buscar a URL correta
        # Adiciona a URL do PagSeguro como uma nova chave no dicionário do plano
        plan['pagseguro_url'] = pagseguro_urls.get(plan['id'])
        
    context = {
        'title': 'Escolha seu Plano Premium',
        'plans': plans
    }
    return render(request, 'tips_core/choose_plan.html', context)


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
    
    # ----------------------------------------------------------------
# --- NOVAS VIEWS: ABA DE DADOS DOS TIMES (ENCICLOPÉDIA) ---
# ----------------------------------------------------------------

@login_required
def lista_times(request):
    # 1. Captura o que o usuário digitou no campo de busca (name="search")
    search_query = request.GET.get('search')
    
    # 2. Se houver algo digitado, filtra. Se não, pega tudo.
    if search_query:
        times = Team.objects.filter(name__icontains=search_query).order_by('name')
        print(f"--- DEBUG: BUSCA POR '{search_query}' RETORNOU {times.count()} TIMES ---")
    else:
        times = Team.objects.all().order_by('name')
        print(f"--- DEBUG: O DJANGO ESTÁ LENDO {times.count()} TIMES (LISTA COMPLETA) ---")
    
    return render(request, 'tips_core/lista_times.html', {'times': times})

@login_required
def detalhes_time(request, team_id):
    """Calcula estatísticas de um time capturando todos os tipos de resultados."""
    time = get_object_or_404(Team, pk=team_id)
    
    # BUSCA AMPLIADA: Pega todos os jogos onde o time participou (Mandante ou Visitante)
    # Removemos a exigência estrita de score_home__isnull para capturar mais dados
    jogos = Tip.objects.filter(
        Q(home_team=time) | Q(away_team=time)
    ).order_by('-match_date')

    vitorias = 0
    derrotas = 0
    empates = 0
    gols_pro = 0
    gols_contra = 0

    for jogo in jogos:
        # Só processamos o cálculo se houver números nos campos de gols
        if jogo.score_home is not None and jogo.score_away is not None:
            if jogo.home_team == time:
                gols_pro += jogo.score_home
                gols_contra += jogo.score_away
                if jogo.score_home > jogo.score_away: vitorias += 1
                elif jogo.score_home < jogo.score_away: derrotas += 1
                else: empates += 1
            else: # Time era visitante
                gols_pro += jogo.score_away
                gols_contra += jogo.score_home
                if jogo.score_away > jogo.score_home: vitorias += 1
                elif jogo.score_away < jogo.score_home: derrotas += 1
                else: empates += 1

    context = {
        'time': time,
        'jogos': jogos,
        'title': f'Estatísticas: {time.name}',
        'stats': {
            'vitorias': vitorias,
            'derrotas': derrotas,
            'empates': empates,
            'gols_pro': gols_pro,
            'gols_contra': gols_contra,
            'saldo': gols_pro - gols_contra,
            'total': jogos.count()
        }
    }
    return render(request, 'tips_core/detalhes_time.html', context)
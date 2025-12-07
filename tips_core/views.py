from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction 
from django.contrib import messages
from datetime import datetime, timedelta, date # Adicionado 'date'
import pytz 
from django.contrib.auth import get_user_model, update_session_auth_hash 
# IMPORTAÇÕES ESSENCIAIS PARA O CÁLCULO DE ANÁLISE
from django.db.models import Sum, Count, F, Case, When, DecimalField, Max, functions # Adicionado Max e functions
from django.conf import settings 
from .models import Tip, Noticia, Assinatura, METHOD_CHOICES, PromocaoBanner
from .forms import CustomUserCreationForm
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests 
import xml.etree.ElementTree as ET
from django.utils import timezone
from google import genai
from google.genai.errors import APIError
import json # Necessário para serializar dados do gráfico

# ----------------------------------------------------------------------
# 🌟 INICIALIZAÇÃO DA API DO GEMINI (COM TRATAMENTO DE ERRO) 🌟
# ----------------------------------------------------------------------
try:
    # A biblioteca genai.Client() buscará a chave na variável de ambiente GEMINI_API_KEY
    client = genai.Client()
    print("Gemini Client inicializado com sucesso.")
except Exception as e:
    # Este bloco captura a falha se a chave não for encontrada ou for inválida
    print(f"ERRO CRÍTICO: Falha ao inicializar o Gemini Client. Verifique a variável de ambiente GEMINI_API_KEY. Detalhe: {e}")
    client = None # Define como None para que a view trate o erro 503

# --- VIEWS DE CONTEÚDO ---

def jogos_flashscore(request):
    """
    Renderiza a página de jogos usando o widget Scores24 (Estilo FlashScore).
    """
    return render(request, 'analysis/jogos_flashscore.html')

def dynamic_matchup_view(request):
    """
    Renderiza a página para GET e processa a análise da IA para POST (AJAX).
    """
    # 2. Requisição POST: Processa a solicitação de análise via Gemini API
    if request.method == 'POST':
        
        # 🛑 CORREÇÃO: DEFINE A DATA LOGO NO INÍCIO DO POST 🛑
        from datetime import date # Garante que 'date' está acessível no POST
        data_hoje = date.today().strftime("%d de %B de %Y")
        
        # Verifica se o cliente Gemini foi inicializado com sucesso
        if not client:
            return JsonResponse({'status': 'error', 'message': 'O serviço de IA não está configurado. Verifique a chave GEMINI_API_KEY.'}, status=503)

        try:
            # Obter dados enviados via AJAX
            data = json.loads(request.body)
            #time1 = data.get('time1')
            #time2 = data.get('time2')
            pedido = data.get('pedido')
            
            # 🛑 NOVO CÓDIGO DO prompt_base (Versão Flexível) 🛑
            prompt_base = f"""
            Você é um AGENTE DE NOTÍCIAS ESPORTIVAS E ANÁLISE DE DESEMPENHO. A data atual é {data_hoje}.
            Seu foco principal é analisar o elenco, desfalques e a situação mais atual, além do desempenho da temporada 2025.
            O pedido do usuário é sobre: "{pedido}".

            **INSTRUÇÕES CRÍTICAS:**
            1. **IDENTIFICAÇÃO:** Primeiro, identifique os dois times envolvidos no confronto mencionados no pedido. Use esses times para todas as buscas.
            2. **USE A DATA ATUAL ({data_hoje})** como contexto para a pesquisa.
            3. **USE A BUSCA NA WEB** para encontrar os desfalques e a situação **MAIS RECENTE (máximo de 1 dia antes)** para os times identificados.
            4. **Desfalques:** Pesquise e liste os desfalques (Lesionados e Suspensos) para **SEUS PRÓXIMOS EVENTOS/JOGOS** ou a situação médica atual.
            5. **Desempenho de 2025:** Pesquise e inclua o desempenho recente (últimos 5 jogos, posição na tabela, etc.) dos times, **focando exclusivamente nos dados da temporada de 2025.**
            6. **Estrutura de Resposta:**
                * Comece a resposta dizendo explicitamente: 'Análise baseada em dados de {data_hoje} e desempenho da temporada 2025.'
                * Use **negrito** e listas Markdown. Não use introduções longas.

            **ESTRUTURA DESEJADA (Aplicar a estrutura abaixo para CADA UM dos times identificados no pedido):**
            - **Análise de Desempenho e Situação Atual do [Nome do Time 1] (Temporada 2025)**
                - Desempenho Recente (2025)
                - Situação do Elenco e Notícias Atuais
            - **Desfalques Atuais do [Nome do Time 1]** (Lesionados e Suspensos)

            - **Análise de Desempenho e Situação Atual do [Nome do Time 2] (Temporada 2025)**
                - Desempenho Recente (2025)
                - Situação do Elenco e Notícias Atuais
            - **Desfalques Atuais do [Nome do Time 2]** (Lesionados e Suspensos)
            """

            # --- CHAMADA À API DO GEMINI ---
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt_base
            )

            # Retorna a resposta da IA como JSON para o JavaScript
            return JsonResponse({'status': 'success', 'analysis_text': response.text})

        except APIError as e:
            # Capturar erros da API (ex: cota excedida)
            return JsonResponse({'status': 'error', 'message': f'Erro de API com o Gemini: {e}'}, status=500)
        except json.JSONDecodeError:
            # Capturar erro se o JSON do frontend for inválido
            return JsonResponse({'status': 'error', 'message': 'Requisição JSON inválida.'}, status=400)
        except Exception as e:
            # Capturar outros erros
            return JsonResponse({'status': 'error', 'message': f'Erro interno inesperado: {e}'}, status=400)

    # 1. Requisição GET: Apenas renderiza o formulário
    else: 
        context = {
            'title': 'Análise de Confronto Dinâmica',
        }
        return render(request, 'analysis/confronto_dinamico.html', context)

def public_tips_list(request):
    """
    Exibe a lista de tips gratuitas, separando-as por Jogos de Hoje, Próximos e Passados.
    """
    noticias_recentes = None
    promo_banners = None

    # Define a data de HOJE (apenas a data, desconsiderando a hora)
    today = timezone.now().date()
    
    # Dicionários vazios para as categorias de tips
    tips_categorias = {
        'hoje': [],
        'proximos': [],
        'passados': [], # Passados com status PENDING/SEM RESULTADO
        'concluidos': [], # Passados com status WIN/LOSS/VOID
    }

    # 1. VISUALIZAÇÃO PÚBLICA (Usuário NÃO logado)
    if not request.user.is_authenticated:
        noticias_recentes = Noticia.objects.all().order_by('-data_publicacao')[:12]
        promo_banners = PromocaoBanner.objects.filter(ativo=True).order_by('ordem')
        
    # 2. VISUALIZAÇÃO DE MEMBRO (Usuário logado)
    else:
        # Filtra todas as tips gratuitas (consideramos todas se o usuário estiver logado)
        all_free_tips = Tip.objects.filter(access_level='FREE').order_by('match_date')
        
        for tip in all_free_tips:
            tip_date = tip.match_date.date()
            
            # --- Regras de Classificação ---
            if tip_date == today:
                # Jogo é hoje
                tips_categorias['hoje'].append(tip)
            elif tip_date > today:
                # Jogo no futuro
                tips_categorias['proximos'].append(tip)
            else: # tip_date < today (Passado)
                # Jogo no passado
                if tip.status in ['WIN', 'LOSS', 'VOID']:
                    # Aposta concluída (com resultado)
                    tips_categorias['concluidos'].append(tip)
                else:
                    # Aposta passada, mas o resultado ainda está como Pendente (PENDING)
                    tips_categorias['passados'].append(tip)


    context = {
        # Passa o dicionário de categorias completo para o template
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
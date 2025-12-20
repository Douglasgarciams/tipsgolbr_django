from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from datetime import datetime, timedelta
import pytz
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.db.models import Sum, Count, F, Case, When, DecimalField
from django.conf import settings  # Importar settings
from .models import Tip, Noticia, Assinatura, METHOD_CHOICES, PromocaoBanner
from .forms import CustomUserCreationForm
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
# Adicionado para o Webhook
import requests 
import xml.etree.ElementTree as ET

# --- VIEWS DE CONTEÚDO ---

def public_tips_list(request):
    free_tips = None
    noticias_recentes = None
    promo_banners = None

    if not request.user.is_authenticated:
        noticias_recentes = Noticia.objects.all().order_by('-data_publicacao')[:12]
        promo_banners = PromocaoBanner.objects.filter(ativo=True).order_by('ordem')
    else:
        free_tips = Tip.objects.filter(access_level='FREE', is_active=True).order_by('-match_date')

    context = {
        'tips': free_tips,
        'noticias': noticias_recentes,
        'promo_banners': promo_banners,
        'title': 'Tips e Análises do Dia'
    }
    return render(request, 'tips_core/tip_list.html', context)


def deactivate_tip(request, tip_id):
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
    return render(request, 'tips_core/access_denied.html', {})


# --- VIEW DE ANÁLISE DE DESEMPENHO ---

@login_required
def analysis_dashboard(request):
    # Lógica de análise de desempenho (mantida como estava)
    concluded_tips = Tip.objects.filter(status__in=['WIN', 'LOSS'])

    net_profit_case = Case(
        When(status='WIN', then=F('valor_ganho')),
        When(status='LOSS', then=F('valor_perda') * -1),
        default=0,
        output_field=DecimalField()
    )

    summary_data = concluded_tips.values('method').annotate(
        total_aposta=Sum('valor_aposta'),
        lucro_liquido_total=Sum(net_profit_case),
        total_apostas=Count('id'),
        total_wins=Count(Case(When(status='WIN', then=1))),
        total_losses=Count(Case(When(status='LOSS', then=1))),
    ).order_by('-lucro_liquido_total')

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
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('home')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})


def go_to_premium(request):
    if request.user.is_authenticated:
        return redirect('premium_tips_content')
    else:
        return redirect('login')


@login_required
def premium_tips(request):
    """
    Página de tips premium. Força a correção do status pela data (via save())
    antes de conceder o acesso.
    """
    
    user = request.user 
    
    # 🌟 PASSO CHAVE: Forçar o save() para ativar a lógica de correção
    # implementada no CustomUser.save() (que compara a data e ajusta o is_premium_member).
    try:
        user.save() 
    except Exception as e:
        # Lidar com exceções se houver problemas ao salvar
        print(f"Erro ao salvar usuário para correção de status: {e}")
        # Opcional: registrar o erro
        
    # 3. VERIFICAÇÃO FINAL DE ACESSO
    # Agora, basta checar o campo is_premium_member (que foi corrigido pelo user.save())
    if not user.is_premium_member: 
        # Garante que a mensagem de bloqueio seja mostrada
        if not messages.get_messages(request): 
             messages.error(request, "Sua assinatura Premium expirou. Você precisa ser um membro Premium para acessar este conteúdo.")
        return redirect('access_denied')
        
    # 4. EXIBE CONTEÚDO PREMIUM SE TUDO ESTIVER OK
    premium_tips = Tip.objects.filter(access_level='PREMIUM', is_active=True).order_by('-match_date')
    
    return render(request, 'tips_core/premium_tips.html', {
        'title': 'Tips Premium Exclusivas',
        'tips': premium_tips,
    })


def choose_plan(request):
    """
    Página que permite ao usuário escolher entre 3 planos de assinatura.
    AGORA: Adiciona as URLs do PagSeguro (do settings.py) a cada plano.
    """
    plans = [
        {'id': 1, 'name': 'Plano Mensal', 'duration': 1, 'price': 'R$ 50,00'},
        {'id': 3, 'name': 'Plano Trimestral', 'duration': 3, 'price': 'R$ 120,00'},
        {'id': 6, 'name': 'Plano Semestral', 'duration': 6, 'price': 'R$ 185,00'},
    ]

    # PASSO CHAVE: Acessa o dicionário de URLs do PagSeguro
    pagseguro_urls = settings.PAGSEGURO_PLAN_URLS 

    # Anexa a URL do PagSeguro correta para cada plano
    for plan in plans:
        plan['pagseguro_url'] = pagseguro_urls.get(plan['id'])

    context = {
        'title': 'Escolha seu Plano Premium',
        'plans': plans
    }
    return render(request, 'tips_core/choose_plan.html', context)


# ----------------------------------------------------------------------
#   🔵 PAGSEGURO WEBHOOK (Notificação de Transação) 🔥 IMPLEMENTADO AQUI
# ----------------------------------------------------------------------
@csrf_exempt
def pagseguro_notification_view(request):
    """
    Recebe a requisição POST do PagSeguro com o código de notificação e processa.
    """
    if request.method != 'POST':
        # Deve retornar 405 se não for POST
        return HttpResponse('Apenas requisições POST são permitidas.', status=405)

    notification_code = request.POST.get('notificationCode')
    notification_type = request.POST.get('notificationType')

    # Apenas processa se for uma notificação de transação válida
    if not notification_code or notification_type != 'transaction':
        return HttpResponse('Notificação Inválida', status=400)

    try:
        # 1. Monta a URL para consultar os detalhes da transação
        url = f"{settings.PAGSEGURO_NOTIFICATION_URL}{notification_code}"
        params = {
            # Usando as credenciais do seu settings.py
            'email': settings.PAGSEGURO_SELLER_EMAIL, 
            'token': settings.PAGSEGURO_TOKEN,
        }
        
        # 2. Faz a chamada GET para a API do PagSeguro/PagBank
        response = requests.get(url, params=params)
        response.raise_for_status() # Levanta exceção para erros HTTP 4xx/5xx
        
        # 3. Processa a Resposta XML
        root = ET.fromstring(response.content)
        
        status_code = root.find('status').text # Ex: '3' = Paga
        transaction_reference = root.find('reference').text # Deve conter o ID/Username do usuário

        # --- LÓGICA DE ATUALIZAÇÃO DA ASSINATURA ---
        username_from_ref = transaction_reference 
        User = get_user_model()
        
        # Verifica se o pagamento foi aprovado (Status 3 ou 4)
        if status_code in ['3', '4']: 
            try:
                # É crucial que o 'transaction_reference' seja o username/ID correto
                user = User.objects.get(username=username_from_ref) 
                
                # Exemplo de lógica de ativação (Ajuste a duração real do plano)
                # NOTA: Você precisaria de lógica adicional para mapear o plano exato (1, 3, 6 meses)
                # se a referência não contiver essa informação.
                
                # Por simplicidade, ativa por 30 dias (se for o plano mensal)
                if not user.is_premium_member or user.premium_expiration_date < datetime.now().date():
                     # Se não é premium ou a assinatura expirou, define a data de expiração a partir de hoje
                     expiration_date = datetime.now().date() + timedelta(days=30)
                else:
                     # Se já é premium, estende a data a partir da data de expiração atual
                     expiration_date = user.premium_expiration_date + timedelta(days=30)
                     
                user.is_premium_member = True
                user.premium_expiration_date = expiration_date
                user.save()
                
                Assinatura.objects.update_or_create(user=user, defaults={'is_active': True})
                print(f"Assinatura do usuário {user.username} ATIVADA/ESTENDIDA. Expira em {expiration_date}")
                
            except User.DoesNotExist:
                 print(f"ERRO: Usuário {username_from_ref} não encontrado via referência.")
                 pass
        
        # Se o status for '7' (Cancelada/Devolvida), você deveria desativar a assinatura.
        elif status_code == '7':
             try:
                 user = User.objects.get(username=username_from_ref) 
                 user.is_premium_member = False
                 user.save()
                 Assinatura.objects.update_or_create(user=user, defaults={'is_active': False})
                 print(f"Assinatura do usuário {user.username} CANCELADA.")
             except User.DoesNotExist:
                 pass
                 
        # O PagSeguro/PagBank espera um HTTP 200 para não reenviar
        return HttpResponse('OK', status=200) 

    except requests.exceptions.HTTPError as e:
        # Logar erro de comunicação com a API do PagSeguro
        print(f"Erro HTTP na consulta ao PagSeguro: {e}. Conteúdo: {response.content}")
        return HttpResponse('Erro ao consultar PagSeguro', status=500)
    except Exception as e:
        # Logar erro geral
        print(f"Erro inesperado no Webhook: {e}")
        return HttpResponse('Erro Interno', status=500)


# ----------------------------
#   🔵 Ativação manual (simulada)
# ----------------------------
def confirm_payment(request, username):
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


# -------------------------------------------------
#   ✅ VIEW EXTRA QUE VOCÊ PEDIU PARA ADICIONAR
# -------------------------------------------------
def calculator_page(request):
    """Renderiza a página da Calculadora Dutching."""
    return render(request, 'tips_core/dutching_calculator.html', {
        'title': 'Calculadora Dutching',
    })
# A função analysis_dashboard já existe acima, não precisa duplicar.
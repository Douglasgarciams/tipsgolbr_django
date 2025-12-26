from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
# Adicionado Team e Assinatura à importação para garantir que tudo funcione
from .models import CustomUser, Tip, Noticia, PromocaoBanner, Team, Assinatura 

# --- 1. Configuração Customizada para o Modelo de Usuário ---
class CustomUserAdmin(UserAdmin):
    # Campos que você quer que apareçam no formulário de edição de usuário
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Premium', {'fields': ('is_premium_member', 'premium_expiration_date',)}),
    )
    # Campos que você quer que apareçam na lista de usuários
    list_display = UserAdmin.list_display + ('is_premium_member',)
    
    # CORREÇÃO: Alterado 'superuser' para 'is_superuser'
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_premium_member',)

# Registra o seu modelo CustomUser com a configuração CustomUserAdmin
admin.site.register(CustomUser, CustomUserAdmin)

# --- NOVO: Registro do Modelo de Times (Cadastro Profissional) ---
@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'logo')
    search_fields = ('name',)


# --- 2. Registro do Modelo de Dica (Tip) ---
@admin.register(Tip)
class TipAdmin(admin.ModelAdmin):
    # ATUALIZADO: Placar inserido entre os nomes dos times para facilitar a leitura
    list_display = (
        'home_team', 
        'score_home', 
        'score_away', 
        'away_team', 
        'league', 
        'method', 
        'status', 
        'is_active', 
        'match_date'
    )

    search_fields = ('home_team__name', 'away_team__name', 'observation')
    
    # Filtros que aparecerão na barra lateral direita
    list_filter = ('access_level', 'status', 'league', 'is_active', 'method')
    
    # Campos que podem ser pesquisados (agora busca pelo nome do time)
    search_fields = ('home_team__name', 'away_team__name', 'method')
    
    # PERMITE EDITAR O PLACAR E O STATUS DIRETO NA LISTA (Muito útil para estatísticas)
    list_editable = ('score_home', 'score_away', 'status', 'is_active')


# --- 3. Registro do Modelo de Notícia ---
@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    # Campos que serão exibidos na lista de Notícias
    list_display = ('titulo', 'fonte_url', 'data_publicacao', 'data_extracao', 'imagem_url')
    # Filtros que aparecerão na barra lateral direita
    list_filter = ('data_extracao', 'data_publicacao')
    # Campos que podem ser pesquisados
    search_fields = ('titulo', 'resumo')


# --- 4. NOVO: Registro do Modelo de Promoção/Banner ---
@admin.register(PromocaoBanner)
class PromocaoBannerAdmin(admin.ModelAdmin):
    # Campos que serão exibidos na lista de Banners
    list_display = ('titulo', 'link_url', 'ativo', 'ordem', 'data_criacao')
    # Filtros que aparecerão na barra lateral direita
    list_filter = ('ativo', 'data_criacao')
    # Campos que podem ser pesquisados
    search_fields = ('titulo', 'descricao')
    # Campos que podem ser editados diretamente na lista
    list_editable = ('ativo', 'ordem')

# --- 5. Registro do Modelo de Assinatura ---
admin.site.register(Assinatura)
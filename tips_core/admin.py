from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
# Importa o novo modelo PromocaoBanner. Assinatura removida da importação para evitar confusão.
from .models import CustomUser, Tip, Noticia, PromocaoBanner 

# --- 1. Configuração Customizada para o Modelo de Usuário ---
class CustomUserAdmin(UserAdmin):
    # Campos que você quer que apareçam no formulário de edição de usuário
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Premium', {'fields': ('is_premium_member', 'premium_expiration_date',)}),
    )
    # Campos que você quer que apareçam na lista de usuários
    list_display = UserAdmin.list_display + ('is_premium_member',)
    
    # É necessário redefinir estes campos para o Admin funcionar corretamente com CustomUser
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_premium_member',)

# Registra o seu modelo CustomUser com a configuração CustomUserAdmin
admin.site.register(CustomUser, CustomUserAdmin)

# --- 2. Registro do Modelo de Dica (Tip) ---
@admin.register(Tip)
class TipAdmin(admin.ModelAdmin):
    # Os campos 'method' e 'is_active' foram adicionados na lista de exibição
    list_display = ('match_title', 'league', 'method', 'odd_value', 'access_level', 'status', 'is_active', 'match_date', 'link_aposta')
    # Filtros que aparecerão na barra lateral direita
    list_filter = ('access_level', 'status', 'league', 'is_active', 'method')
    # Campos que podem ser pesquisados
    search_fields = ('match_title', 'method')
    # Campos que podem ser editados diretamente na lista
    list_editable = ('is_active', 'status', 'access_level')


# --- 3. Registro do Modelo de Notícia ---
@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    # Campos que serão exibidos na lista de Notícias
    list_display = ('titulo', 'fonte_url', 'data_publicacao', 'data_extracao', 'imagem_url')
    # Filtros que aparecerão na barra lateral direita
    list_filter = ('data_extracao', 'data_publicacao')
    # Campos que podem ser pesquisados
    search_fields = ('titulo', 'resumo')


# >>>>> SEÇÃO 4 (Assinatura) REMOVIDA PARA CENTRALIZAR O CONTROLE NO CustomUser <<<<<


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
# tips_core/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Tip, Noticia, Assinatura # <-- NOVO: Importa Noticia e Assinatura

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
    # Campos que serão exibidos na lista de Tips
    list_display = ('match_title', 'league', 'odd_value', 'access_level', 'status', 'match_date', 'link_aposta')
    # Filtros que aparecerão na barra lateral direita
    list_filter = ('access_level', 'status', 'league')
    # Campos que podem ser pesquisados
    search_fields = ('match_title', 'prediction')

# --- 3. Registro do Modelo de Notícia ---
@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    # Campos que serão exibidos na lista de Notícias
    list_display = ('titulo', 'fonte_url', 'data_publicacao', 'data_extracao', 'imagem_url')
    # Filtros que aparecerão na barra lateral direita
    list_filter = ('data_extracao', 'data_publicacao')
    # Campos que podem ser pesquisados
    search_fields = ('titulo', 'resumo')

# --- 4. Registro do Modelo de Assinatura ---
@admin.register(Assinatura)
class AssinaturaAdmin(admin.ModelAdmin):
    # Campos que serão exibidos na lista de Assinaturas
    list_display = ('user', 'is_active', 'start_date')
    # Filtros que aparecerão na barra lateral direita
    list_filter = ('is_active', 'start_date')
    # Campos que podem ser pesquisados
    search_fields = ('user__username',) # Permite pesquisar pelo nome de usuário
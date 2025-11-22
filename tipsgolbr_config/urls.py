# tipsgolbr_config/urls.py (Versão Corrigida - SEM CARACTERES ESPECIAIS)

from django.contrib import admin
from django.urls import path, include
from django.conf import settings # Importa settings
from django.conf.urls.static import static # Importa static helper
# Não é necessário importar settings de novo

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')), 
    path('', include('tips_core.urls')), 
]

# --- CONFIGURAÇÃO DE ARQUIVOS ESTÁTICOS E MÍDIA (SOMENTE EM DEBUG=True) ---
if settings.DEBUG:
    # Adiciona a rota para servir arquivos estáticos (CSS, JS, etc.)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 
    
    # ADICIONA ROTA PARA SERVIR ARQUIVOS DE MÍDIA (Imagens do Carrossel)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
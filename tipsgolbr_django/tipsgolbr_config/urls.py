# tipsgolbr_config/urls.py (Versão Corrigida - COM CONFIGURAÇÃO DE ESTÁTICOS)

from django.contrib import admin
from django.urls import path, include
from django.conf import settings      # Importa settings
from django.conf.urls.static import static # Importa static helper
from django.conf import settings # Pode ser redundante, mas é seguro ter certeza

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')), 
    path('', include('tips_core.urls')), 
]

# --- CONFIGURAÇÃO DE ARQUIVOS ESTÁTICOS (SOMENTE EM DEBUG=True) ---
if settings.DEBUG:
    # Adiciona a rota para servir arquivos estáticos (CSS, JS, Imagens)
    # A variável BASE_DIR precisa ser importada/definida no settings.py
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 
    
    # Nota: Não é necessário mais nada aqui.
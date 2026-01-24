import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tipsgolbr_config.settings')
django.setup()

from tips_core.models import Team

# ISSO VAI MOSTRAR ONDE O BANCO ESTÁ ESCONDIDO
print(f"--- CAMINHO DO BANCO QUE O DJANGO ESTÁ USANDO: ---")
print(settings.DATABASES['default']['NAME'])
print("-" * 50)
print(f"Total de Times lidos: {Team.objects.count()}")
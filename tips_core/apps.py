# tips_core/apps.py

from django.apps import AppConfig


class TipsCoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tips_core'

    # ADICIONADO: Método para carregar os signals
    def ready(self):
        # Importa os signals.py (ou neste caso, o models.py, onde o signal está conectado)
        import tips_core.models # Garante que o signal seja carregado
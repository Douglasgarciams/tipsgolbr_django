from django.apps import AppConfig

class TipsCoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tips_core'

    # ADICIONADO: Método para carregar os signals
    def ready(self):
        # Garante que o signals.py seja carregado
        import tips_core.signals

from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from tips_core.models import Noticia 
from tips_core.tasks import extrair_noticias_rss # IMPORTAÇÃO CHAVE

class Command(BaseCommand):
    help = 'Extrai notícias de fontes externas e limpa notícias muito antigas.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Iniciando a extração de notícias e limpeza de dados antigos...'))

        # 1. DELETA NOTÍCIAS COM MAIS DE 7 DIAS
        seven_days_ago = timezone.now() - timedelta(days=7)
        deleted_count, _ = Noticia.objects.filter(data_publicacao__lt=seven_days_ago).delete()
        self.stdout.write(self.style.SUCCESS(f'Limpeza concluída. {deleted_count} notícias antigas removidas.'))

        # 2. LÓGICA DE EXTRAÇÃO REAL
        summary_message = extrair_noticias_rss()

        self.stdout.write(self.style.SUCCESS(summary_message))
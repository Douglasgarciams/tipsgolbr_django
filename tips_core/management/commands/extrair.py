from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from tips_core.models import Noticia 

class Command(BaseCommand):
    help = 'Extrai notícias de fontes externas e limpa notícias muito antigas.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Iniciando a extração de notícias e limpeza de dados antigos...'))

        # 1. DELETA NOTÍCIAS COM MAIS DE 7 DIAS
        seven_days_ago = timezone.now() - timedelta(days=7)
        deleted_count, _ = Noticia.objects.filter(data_publicacao__lt=seven_days_ago).delete()
        self.stdout.write(self.style.SUCCESS(f'Limpeza concluída. {deleted_count} notícias antigas removidas.'))

        # 2. LOGICA DE EXTRAÇÃO EXISTENTE
        # ... Seu código para extrair e salvar as 90 notícias aqui ...

        self.stdout.write(self.style.SUCCESS('Extração concluída.'))
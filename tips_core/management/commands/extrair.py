from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from tips_core.models import Noticia # Assumindo que seu modelo é este

class Command(BaseCommand):
    help = 'Extrai notícias de fontes externas e limpa notícias muito antigas.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Iniciando a extração de notícias e limpeza de dados antigos...'))

        # 1. DEFININDO O LIMITE DE TEMPO
        # Deleta notícias com mais de 7 dias de idade
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        # 2. EXECUTANDO A LIMPEZA
        deleted_count, _ = Noticia.objects.filter(data_publicacao__lt=seven_days_ago).delete()
        self.stdout.write(self.style.SUCCESS(f'Limpeza concluída. {deleted_count} notícias antigas removidas.'))

        # 3. LÓGICA DE EXTRAÇÃO EXISTENTE (substitua pelo seu código)
        # ------------------------------------------------------------------
        # Exemplo da sua lógica de extração (manter a sua existente):
        # for item in dados_extraidos:
        #     Noticia.objects.update_or_create(
        #         titulo=item['titulo'],
        #         defaults={
        #             'conteudo': item['conteudo'],
        #             'data_publicacao': item['data_publicacao'],
        #             # ... outros campos ...
        #         }
        #     )
        # ------------------------------------------------------------------
        
        # Simulação para demonstrar a continuação:
        # ------------------------------------------------------------------
        # ... Seu código para extrair e salvar as 90 notícias aqui ...
        # ------------------------------------------------------------------

        # Mensagem final (manter)
        self.stdout.write(self.style.SUCCESS('Extração concluída.'))
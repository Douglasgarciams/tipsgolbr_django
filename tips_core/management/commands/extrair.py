from django.core.management.base import BaseCommand
from tips_core.tasks import extrair_noticias_rss # Importa a função do seu tasks.py

class Command(BaseCommand):
    help = 'Executa a função de extração de notícias de feeds RSS externos.'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando a extração de notícias...")
        
        # Chama a função que já está pronta no tasks.py
        resultado = extrair_noticias_rss()
        
        # Exibe o resultado da função
        self.stdout.write(self.style.SUCCESS(resultado))
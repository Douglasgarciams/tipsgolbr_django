import os
import django
import json

# Configura o ambiente com a pasta correta que vi na sua imagem
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tipsgolbr_config.settings')
django.setup()

from tips_core.models import Tip, Team, PromocaoBanner

def importar():
    # Carrega o arquivo JSON
    try:
        with open('dados_reais.json', 'r', encoding='utf-8') as f:
            dados = json.load(f)
    except Exception as e:
        print(f"Erro ao abrir o arquivo: {e}")
        return

    print(f"Iniciando processamento de {len(dados)} registros...")

    for item in dados:
        pk = item['pk']
        fields = item['fields']

        if item['model'] == 'tips_core.tip':
            # AGORA USANDO 'name' QUE É O CAMPO REAL DO SEU MODELO
            home, _ = Team.objects.get_or_create(
                id=fields['home_team'], 
                defaults={'name': f"Time {fields['home_team']}"}
            )
            away, _ = Team.objects.get_or_create(
                id=fields['away_team'], 
                defaults={'name': f"Time {fields['away_team']}"}
            )
            
            fields_copy = fields.copy()
            fields_copy.pop('home_team')
            fields_copy.pop('away_team')

            Tip.objects.update_or_create(
                pk=pk,
                defaults={
                    **fields_copy,
                    'home_team': home,
                    'away_team': away
                }
            )
            print(f"Jogo {pk} importado.")

        elif item['model'] == 'tips_core.promocaobanner':
            PromocaoBanner.objects.update_or_create(pk=pk, defaults=fields)
            print(f"Banner {pk} importado.")

    print("\n--- IMPORTAÇÃO CONCLUÍDA COM SUCESSO! ---")

if __name__ == '__main__':
    importar()
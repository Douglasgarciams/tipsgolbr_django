import os
import django

# Configura o ambiente do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tipsgolbr_config.settings')
django.setup()

from tips_core.models import Team, Tip

def fix():
    print("Iniciando varredura de nomes nas Tips...")
    
    # Busca nomes de times que foram escritos mas não têm objeto Team vinculado
    # ou que existem apenas como texto nas dicas antigas.
    tips = Tip.objects.all()
    count_criados = 0

    for tip in tips:
        # Se você tiver campos de texto ou se os ForeignKeys estiverem vazios,
        # esse script tenta recuperar o vínculo.
        if tip.home_team:
            obj, created = Team.objects.get_or_create(name=tip.home_team.name)
            if created: count_criados += 1
            
        if tip.away_team:
            obj, created = Team.objects.get_or_create(name=tip.away_team.name)
            if created: count_criados += 1

    print(f"Varredura concluída!")
    print(f"Total de times agora no banco: {Team.objects.count()}")

if __name__ == "__main__":
    fix()
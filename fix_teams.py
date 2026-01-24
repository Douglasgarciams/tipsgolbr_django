import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tipsgolbr_config.settings')
django.setup()

from tips_core.models import Team, Tip

# Pega todos os nomes de times que estão nas dicas mas podem não estar na tabela Team
home_teams = Tip.objects.values_list('home_team__name', flat=True)
away_teams = Tip.objects.values_list('away_team__name', flat=True)
todos_nomes = set(list(home_teams) + list(away_teams))

for nome in todos_nomes:
    if nome:
        obj, created = Team.objects.get_or_create(name=nome)
        if created:
            print(f"Time criado: {nome}")

print("Finalizado! Agora todos os times das dicas existem na tabela Team.")
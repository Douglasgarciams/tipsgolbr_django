from django.db.models.signals import post_save
from django.contrib.auth import update_session_auth_hash
from .models import Assinatura 

def sync_premium_status(sender, instance, created, **kwargs):
    """
    Sincroniza o status 'is_active' da Assinatura com o campo 'is_premium_member' do Usuário.
    Executado após o modelo Assinatura ser salvo.
    """
    # 1. Puxa o objeto do usuário
    user = instance.user
    
    # 2. Atualiza o status do usuário com o status da Assinatura
    user.is_premium_member = instance.is_active
    
    # 3. Salva o objeto do usuário
    # Usar update_fields evita que este signal chame recursivamente outros signals
    user.save(update_fields=['is_premium_member']) 

# Conecta a função ao evento post_save do modelo Assinatura
post_save.connect(sync_premium_status, sender=Assinatura)
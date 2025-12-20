# tips_core/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings 
from django.db.models.signals import post_save 
from django.utils import timezone # IMPORTADO: Necessário para usar timezone.now

# --- 1. MODELO DE USUÁRIO CUSTOMIZADO ---
class CustomUser(AbstractUser):
    """
    Modelo de Usuário estendido para o TipsGolBR.
    """
    is_premium_member = models.BooleanField(
        default=False,
        verbose_name='Membro Premium'
    )
    
    premium_expiration_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name='Expiração Premium'
    )
    
    # --- CORREÇÃO DO ERRO E304 (Chaves Estrangeiras Colidindo) ---
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set', 
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions_set', 
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    # ----------------------------------------------------------------

    def __str__(self):
        return self.username


# --- DEFINIÇÕES DE ESCOLHAS ---
STATUS_CHOICES = [
    ('PENDING', 'Pendente'),
    ('WIN', 'Ganho'),
    ('LOSS', 'Perda'),
    ('VOID', 'Anulada'),
]

ACCESS_LEVEL_CHOICES = [
    ('FREE', 'Grátis'),
    ('PREMIUM', 'Premium'),
]

METHOD_CHOICES = [
    # Inclua suas choices de método aqui, se necessário.
    # Exemplo: ('M1', 'Método Exemplo 1'),
    #         ('M2', 'Método Exemplo 2'),
]

# --- 2. MODELO DE DICA (TIP) ---
class Tip(models.Model):
    """
    Representa uma dica de aposta de futebol no TipsGolBR.
    """
    match_title = models.CharField(max_length=200, verbose_name='Título do Jogo')
    league = models.CharField(max_length=100, verbose_name='Liga/Competição')
    match_date = models.DateTimeField(verbose_name='Data e Hora do Jogo')

    prediction = models.TextField(verbose_name='Prognóstico (Ex: Over 2.5, Casa vence)')
    odd_value = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Odd (Cotação)')
    
    link_aposta = models.URLField(
        max_length=500, 
        blank=True, 
        null=True, 
        verbose_name="Link para Aposta (URL)"
    )
    
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='PENDING',
        verbose_name='Resultado'
    )

    access_level = models.CharField(
        max_length=10, 
        choices=ACCESS_LEVEL_CHOICES, 
        default='FREE',
        verbose_name='Nível de Acesso'
    )
    
    # Adicione este campo se ele estiver faltando (necessário para a View analysis_dashboard)
    # method = models.CharField(max_length=10, choices=METHOD_CHOICES, verbose_name='Método de Aposta', default='M1')
    
    # Campos para cálculo de lucro (necessário para a View analysis_dashboard)
    # valor_aposta = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Valor Apostado')
    # valor_ganho = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Lucro Líquido (se WIN)')
    # valor_perda = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Prejuízo (se LOSS)')


    class Meta:
        verbose_name = "Dica de Aposta"
        verbose_name_plural = "Dicas de Apostas"

    def __str__(self):
        return f"{self.match_title} - {self.prediction}"
        
        
# --- 3. MODELO DE NOTÍCIA ---
class Noticia(models.Model):
    titulo = models.CharField(max_length=255, unique=True, verbose_name="Título")
    fonte_url = models.URLField(max_length=500, verbose_name="URL da Fonte")
    resumo = models.TextField(blank=True, null=True, verbose_name="Resumo")
    
    # MODIFICAÇÃO CHAVE: data_publicacao agora tem um default (timezone.now)
    data_publicacao = models.DateTimeField(
        verbose_name="Data de Publicação",
        default=timezone.now
    ) 
    
    data_extracao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Extração")

    imagem_url = models.URLField(
        max_length=500, 
        blank=True, 
        null=True, 
        verbose_name="URL da Imagem de Capa"
    )
    
    class Meta:
        verbose_name = "Notícia Diária"
        verbose_name_plural = "Notícias Diárias"
        ordering = ['-data_publicacao'] 

    def __str__(self):
        return self.titulo
        
        
# --- 4. MODELO DE ASSINATURA ---
class Assinatura(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Usuário"
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativa")
    start_date = models.DateTimeField(auto_now_add=True, verbose_name="Data de Início")
    
    class Meta:
        verbose_name = "Assinatura Premium"
        verbose_name_plural = "Assinaturas Premium"
    
    def __str__(self):
        return f"Assinatura de {self.user.username} - Ativa: {self.is_active}"

# ----------------------------------------------------------------
# --- CORREÇÃO FINAL: LOGICA DE SINCRONIZAÇÃO VIA SIGNALS ---
# ----------------------------------------------------------------

def sync_premium_status(sender, instance, **kwargs):
    """Sincroniza o status 'is_active' da Assinatura com o campo 'is_premium_member' do Usuário."""
    
    user = instance.user
    user.is_premium_member = instance.is_active
    user.save(update_fields=['is_premium_member']) 

# Conecta a função ao evento post_save (após salvar) do modelo Assinatura
post_save.connect(sync_premium_status, sender=Assinatura)
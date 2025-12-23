# tips_core/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings 
from django.db.models.signals import post_save 
from django.utils import timezone 
from datetime import date 

# --- 1. MODELO DE USUÁRIO CUSTOMIZADO ---
class CustomUser(AbstractUser):
    """
    Modelo de Usuário estendido para o TipsGolBR.
    A lógica de save() garante que is_premium_member seja controlado pela data.
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
    
    # 🌟 IMPLEMENTAÇÃO CORRIGIDA: MÉTODO save() SOBRESCRITO
    def save(self, *args, **kwargs):
        """
        Sobrescreve o save() para garantir que is_premium_member seja sempre
        calculado pela data de expiração (Prevalência da data).
        """
        today = date.today()
        
        # Correção para evitar IntegrityError: 
        # Verificamos se existe uma data antes de comparar.
        if self.premium_expiration_date:
            is_active_by_date = self.premium_expiration_date >= today
        else:
            is_active_by_date = False
        
        # Garante que o campo booleano nunca seja NULL ao salvar no banco
        self.is_premium_member = is_active_by_date
        
        super().save(*args, **kwargs)

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

    def __str__(self):
        return self.username


# --- DEFINIÇÕES DE ESCOLHAS ---

METHOD_CHOICES = [
    ('LAY0X1', 'LAY 0x1'),
    ('LAY0X2', 'LAY 0x2'),
    ('LAY0X3', 'LAY 0x3'),
    ('LAY1X0', 'LAY 1x0'),
    ('LAY2X0', 'LAY 2x0'),
    ('LAY3X0', 'LAY 3x0'),
    ('LAY2X2', 'LAY 2x2'),
    ('LAYGC', 'LAY GOLEADA CASA'),
    ('LAYGV', 'LAY GOLEADA VISITANTE'),
    ('BACKC', 'BACK CASA'),
    ('BACKV', 'BACK VISITANTE'),
    ('OVER05HT', 'OVER 0.5 HT'),
    ('OVER05FT', 'OVER 0.5 FT'),
    ('OVER15FT', 'OVER 1.5 FT'),
]

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


# --- 2. MODELO DE DICA (TIP) ---
class Tip(models.Model):
    match_title = models.CharField(max_length=200, verbose_name='Título do Jogo')
    league = models.CharField(max_length=100, verbose_name='Liga/Competição')
    match_date = models.DateTimeField(verbose_name='Data e Hora do Jogo')

    method = models.CharField(
        max_length=10, 
        choices=METHOD_CHOICES, 
        default='LAY0X1',
        verbose_name='Método de Aposta'
    )
    
    odd_value = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Odd (Cotação)')
    
    resultado_final = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        verbose_name='Resultado Final'
    )

    is_active = models.BooleanField(
        default=True, 
        verbose_name='Aposta Ativa/Visível',
        help_text='Desmarque para ocultar esta aposta do site (mas manter no histórico/gráfico).'
    )
    
    valor_aposta = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00, 
        verbose_name='Valor da Aposta (Stake)'
    )
    
    valor_ganho = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00, 
        verbose_name='Valor Ganho (Lucro)'
    )
    
    valor_perda = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00, 
        verbose_name='Valor Perda (Prejuízo)'
    )

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

    class Meta:
        verbose_name = "Dica de Aposta"
        verbose_name_plural = "Dicas de Apostas"

    def __str__(self):
        return f"{self.match_title} - {self.get_method_display()}" 
        
        
# --- 3. MODELO DE NOTÍCIA ---
class Noticia(models.Model):
    titulo = models.CharField(max_length=255, unique=True, verbose_name="Título")
    fonte_url = models.URLField(max_length=500, verbose_name="URL da Fonte")
    resumo = models.TextField(blank=True, null=True, verbose_name="Resumo")
    data_publicacao = models.DateTimeField(verbose_name="Data de Publicação", default=timezone.now) 
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


# --- 5. MODELO DE PROMOÇÃO/BANNER PARA CARROSSEL ---
class PromocaoBanner(models.Model):
    titulo = models.CharField(max_length=200, verbose_name="Título do Banner", blank=True, null=True)
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição Curta")
    
    imagem = models.ImageField(
        upload_to='promo_banners/', 
        verbose_name="Imagem/Banner (Upload)"
    )

    link_url = models.URLField(max_length=500, verbose_name="URL de Redirecionamento", help_text="Link para onde o banner irá direcionar.")
    ativo = models.BooleanField(default=True, verbose_name="Banner Ativo", help_text="Marque para exibir o banner no carrossel.")
    ordem = models.IntegerField(default=0, help_text="Defina a ordem de exibição (menor número aparece primeiro).")
    data_criacao = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['ordem', '-data_criacao']
        verbose_name = "Banner de Promoção"
        verbose_name_plural = "Banners de Promoções"

    def __str__(self):
        return self.titulo or f"Banner ID {self.id}" 

# ----------------------------------------------------------------
# --- LOGICA DE SINCRONIZAÇÃO VIA SIGNALS (REVISADA) ---
# ----------------------------------------------------------------

def sync_premium_status(sender, instance, **kwargs):
    """
    Sincroniza a Assinatura com o CustomUser.
    """
    user = instance.user
    
    # Se a assinatura for marcada como inativa, podemos limpar a data (opcional)
    if not instance.is_active:
        user.premium_expiration_date = None
        
    # Salva o usuário, o que dispara o método save() do CustomUser e recalcula tudo
    user.save() 

post_save.connect(sync_premium_status, sender=Assinatura)
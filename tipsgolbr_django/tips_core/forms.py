# tips_core/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    """
    Formulário para a criação de novos usuários (Registro).
    Usa o nosso CustomUser.
    """
    class Meta:
        model = CustomUser
        # Campos que o usuário precisa preencher no registro:
        fields = ('username', 'email', 'first_name', 'last_name') 
        # NOTA: O campo 'password' já é tratado pelo UserCreationForm
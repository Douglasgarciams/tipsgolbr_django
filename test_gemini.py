# Arquivo: test_gemini.py

import os
from google import genai
from google.genai.errors import APIError

print("--- Iniciando Teste de Conexão Gemini ---")

# 1. Tenta inicializar o cliente
try:
    # Ele buscará a chave na variável de ambiente GEMINI_API_KEY
    client = genai.Client()
    print("STATUS: Cliente Gemini inicializado com sucesso.")

    # 2. Executa uma consulta simples com busca na web
    print("\n--- Executando Chamada de Teste com Busca ---")
    
    prompt = "Qual o desfalque mais recente do Flamengo para o próximo jogo, em uma frase?"
    print(f"PROMPT: {prompt}")

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )

    print("\n--- Resultado da API ---")
    print(f"STATUS: SUCESSO. Resposta recebida.")
    print(f"RESPOSTA: {response.text}")

except APIError as e:
    print("\n--- Erro Crítico da API ---")
    print(f"FALHA: Erro na chamada da API. Detalhe: {e}")
    print("A CHAVE PODE ESTAR INCORRETA, INVÁLIDA OU O PAGAMENTO PODE ESTAR INATIVO/SEM CRÉDITO.")

except Exception as e:
    print("\n--- Erro de Ambiente/Dependência ---")
    print(f"FALHA: Erro ao inicializar o cliente. O módulo foi encontrado? Detalhe: {e}")

print("\n--- Fim do Teste ---")
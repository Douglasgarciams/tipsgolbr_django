@echo off
REM Arquivo: run_extractor.bat

REM Define o caminho para o Python do seu ambiente virtual (venv)
set PYTHON_EXE="C:\Users\Home\TipsGolBR_project\venv\Scripts\python.exe"

REM Define o caminho para o manage.py
set MANAGE_PY="C:\Users\Home\TipsGolBR_project\manage.py"

REM Executa a função extrair_noticias_rss via o shell do Django
REM O comando é fechado entre aspas duplas para garantir que o Windows processe o comando Python
%PYTHON_EXE% %MANAGE_PY% shell --command="from tips_core.tasks import extrair_noticias_rss; print('Iniciando extração...'); extrair_noticias_rss()"

REM Adiciona uma pausa para que a janela não feche imediatamente após a execução, permitindo que você veja o resultado.
pause
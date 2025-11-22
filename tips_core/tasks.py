# tips_core/tasks.py (ATUALIZADO COM LIMPEZA DE IMAGENS NO RESUMO)

import feedparser
import time
from datetime import datetime
from django.utils import timezone
from .models import Noticia
import requests
from bs4 import BeautifulSoup

# --- FEEDS RSS ATIVOS ---
RSS_FEEDS = [
    'https://ge.globo.com/rss/ge/futebol/',
    'https://www.gazetaesportiva.com/feed/',
    'https://rss.uol.com.br/esporte/ultimas-noticias.xml',
]

# -------------------------------
# FUNÇÃO PARA REMOVER <img> DO RESUMO
# -------------------------------
def limpar_html_resumo(resumo):
    """
    Remove imagens e tags problemáticas do resumo do RSS.
    Evita a quebra de layout no template.
    """
    try:
        soup = BeautifulSoup(resumo, 'html.parser')

        # Remove todas as tags <img>
        for img in soup.find_all('img'):
            img.decompose()

        return str(soup)
    except:
        return resumo  # fallback seguro


# -------------------------------
# FUNÇÃO PARA BUSCAR A IMAGEM DA PÁGINA
# -------------------------------
def get_image_url_from_page(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Tenta pegar imagem Open Graph
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image['content']

        # Tenta pegar imagem principal
        img_tag = soup.find('img')
        if img_tag and img_tag.get('src'):
            return img_tag['src']

        return None
    except:
        return None


# -------------------------------
# EXTRATOR PRINCIPAL
# -------------------------------
def extrair_noticias_rss():
    """Extrai notícias dos feeds RSS e salva no banco."""
    noticias_novas = 0

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)

            for item in feed.entries:

                # -------------------------------
                # DATA DA PUBLICAÇÃO
                # -------------------------------
                pub_date = timezone.now()
                if hasattr(item, 'published_parsed'):
                    try:
                        timestamp = time.mktime(item.published_parsed)
                        pub_date = datetime.fromtimestamp(timestamp, tz=timezone.get_current_timezone())
                    except:
                        pass

                # -------------------------------
                # CAMPOS OBRIGATÓRIOS
                # -------------------------------
                titulo = getattr(item, 'title', None)
                link = getattr(item, 'link', None)
                resumo_raw = getattr(item, 'summary', "Sem resumo disponível.")

                if titulo and link and not Noticia.objects.filter(titulo=titulo).exists():

                    # --- Limpar resumo (remove <img>) ---
                    resumo_limpo = limpar_html_resumo(resumo_raw)

                    # --- Scraping da imagem ---
                    imagem_url_capa = get_image_url_from_page(link)

                    # -------------------------------
                    # SALVAR NO BANCO
                    # -------------------------------
                    Noticia.objects.create(
                        titulo=titulo,
                        fonte_url=link,
                        resumo=resumo_limpo,
                        data_publicacao=pub_date,
                        imagem_url=imagem_url_capa
                    )

                    noticias_novas += 1

        except Exception as e:
            print(f"Erro ao processar feed {feed_url}: {e}")

    return f"Extração concluída. {noticias_novas} novas notícias salvas."

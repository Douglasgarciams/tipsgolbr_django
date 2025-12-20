import feedparser
import time
from datetime import datetime
from django.utils import timezone
from .models import Noticia 
import requests 
from bs4 import BeautifulSoup 

# --- FEEDS RSS ATIVOS ---
RSS_FEEDS = [
    # G1/GE Esportes (Geralmente mais focado em futebol do que o feed genérico)
    'https://ge.globo.com/rss/ge/futebol/', 
    # Notícias esportivas mais gerais, mas mais estáveis que as específicas de campeonatos
    'https://www.gazetaesportiva.com/feed/', 
    # UOL Esporte (Mais estável que o feed anterior)
    'https://rss.uol.com.br/esporte/ultimas-noticias.xml', 
]

# Função para encontrar a imagem dentro da página HTML
def get_image_url_from_page(url):
    try:
        # Simula um navegador para evitar bloqueios
        headers = {'User-Agent': 'Mozilla/5.0'}
        # Aumenta o timeout para 10 segundos, pois a busca de imagens é lenta
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Procura a tag meta Open Graph (Padrão para redes sociais/capa)
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image['content']
        
        # Fallback: Procura a primeira imagem principal (menos confiável)
        img_tag = soup.find('img', {'class': lambda x: x and ('capa' in x or 'principal' in x)})
        if img_tag and img_tag.get('src'):
            return img_tag['src']
            
        return None # Nenhuma imagem encontrada
        
    except Exception as e:
        # print(f"Erro ao buscar imagem em {url}: {e}") # Descomente para debug
        return None

def extrair_noticias_rss():
    """Extrai notícias de feeds RSS, incluindo o web scraping da imagem."""
    noticias_novas = 0
    
    # Define o fuso horário atual para uso consistente
    current_timezone = timezone.get_current_timezone() 
    
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            
            for item in feed.entries:
                
                # A data do RSS será ignorada, mas mantemos o código para debug futuro
                # pub_date = timezone.now()
                # if hasattr(item, 'published_parsed'):
                #     try:
                #         timestamp = time.mktime(item.published_parsed)
                #         pub_date = datetime.fromtimestamp(timestamp, tz=current_timezone)
                #     except ValueError:
                #         pass
                
                titulo = getattr(item, 'title', None)
                link = getattr(item, 'link', None)
                resumo = getattr(item, 'summary', "Sem resumo disponível.")
                
                # Corrigido: Usar update_or_create para evitar duplicatas, mas criar novas se não existirem
                if titulo and link:
                    
                    # Verifica se a notícia já existe pelo título para evitar o web scraping desnecessário
                    if Noticia.objects.filter(titulo=titulo).exists():
                        continue 
                    
                    # --- NOVO PASSO: WEBSCRAPING DA IMAGEM ---
                    imagem_url_capa = get_image_url_from_page(link)
                    # ----------------------------------------
                    
                    Noticia.objects.create(
                        titulo=titulo,
                        fonte_url=link,
                        resumo=resumo,
                        
                        # CORREÇÃO FINAL: Força a data de publicação a ser o momento atual.
                        data_publicacao=timezone.now(), 
                        
                        imagem_url=imagem_url_capa # Salva a URL da imagem
                    )
                    noticias_novas += 1
                    
        except Exception as e:
            # print(f"Erro catastrófico ao processar feed {feed_url}: {e}") # Descomente para debug
            continue # Tenta o próximo feed
            
    return f"Extração concluída. {noticias_novas} novas notícias salvas."
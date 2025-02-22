from notion_client import Client
from urllib.parse import quote
import pandas as pd
import requests
from config import DATABASE_ID, TOKEN_V3, OMDB_API_KEY

def notionhook(request):
    """
    Função para receber e processar webhooks do Notion.
    """
    # Verifica se a requisição contém JSON
    if request.is_json:
        # Acessa os dados enviados pelo Notion
        request = request.get_json()
        dados = request['data']
        print("Dados recebidos do Notion:", dados)

        # Verifica se a estrutura dos dados está correta
        if 'properties' not in dados or 'Name' not in dados['properties']:
            print("Propriedade 'Name' não encontrada ou formato inválido.")
            return {"status": "error", "message": "Propriedade 'Name' não encontrada ou formato inválido."}, 400

        # Verifica se a estrutura dos dados está correta
        if 'properties' not in dados:
            print("Propriedades não encontradas nos dados.")
            return {"status": "error", "message": "Propriedades não encontradas nos dados."}, 400

        # Extrai o título da página
        if 'Name' in dados['properties'] and 'title' in dados['properties']['Name']:
            title = dados['properties']['Name']['title'][0]['plain_text']
            print(f"Título da página: {title}")
        else:
            print("Propriedade 'Name' não encontrada ou formato inválido.")
            return {"status": "error", "message": "Propriedade 'Name' não encontrada ou formato inválido."}, 400

        # Obter informações do OMDB
        omdb_url = f"http://www.omdbapi.com/?t={quote(title)}&apikey={OMDB_API_KEY}"
        try:
            response = requests.get(omdb_url)
            response.raise_for_status()  # Lança uma exceção se o status não for 200
            data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao acessar a API do OMDB: {e}")
            return {"status": "error", "message": f"Erro ao acessar a API do OMDB: {e}"}, 500

        # Extrai informações do filme
        director = data.get('Director', 'N/A')
        genre = data.get('Genre', 'N/A')
        country = data.get('Country', 'N/A')
        language = data.get('Language', 'N/A')
        released_date = data.get('Released', 'N/A')
        try:
            released_date = pd.to_datetime(released_date).strftime('%Y-%m-%d')
        except ValueError:
            released_date = 'N/A'
        year = released_date.split('-')[0] if released_date != 'N/A' else 'N/A'
        poster = data.get('Poster', 'N/A')
        actors = data.get('Actors', 'N/A')
        Date = pd.Timestamp.today().strftime('%Y-%m-%d')

        # Adicionar ao banco de dados do Notion
        try:
            client = Client(auth=TOKEN_V3)
            response = client.pages.update(
                page_id=dados['id'],
                properties={
                    "Name": {"title": [{"text": {"content": title}}]},
                    "Date": {"date": {"start": Date}},
                    "Year": {"rich_text": [{"text": {"content": year}}]},
                    "Director": {"multi_select": [{"name": diretor.strip()} for diretor in director.split(",")] if director != 'N/A' else []},
                    "Actors": {"multi_select": [{"name": actor.strip()} for actor in actors.split(",")] if actors != 'N/A' else []},
                    "Genre": {"multi_select": [{"name": genre.strip()} for genre in genre.split(",")] if genre != 'N/A' else []},
                    "Country": {"multi_select": [{"name": country.strip()} for country in country.split(",")] if country != 'N/A' else []},
                    "Language": {"multi_select": [{"name": language.strip()} for language in language.split(",")] if language != 'N/A' else []},
                    "Released Date": {"date": {"start": released_date}} if released_date != 'N/A' else {"date": None},
                    "Poster": {"files": [{"name": "Poster", "external": {"url": poster}}]}
                }
            )
            print(f"Added {title} to Notion Database")
        except Exception as e:
            print(f"Erro ao atualizar a página no Notion: {e}")
            return {"status": "error", "message": f"Erro ao atualizar a página no Notion: {e}"}, 500

        # Retorna uma resposta de sucesso
        return {"status": "success", "message": "Webhook recebido com sucesso!"}, 200
    else:
        # Se não for JSON, retorna um erro
        return {"status": "error", "message": "Requisição inválida: o corpo deve ser JSON"}, 400
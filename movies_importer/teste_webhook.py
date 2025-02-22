import json
from urllib.parse import quote

import pandas as pd
import requests
from ..config import DATABASE_ID, OMDB_API_KEY, TOKEN_V3
from notion_client import Client

with open('/home/gustavo/Letterboxd-to-Notion/letterboxd2notion/notion_moviedb_json_example.json', 'r', encoding='utf-8-sig') as file:
    request = json.load(file)
    

# Verifica se a requisição contém JSON
if request.exists():
    # Acessa os dados enviados pelo Notion
    dados = request.get_json()
    print("Dados recebidos do Notion:", dados)

    # Processa os dados (exemplo: extrair informações específicas)
    if dados.get("object") == "page":
        page_id = dados.get("id")
        title = dados.get(['data']['properties']['Name']['title'][0]['plain_text'])

        # Obter informações do OMDB
        omdb_url = f"http://www.omdbapi.com/?t={quote(title)}&apikey={OMDB_API_KEY}"
        response = requests.get(omdb_url)
        data = response.json()

        director = data.get('Director', 'N/A')
        genre = data.get('Genre', 'N/A')
        country = data.get('Country', 'N/A')
        language = data.get('Language', 'N/A')
        released_date = data.get('Released', 'N/A')
        if released_date != 'N/A':
            released_date = pd.to_datetime(released_date).strftime('%Y-%m-%d')
        year = released_date.split('-')[0] if released_date != 'N/A' else 'N/A'
        poster = data.get('Poster', 'N/A')
        actors = data.get('Actors', 'N/A')
        Date = pd.Timestamp.today().strftime('%Y-%m-%d')

        # Adicionar ao banco de dados do Notion
        client = Client(auth=TOKEN_V3)
        database_id = DATABASE_ID

        # Change the type of a column in the Notion database
        database = client.databases.retrieve(database_id=database_id)
        properties = database['properties']

        # Example: Change the type of the "Year" column to "number"
        if "Year" in properties:
            properties["Year"]["type"] = "number"
            properties["Year"]["number"] = {}

        client.databases.update(
            database_id=database_id,
            properties=properties
        )

        response = client.pages.update(
            page_id=page_id,
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

#     # Retorna uma resposta de sucesso
#     return {"status": "success", "message": "Webhook recebido com sucesso!"}, 200
# else:
#     # Se não for JSON, retorna um erro
#     return {"status": "error", "message": "Requisição inválida: o corpo deve ser JSON"}, 400

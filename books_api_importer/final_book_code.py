import json
from urllib.parse import quote
from notion_client import Client
from urllib.parse import quote
import pandas as pd
import requests
from config import TOKEN_V3  # OMDB_API_KEY removido


def notionbook(request):
    if request.is_json:
        request = request.get_json()
        dados = request['data']
        print("Dados recebidos do Notion:", dados)# Verifica se a estrutura dos dados está correta

            # Extrai título
        title = dados['properties']['Name']['title'][0]['plain_text']
        print(f"Título: {title}")
        
        # Extrai autor, se existir
        author = ""
        if 'Author' in dados['properties']:
            author = dados['properties']['Author']['rich_text'][0]['plain_text']
            print(f"Autor: {author}")
            
        query = f"intitle:{quote(title)}"
        if author:
            query += f"+inauthor:{quote(author)}"

        api_url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=1&langRestrict=pt"
        print(api_url)

        try:
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro na Google Books API: {e}")
            return {"status": "error", "message": str(e)}, 500

        if not data.get("items"):
            return {"status": "error", "message": "Livro não encontrado"}, 404

        info = data["items"][0].get("volumeInfo", {})
        
        # Extrair informações
        titulo = info.get("title", title)
        autores = info.get("authors", [])
        data_pub = info.get("publishedDate", "")
        descricao = info.get("description", "Sem descrição.")
        page_count = info.get("pageCount", 0)
        categorias = info.get("categories", [])
        capa = info.get("imageLinks", {}).get("thumbnail", "")
        isbn13 = next((id['identifier'] for id in info.get("industryIdentifiers", []) if id['type'] == 'ISBN_13'), "")
        isbn10 = next((id['identifier'] for id in info.get("industryIdentifiers", []) if id['type'] == 'ISBN_10'), "")
        
        try:
            data_pub_formatada = pd.to_datetime(data_pub).strftime('%Y-%m-%d')
        except:
            data_pub_formatada = None
            
        try:
            client = Client(auth=TOKEN_V3)
            response = client.pages.update(
                page_id=dados['id'],
                properties={
                    "Name": {"title": [{"text": {"content": titulo}}]},
                    "Publish Date": {"date": {"start": data_pub_formatada}} if data_pub_formatada else {},
                    # "Categories": {"multi_select": [{"name": cat.strip()} for cat in categorias]},
                    "Description": {"rich_text": [{"text": {"content": descricao}}]},
                    "Image": {"files": [{"name": "Image", "external": {"url": capa}}]} if capa else {},
                    "Pages": {"number": page_count} if page_count else {},
                    "ISBN-13": {"rich_text": [{"text": {"content": isbn13}}]} if isbn13 else {},
                    "ISBN-10": {"rich_text": [{"text": {"content": isbn10}}]} if isbn10 else {},
                }
            )
            print(f"{titulo} atualizado no Notion.")
        except Exception as e:
            print(f"Erro ao atualizar no Notion: {e}")
            return {"status": "error", "message": str(e)}, 500
        return {"status": "success", "message": "Livro atualizado com sucesso!"}, 200
    else:
        return {"status": "error", "message": "Requisição inválida: o corpo deve ser JSON"}, 400

notionhook(request)
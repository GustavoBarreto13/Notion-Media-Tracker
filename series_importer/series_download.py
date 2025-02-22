import json
from urllib.parse import quote
import pandas as pd
import requests
from config import DATABASE_ShOWS_ID, TOKEN_V3, TRAKT_CLIENT_ID, TMDB_API_KEY
from notion_client import Client

def serieshook(file_path):
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        request = json.load(file)

    if request:
        # Acessa os dados enviados pelo Notion
        dados = request['data'] 
        print("Dados recebidos do Notion:")

        # Processa os dados (exemplo: extrair informações específicas)
        if dados.get("object") == "page":
            page_id = dados.get("id")
            title = dados['properties']['Name']['title'][0]['plain_text']
            title_url = title.replace(" ", "-").lower()

            # Obter show_id do Trakt
            trakt_url = f"https://api.trakt.tv/shows/{title_url}?extended=full"
            headers = {
                "Content-Type": "application/json",
                "trakt-api-version": "2",
                "trakt-api-key": TRAKT_CLIENT_ID
            }
            response = requests.get(trakt_url, headers=headers)
            data = response.json()
            show_id = data['ids']['tmdb']

            # Obter dados do show do TMDB
            tmdb_url_show = f"https://api.themoviedb.org/3/tv/{show_id}"
            headers = {
                "accept": "application/json",
                "authorization": f"Bearer {TMDB_API_KEY}"
            }
            response = requests.get(tmdb_url_show, headers=headers)
            show_data = response.json()

            networks = show_data['networks'][0]['name']
            first_air_date = show_data['first_air_date']
            last_air_date = show_data['last_air_date']
            backdrop = "https://image.tmdb.org/t/p/original" + show_data['backdrop_path']
            poster = "https://image.tmdb.org/t/p/original" + show_data['poster_path']
            Date = pd.Timestamp.today().strftime('%Y-%m-%d')
            Overview = show_data['overview']
            episode_count = show_data['number_of_episodes']
            seasons_count = show_data['number_of_seasons']
            series_status = show_data['status']
            if show_data['next_episode_to_air']:
                next_episode_to_air = show_data['next_episode_to_air']['air_date'] if show_data['next_episode_to_air'] else None

            client = Client(auth=TOKEN_V3)
            database_id = DATABASE_ShOWS_ID

            response = client.pages.update(
                page_id=page_id,
                properties={
                    "Name": {"title": [{"text": {"content": title}}]},
                    "Release Date": {"date": {"start": first_air_date, "end": last_air_date}},
                    "Poster": {"files": [{"name": "Poster", "external": {"url": poster}}]},
                    "Episode Count": {"number": episode_count},
                    "Network": {"select": {"name": networks}},
                    "Overview": {"rich_text": [{"text": {"content": Overview}}]},
                    "Seasons Count": {"number": seasons_count},
                    "Type": {"select": {"name": "Show"}},
                    "Series Status": {"select": {"name": series_status}},
                },
                cover={
                    "type": "external",
                    "external": {
                        "url": backdrop
                    }
                }
            )

            for season in show_data['seasons']:
                if season['name'] != 'Specials':
                    season_name = season['name']
                    season_number = season['season_number']
                    season_id = season['id']
                    release_date = season['air_date']
                    episode_count = season['episode_count']
                    season_overview = season['overview']
                    poster = "https://image.tmdb.org/t/p/original" + season['poster_path']
                    response = client.pages.create(
                        parent={"database_id": database_id},
                        properties={
                            "Name": {"title": [{"text": {"content": title + f" - {season_name}"}}]},
                            "Release Date": {"date": {"start": release_date}},
                            "Season Number": {"number": season_number},
                            "Episode Count": {"number": episode_count},
                            "Overview": {"rich_text": [{"text": {"content": season_overview}}]},
                            "Type": {"select": {"name": "Season"}},
                            "Poster": {"files": [{"name": "Poster", "external": {"url": poster}}]},
                            "Network": {"select": {"name": networks}},
                            "Parent item": {"relation": [{"id": page_id}]},
                        }
                    )
                    season_page_id = response['id']
                    tmdb_url_episode = f"https://api.themoviedb.org/3/tv/{show_id}/season/{season_number}"
                    headers = {
                        "accept": "application/json",
                        "authorization": f"Bearer {TMDB_API_KEY}"
                    }
                    response = requests.get(tmdb_url_episode, headers=headers)
                    eps_data = response.json()

                    for episode in eps_data['episodes']:
                        episode_number = episode['episode_number']
                        season_number = episode['season_number']
                        episode_name = f"S{season_number:02d}E{episode_number:02d} - {episode['name']}"
                        release_date = episode['air_date']
                        episode_overview = episode['overview']
                        poster = "https://image.tmdb.org/t/p/original" + episode['still_path']
                        response = client.pages.create(
                            parent={"database_id": database_id},
                            properties={
                                "Name": {"title": [{"text": {"content": episode_name}}]},
                                "Release Date": {"date": {"start": release_date}},
                                "Episode Number": {"number": episode_number},
                                "Season Number": {"number": season_number},
                                "Overview": {"rich_text": [{"text": {"content": episode_overview}}]},
                                "Type": {"select": {"name": "Episode"}},
                                "Poster": {"files": [{"name": "Poster", "external": {"url": poster}}]},
                                "Parent item": {"relation": [{"id": season_page_id}]},
                                "Related Series": {"relation": [{"id": page_id}]},
                                "Network": {"select": {"name": networks}},
                            },
                            cover={
                                "type": "external",
                                "external": {
                                    "url": poster
                                }
                            }
                        ),  
                        
            return page_id, title
    return None, None

# Example usage 
file_path = '/home/gustavo/Notion-Media-Tracker/series_importer/notion_seriedb_json_example.json'
page_id, title = serieshook(file_path)
print(page_id, title)

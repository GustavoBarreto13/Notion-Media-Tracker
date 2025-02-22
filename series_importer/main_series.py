import json
from urllib.parse import quote
import pandas as pd
import requests
import logging
from config import DATABASE_ShOWS_ID, TOKEN_V3, TRAKT_CLIENT_ID, TMDB_API_KEY
from notion_client import Client

file_path = '/home/gustavo/Notion-Media-Tracker/series_importer/notion_seriedb_json_example.js'
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def serieshook(file_path):
    """
    Process the Notion data from the given file path.
    
    Args:
        file_path (str): Path to the JSON file containing Notion data.
    
    Returns:
        tuple: Page ID and title extracted from the Notion data.
    """
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            request = json.load(file)

        if request:
            # Access the data sent by Notion
            dados = request['data']
            print("Dados recebidos do Notion:", dados)
        # if request:
        #     # Acessa os dados enviados pelo Notion
        #     request = request.get_json()
        #     dados = request['data']
        #     logging.info("Dados recebidos do Notion: %s", dados)

            # Verifica se a estrutura dos dados está correta
            if 'properties' not in dados or 'Name' not in dados['properties']:
                print("Propriedade 'Name' não encontrada ou formato inválido.")
                return {"status": "error", "message": "Propriedade 'Name' não encontrada ou formato inválido."}, 400

            # Process the data (example: extract specific information)
            if dados.get("object") == "page":
                page_id = dados.get("id")
                title = dados['properties']['Name']['title'][0]['plain_text']
                return page_id, title
        return None, None
    except Exception as e:
        logging.error("Error in serieshook: %s", e)
        return None, None

def get_show_id(title, TRAKT_CLIENT_ID):
    """
    Get the show ID from Trakt API using the show title.
    
    Args:
        title (str): Title of the show.
        TRAKT_CLIENT_ID (str): Trakt API client ID.
    
    Returns:
        int: TMDB show ID.
    """
    try:
        trakt_url = f"https://api.trakt.tv/shows/{quote(title)}?extended=full"
        headers = {
            "Content-Type": "application/json",
            "trakt-api-version": "2",
            "trakt-api-key": TRAKT_CLIENT_ID
        }
        response = requests.get(trakt_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        show_id = data['ids']['tmdb']
        return show_id
    except Exception as e:
        logging.error("Error in get_show_id: %s", e)
        return None

def fetch_show_data(show_id, TMDB_API_KEY):
    """
    Fetch show data from TMDB API.
    
    Args:
        show_id (int): TMDB show ID.
        TMDB_API_KEY (str): TMDB API key.
    
    Returns:
        dict: Show data from TMDB API.
    """
    try:
        tmdb_url_show = f"https://api.themoviedb.org/3/tv/{show_id}"
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {TMDB_API_KEY}"
        }
        response = requests.get(tmdb_url_show, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error("Error in fetch_show_data: %s", e)
        return None

def update_notion_page(client, page_id, title, show_data, networks):
    """
    Update Notion page with show information.
    
    Args:
        client (Client): Notion client.
        page_id (str): Notion page ID.
        title (str): Title of the show.
        show_data (dict): Show data from TMDB API.
    """
    try:
        networks = show_data['networks'][0]['name']
        first_air_date = show_data['first_air_date']
        last_air_date = show_data['last_air_date']
        poster = "https://image.tmdb.org/t/p/original" + show_data['poster_path']
        Overview = show_data['overview']
        episode_count = show_data['number_of_episodes']
        seasons_count = show_data['number_of_seasons']
        series_status = show_data['status']

        client.pages.update(
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
            }
        )
        logging.info("Notion page updated successfully for show: %s", title)
    except Exception as e:
        logging.error("Error in update_notion_page: %s", e)

def process_seasons(client, database_id, show_data, page_id, title, TMDB_API_KEY, networks):
    """
    Process each season of the show and update Notion.
    
    Args:
        client (Client): Notion client.
        database_id (str): Notion database ID.
        show_data (dict): Show data from TMDB API.
        page_id (str): Notion page ID.
        title (str): Title of the show.
        TMDB_API_KEY (str): TMDB API key.
    """
    try:
        for season in show_data['seasons']:
            if season['name'] != 'Specials':
                season_number = season['season_number']
                release_date = season['air_date']
                episode_count = season['episode_count']
                season_overview = season['overview']
                poster = "https://image.tmdb.org/t/p/original" + season['poster_path']
                
                # Create a new page for the season in Notion
                response = client.pages.create(
                    parent={"database_id": database_id},
                    properties={
                        "Name": {"title": [{"text": {"content": title + f" - Season {season_number}"}}]},
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
                
                # Fetch episode data for the season from TMDB API
                tmdb_url_episode = f"https://api.themoviedb.org/3/tv/{show_data['id']}/season/{season_number}"
                headers = {
                    "accept": "application/json",
                    "authorization": f"Bearer {TMDB_API_KEY}"
                }
                response = requests.get(tmdb_url_episode, headers=headers)
                response.raise_for_status()
                eps_data = response.json()

                # Process each episode of the season
                for episode in eps_data['episodes']:
                    episode_name = str(episode['episode_number']) + " - " + episode['name']
                    episode_number = episode['episode_number']
                    season_number = episode['season_number']
                    release_date = episode['air_date']
                    episode_overview = episode['overview']
                    poster = "https://image.tmdb.org/t/p/original" + episode['still_path']
                    
                    # Create a new page for the episode in Notion
                    client.pages.create(
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
                            "Network": {"select": {"name": networks}},
                        }
                    )
                logging.info("Processed season %s for show: %s", season_number, title)
    except Exception as e:
        logging.error("Error in process_seasons: %s", e)

def main():
    try:
        file_path = '/home/gustavo/Notion-Media-Tracker/series_importer/notion_seriedb_json_example.js'
        page_id, title = serieshook(file_path)

        if not page_id or not title:
            logging.error("Failed to retrieve page ID or title from Notion data.")
            return

        show_id = get_show_id(title, TRAKT_CLIENT_ID)
        if not show_id:
            logging.error("Failed to retrieve show ID from Trakt API.")
            return

        show_data = fetch_show_data(show_id, TMDB_API_KEY)
        if not show_data:
            logging.error("Failed to fetch show data from TMDB API.")
            return

        client = Client(auth=TOKEN_V3)
        database_id = DATABASE_ShOWS_ID

        networks = show_data['networks'][0]['name']
        update_notion_page(client, page_id, title, show_data, networks)
        process_seasons(client, database_id, show_data, page_id, title, TMDB_API_KEY, networks)
    except Exception as e:
        logging.error("Error in main: %s", e)

if __name__ == "__main__":
    main()
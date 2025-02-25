﻿import os

from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
env_file_path = os.path.join(parent_dir, ".env")

load_dotenv(env_file_path)

TOKEN_V3 = os.getenv("TOKEN_V3", "")
DATABASE_ID = os.getenv("DATABASE_ID", "")
DATABASE_ShOWS_ID = os.getenv("DATABASE_ShOWS_ID", "")

if not TOKEN_V3 or not DATABASE_ID:
    raise ValueError("Please add your TOKEN_V3 and DATABASE_ID to your .env file.")

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
if not TMDB_API_KEY:
    raise ValueError("Please add your TMDB_API_KEY to your .env file.")

OMDB_API_KEY = os.getenv("OMDB_API_KEY", "")
if not OMDB_API_KEY:
    raise ValueError("Please add your OMDB_API_KEY to your .env file.")

TRAKT_CLIENT_ID = os.getenv("TRAKT_CLIENT_ID", "")
if not TRAKT_CLIENT_ID:
    raise ValueError("Please add your TRAKT_CLIENT_ID to your .env file.")

# TODO(michaelfromyeg): implement; for now, it's OK since we don't import duplicates
# get all data (true) or data after last sync (false)
ALL_DATA = False

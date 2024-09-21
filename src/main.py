import time
import logging
from datetime import datetime
from croniter import croniter

from lidarr import LidarrService
from navidrome import NavidromeService
from spotify import SpotifyService
from playlist import PlaylistManager
from utils import get_env_variable

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for Spotify and other services
SPOTIFY_CLIENT_ID = get_env_variable('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = get_env_variable('SPOTIFY_CLIENT_SECRET')
LIDARR_URL = get_env_variable('LIDARR_URL', 'http://localhost:8686')
LIDARR_API_KEY = get_env_variable('LIDARR_API_KEY')
NAVIDROME_URL = get_env_variable('NAVIDROME_URL', 'http://localhost:4533')
NAVIDROME_USERNAME = get_env_variable('NAVIDROME_USERNAME')
NAVIDROME_PASSWORD = get_env_variable('NAVIDROME_PASSWORD')

# Playlist limits
SPOTIFY_PLAYLIST_LIMIT_BY_ARTIST = int(get_env_variable('SPOTIFY_PLAYLIST_LIMIT_BY_ARTIST', 3))
SPOTIFY_PLAYLIST_LIMIT_BY_CATEGORY = int(get_env_variable('SPOTIFY_PLAYLIST_LIMIT_BY_CATEGORY', 3))
SPOTIFY_RANDOM_CATEGORY_LIMIT = int(get_env_variable('SPOTIFY_RANDOM_CATEGORY_LIMIT', 50))

# Included and excluded categories
INCLUDED_CATEGORIES = get_env_variable('INCLUDED_CATEGORIES', '').split(',')
EXCLUDED_CATEGORIES = get_env_variable('EXCLUDED_CATEGORIES', '').split(',')

# Lidarr profiles
QUALITY_PROFILE_NAME = get_env_variable('QUALITY_PROFILE_NAME', 'HQ')
METADATA_PROFILE_NAME = get_env_variable('METADATA_PROFILE_NAME', 'Standard')

# Cron-like schedule for running the task
CRON_SCHEDULE = get_env_variable('CRON_SCHEDULE', '0 0 * * *')

def run_playlist_manager():
    """Run the main playlist processing logic."""
    logging.info(f"Running task at {datetime.now()}")
    
    # Initialize services
    spotify = SpotifyService(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
    lidarr = LidarrService(lidarr_url=LIDARR_URL, api_key=LIDARR_API_KEY)
    navidrome = NavidromeService(navidrome_url=NAVIDROME_URL, username=NAVIDROME_USERNAME, password=NAVIDROME_PASSWORD)
    
    # Initialize playlist manager
    playlist_manager = PlaylistManager(
        spotify=spotify,
        lidarr=lidarr,
        navidrome=navidrome,
        artist_playlist_limit=SPOTIFY_PLAYLIST_LIMIT_BY_ARTIST,
        category_playlist_limit=SPOTIFY_PLAYLIST_LIMIT_BY_CATEGORY,
        included_categories=INCLUDED_CATEGORIES,
        excluded_categories=EXCLUDED_CATEGORIES,
        random_category_limit=SPOTIFY_RANDOM_CATEGORY_LIMIT,
        quality_profile_name=QUALITY_PROFILE_NAME,
        metadata_profile_name=METADATA_PROFILE_NAME,
    )

    # Process playlists
    playlist_manager.process()
    logging.info("Playlist processing completed.")

def schedule_task():
    cron = croniter(CRON_SCHEDULE, datetime.now())
    
    run_playlist_manager()  # Run immediately
    next_run = cron.get_next(datetime)

    while True:
        current_time = datetime.now()
        if current_time >= next_run:
            run_playlist_manager()
            next_run = cron.get_next(datetime)
        time.sleep(60)

def main():
    logging.info(f"Scheduling task with cron: {CRON_SCHEDULE}")
    schedule_task()

if __name__ == '__main__':
    main()

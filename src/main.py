import os
import time
from datetime import datetime
from croniter import croniter

from lidarr import LidarrService
from navidrome import NavidromeService
from spotify import SpotifyService

# Constants for Spotify and other services
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', 'default-client-id')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', 'default-client-secret')
LIDARR_URL = os.getenv('LIDARR_URL', 'http://localhost:8686')
LIDARR_API_KEY = os.getenv('LIDARR_API_KEY', 'default-lidarr-api-key')
NAVIDROME_URL = os.getenv('NAVIDROME_URL', 'http://localhost:4533')
NAVIDROME_USERNAME = os.getenv('NAVIDROME_USERNAME', 'default-username')
NAVIDROME_PASSWORD = os.getenv('NAVIDROME_PASSWORD', 'default-password')

# Playlist limits
SPOTIFY_PLAYLIST_LIMIT_BY_ARTIST = int(os.getenv('SPOTIFY_PLAYLIST_LIMIT_BY_ARTIST', 3))  # Number of playlists per artist
SPOTIFY_PLAYLIST_LIMIT_BY_CATEGORY = int(os.getenv('SPOTIFY_PLAYLIST_LIMIT_BY_CATEGORY', 3))  # Number of playlists per category
SPOTIFY_RANDOM_CATEGORY_LIMIT = int(os.getenv('SPOTIFY_RANDOM_CATEGORY_LIMIT', 50))  # Number of random categories to process

# Included and excluded categories
INCLUDED_CATEGORIES = os.getenv('INCLUDED_CATEGORIES', '').split(',')
EXCLUDED_CATEGORIES = os.getenv('EXCLUDED_CATEGORIES', '').split(',')

# Cron-like schedule for running the task (example: "0 0 * * *" for midnight every day)
CRON_SCHEDULE = os.getenv('CRON_SCHEDULE', '0 0 * * *')

def run_playlist_manager():
    """Run the main playlist processing logic."""
    print(f"Running task at {datetime.now()}")
    # Initialize services
    spotify = SpotifyService(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
    lidarr = LidarrService(lidarr_url=LIDARR_URL, api_key=LIDARR_API_KEY)
    navidrome = NavidromeService(navidrome_url=NAVIDROME_URL, username=NAVIDROME_USERNAME, password=NAVIDROME_PASSWORD)
    
    # Initialize playlist manager
    manager = PlaylistManager(
        spotify=spotify,
        lidarr=lidarr,
        navidrome=navidrome,
        artist_playlist_limit=SPOTIFY_PLAYLIST_LIMIT_BY_ARTIST,
        category_playlist_limit=SPOTIFY_PLAYLIST_LIMIT_BY_CATEGORY,
        included_categories=INCLUDED_CATEGORIES,
        excluded_categories=EXCLUDED_CATEGORIES,
        random_category_limit=SPOTIFY_RANDOM_CATEGORY_LIMIT
    )

    # Process playlists
    manager.process_playlists(QUALITY_PROFILE_NAME, METADATA_PROFILE_NAME)
    print("Playlist processing completed.")

def schedule_task():
    """Schedule the task using cron-like syntax."""
    cron = croniter(CRON_SCHEDULE, datetime.now())
    next_run = cron.get_next(datetime)
    
    while True:
        current_time = datetime.now()
        
        # Check if it's time to run the task
        if current_time >= next_run:
            run_playlist_manager()
            next_run = cron.get_next(datetime)  # Schedule the next run
        
        # Sleep for a minute before checking again
        time.sleep(60)

def main():
    """Main function to start the cron-like scheduling."""
    print(f"Scheduling task with cron: {CRON_SCHEDULE}")
    schedule_task()

if __name__ == '__main__':
    main()

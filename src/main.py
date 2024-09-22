import time
import logging
from datetime import datetime
from croniter import croniter

from lidarr import LidarrService
from musicbrainz import MusicBrainzService
from navidrome import NavidromeService
from spotify import SpotifyService
from playlist import PlaylistManager
from utils import get_env_variable

import logging

log_level = get_env_variable("LOG_LEVEL", "INFO").upper()

match log_level:
    case "DEBUG":
        logging.basicConfig(
            level=getattr(logging, log_level, logging.DEBUG),
            format="%(levelname)s - %(message)s",
        )
    case _:
        logging.basicConfig(
            level=getattr(logging, log_level, logging.INFO),
            format="%(levelname)s - %(message)s",
        )

# Constants for Spotify and other services
SPOTIFY_CLIENT_ID = get_env_variable("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = get_env_variable("SPOTIFY_CLIENT_SECRET")
LIDARR_URL = get_env_variable("LIDARR_URL", "http://localhost:8686")
LIDARR_API_KEY = get_env_variable("LIDARR_API_KEY")
NAVIDROME_URL = get_env_variable("NAVIDROME_URL", "http://localhost:4533")
NAVIDROME_USERNAME = get_env_variable("NAVIDROME_USERNAME")
NAVIDROME_PASSWORD = get_env_variable("NAVIDROME_PASSWORD")

# Playlist limits
SPOTIFY_PLAYLIST_LIMIT_BY_ARTIST = int(
    get_env_variable("SPOTIFY_PLAYLIST_LIMIT_BY_ARTIST", 3)
)
SPOTIFY_PLAYLIST_LIMIT_BY_CATEGORY = int(
    get_env_variable("SPOTIFY_PLAYLIST_LIMIT_BY_CATEGORY", 3)
)
SPOTIFY_RANDOM_CATEGORY_LIMIT = int(
    get_env_variable("SPOTIFY_RANDOM_CATEGORY_LIMIT", 50)
)

# Included and excluded categories
INCLUDED_CATEGORIES = get_env_variable("INCLUDED_CATEGORIES", "").split(",")
EXCLUDED_CATEGORIES = get_env_variable("EXCLUDED_CATEGORIES", "").split(",")

# Lidarr profiles
QUALITY_PROFILE_NAME = get_env_variable("QUALITY_PROFILE_NAME", "HQ")
METADATA_PROFILE_NAME = get_env_variable("METADATA_PROFILE_NAME", "Standard")

# Cron-like schedule for running the task
CRON_SCHEDULE = get_env_variable("CRON_SCHEDULE", "0 0 * * *")


def run_playlist_manager():
    """Run the main playlist processing logic."""
    logging.info(f"Running task at {datetime.now()}")

    # Log environment variables at debug level
    logging.debug(f"Spotify Client ID: {SPOTIFY_CLIENT_ID}")
    logging.debug(
        f"Spotify Playlist Limit by Artist: {SPOTIFY_PLAYLIST_LIMIT_BY_ARTIST}"
    )
    logging.debug(f"Included Categories: {INCLUDED_CATEGORIES}")
    logging.debug(f"Excluded Categories: {EXCLUDED_CATEGORIES}")
    logging.debug(f"Lidarr Quality Profile: {QUALITY_PROFILE_NAME}")
    logging.debug(f"Lidarr Metadata Profile: {METADATA_PROFILE_NAME}")

    # Initialize services
    logging.debug("Initializing Spotify service...")
    spotify = SpotifyService(
        client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET
    )

    logging.debug("Initializing Lidarr service...")
    lidarr = LidarrService(lidarr_url=LIDARR_URL, api_key=LIDARR_API_KEY)

    logging.debug("Initializing Navidrome service...")
    navidrome = NavidromeService(
        navidrome_url=NAVIDROME_URL,
        username=NAVIDROME_USERNAME,
        password=NAVIDROME_PASSWORD,
    )

    # Initialize playlist manager
    logging.debug("Initializing Playlist Manager...")
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
    logging.debug("Starting playlist processing...")
    playlist_manager.process()
    logging.info("Playlist processing completed.")


def schedule_task():
    cron = croniter(CRON_SCHEDULE, datetime.now())

    logging.debug(f"Initial cron schedule: {CRON_SCHEDULE}")
    logging.debug(f"Next scheduled run time: {cron.get_next(datetime)}")

    run_playlist_manager()
    next_run = cron.get_next(datetime)

    while True:
        current_time = datetime.now()
        logging.debug(f"Current time: {current_time}, Next run: {next_run}")

        if current_time >= next_run:
            logging.debug("Time to run the playlist manager.")
            run_playlist_manager()
            next_run = cron.get_next(datetime)
            logging.debug(f"Next run scheduled at: {next_run}")
        time.sleep(60)


def main():
    logging.info(f"Scheduling task with cron: {CRON_SCHEDULE}")
    schedule_task()


if __name__ == "__main__":
    main()

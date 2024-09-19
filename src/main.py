import os

# Constants
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', 'default-client-id')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', 'default-client-secret')
LIDARR_URL = os.getenv('LIDARR_URL', 'http://localhost:8686')
LIDARR_API_KEY = os.getenv('LIDARR_API_KEY', 'default-lidarr-api-key')
NAVIDROME_URL = os.getenv('NAVIDROME_URL', 'http://localhost:4533')
NAVIDROME_USERNAME = os.getenv('NAVIDROME_USERNAME', 'default-username')
NAVIDROME_PASSWORD = os.getenv('NAVIDROME_PASSWORD', 'default-password')
QUALITY_PROFILE_NAME = os.getenv('QUALITY_PROFILE_NAME', 'HQ')
METADATA_PROFILE_NAME = os.getenv('METADATA_PROFILE_NAME', 'Standard')

def main():
    # Initialize
    spotify_service = SpotifyService(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
    lidarr_service = LidarrService(lidarr_url=LIDARR_URL, api_key=LIDARR_API_KEY)
    navidrome_service = NavidromeService(navidrome_url=NAVIDROME_URL, username=NAVIDROME_USERNAME, password=NAVIDROME_PASSWORD)
    manager = PlaylistManager(spotify_service, lidarr_service, navidrome_service)

    # Run
    manager.process_playlists(QUALITY_PROFILE_NAME, METADATA_PROFILE_NAME)

if __name__ == '__main__':
    main()
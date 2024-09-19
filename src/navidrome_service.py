import requests

class NavidromeService:
    def __init__(self, navidrome_url, username, password):
        self.navidrome_url = navidrome_url
        self.username = username
        self.password = password  # Base64 encoded password for Subsonic API

    def create_playlist(self, playlist_name):
        """Create a playlist in Navidrome."""
        url = f"{self.navidrome_url}/rest/createPlaylist"
        params = {
            'v': '1.16.1',
            'c': 'myapp',
            'f': 'json',
            'name': playlist_name,
            'u': self.username,
            'p': f'enc:{self.password}',
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            playlist_id = response.json()['subsonic-response']['playlist']['id']
            print(f'Created playlist {playlist_name} with ID {playlist_id}')
            return playlist_id
        else:
            print(f'Failed to create playlist {playlist_name}')
            return None

    def search_track_in_navidrome(self, artist_name, track_name):
        """Search for a track in Navidrome using the Subsonic API."""
        url = f"{self.navidrome_url}/rest/search3"
        params = {
            'v': '1.16.1',
            'c': 'myapp',
            'f': 'json',
            'query': f'{artist_name} {track_name}',
            'u': self.username,
            'p': f'enc:{self.password}',
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            search_result = response.json().get('subsonic-response', {}).get('song', [])
            if search_result:
                return search_result[0]['id']
        return None

    def add_tracks_to_playlist(self, playlist_id, track_ids):
        """Add tracks to a playlist in Navidrome."""
        url = f"{self.navidrome_url}/rest/updatePlaylist"
        params = {
            'v': '1.16.1',
            'c': 'myapp',
            'f': 'json',
            'playlistId': playlist_id,
            'songId': track_ids,
            'u': self.username,
            'p': f'enc:{self.password}',
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            print(f'Added {len(track_ids)} tracks to playlist {playlist_id}')
        else:
            print(f'Failed to add tracks to playlist {playlist_id}')

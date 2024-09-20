class NavidromeService:
    def __init__(self, navidrome_url, username, password):
        self.navidrome_url = navidrome_url
        self.username = username
        self.password = password  # Base64 encoded password for Subsonic API

    @property
    def artists(self):
        url = f"{self.navidrome_url}/rest/getArtists"
        params = {
            'v': '1.16.1',
            'c': 'myapp',
            'f': 'json',
            'u': self.username,
            'p': f'enc:{self.password}'
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get('subsonic-response', {}).get('artists', {}).get('index', [])
        else:
            print(f'Failed to fetch artists from Navidrome: {response.content}')
            return []

    def create_playlist(self, playlist_name):
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

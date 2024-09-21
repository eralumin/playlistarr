import requests

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

    def search_playlist(self, playlist_name):
        """Search for a playlist in Navidrome by name."""
        url = f"{self.navidrome_url}/rest/getPlaylists"
        params = {
            'v': '1.16.1',
            'c': 'myapp',
            'f': 'json',
            'u': self.username,
            'p': f'enc:{self.password}',
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            playlists = response.json().get('subsonic-response', {}).get('playlists', {}).get('playlist', [])
            for playlist in playlists:
                if playlist['name'].lower() == playlist_name.lower():
                    return playlist['id']
        return None

    def create_or_update_playlist(self, playlist_name):
        """Create a new playlist or update an existing one if it already exists."""
        playlist_id = self.search_playlist(playlist_name)
        if playlist_id:
            print(f'Playlist "{playlist_name}" already exists with ID {playlist_id}. Updating it.')
            return playlist_id
        else:
            print(f'Creating new playlist: {playlist_name}')
            return self.create_playlist(playlist_name)

    def create_playlist(self, playlist_name):
        """Create a new playlist in Navidrome."""
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
            print(f'Failed to create playlist {playlist_name}: {response.content}')
            return None

    def add_tracks_to_playlist(self, playlist_id, track_ids):
        """Add tracks to an existing playlist in Navidrome."""
        url = f"{self.navidrome_url}/rest/updatePlaylist"
        params = {
            'v': '1.16.1',
            'c': 'myapp',
            'f': 'json',
            'playlistId': playlist_id,
            'songId': track_ids,  # Can be a list of track IDs
            'u': self.username,
            'p': f'enc:{self.password}',
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            print(f'Successfully added {len(track_ids)} tracks to playlist with ID {playlist_id}.')
        else:
            print(f'Failed to add tracks to playlist {playlist_id}: {response.content}')

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

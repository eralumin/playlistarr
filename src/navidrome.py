import hashlib
import random
import string
import requests

class NavidromeService:
    def __init__(self, navidrome_url, username, password):
        self.navidrome_url = navidrome_url
        self.username = username
        self.password = password
        self.salt = self.generate_salt()

    def generate_salt(self, length=6):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def generate_token(self):
        token_string = self.password + self.salt
        return hashlib.md5(token_string.encode('utf-8')).hexdigest()

    @property
    def params(self):
        return {
            'u': self.username,
            't': self.generate_token(),
            's': self.salt,
            'v': '1.16.1',
            'c': 'playlistarr',
            'f': 'json'
        }

    @property
    def artists(self):
        url = f"{self.navidrome_url}/rest/getArtists"
        response = requests.get(url, params=self.params)
        if response.status_code == 200:
            return response.json().get('subsonic-response', {}).get('artists', {}).get('index', [])
        else:
            print(f'Failed to fetch artists from Navidrome: {response.content}')
            return []

    def get_playlist_id_or_none(self, playlist_name):
        url = f"{self.navidrome_url}/rest/getPlaylists"
        response = requests.get(url, params=self.params)
        if response.status_code == 200:
            playlists = response.json().get('subsonic-response', {}).get('playlists', {}).get('playlist', [])
            for playlist in playlists:
                if playlist['name'].lower() == playlist_name.lower():
                    return playlist['id']
        return None

    def create_or_update_playlist(self, playlist_name):
        playlist_id = self.get_playlist_id_or_none(playlist_name)
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
            **self.params,
            'name': playlist_name,
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
        url = f"{self.navidrome_url}/rest/updatePlaylist"
        params = {
            **self.params,
            'playlistId': playlist_id,
            'songId': track_ids,  # Can be a list of track IDs
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            print(f'Successfully added {len(track_ids)} tracks to playlist with ID {playlist_id}.')
        else:
            print(f'Failed to add tracks to playlist {playlist_id}: {response.content}')

    def get_track_id_or_none(self, artist_name, track_name):
        """Search for a track in Navidrome using the Subsonic API."""
        url = f"{self.navidrome_url}/rest/search3"
        params = {
            **self.params,
            'query': f'{artist_name} {track_name}',
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            search_result = response.json().get('subsonic-response', {}).get('song', [])
            if search_result:
                return search_result[0]['id']

        return None

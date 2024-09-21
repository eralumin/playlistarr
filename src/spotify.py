import requests
import base64
from dataclasses import dataclass

@dataclass
class SpotifyArtist:
    _id: str
    name: str

@dataclass
class SpotifyAlbum:
    _id: str
    title: str
    artist: SpotifyArtist

@dataclass
class SpotifyTrack:
    _id: str
    title: str
    album: SpotifyAlbum

@dataclass
class SpotifyPlaylist:
    _id: str
    name: str
    tracks: list[SpotifyTrack]

class SpotifyService:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = self._get_access_token()

    def _get_access_token(self):
        """Authenticate with Spotify API and get access token."""
        auth_url = 'https://accounts.spotify.com/api/token'

        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode('utf-8')
        auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
        auth_header = {
            'Authorization': f'Basic {auth_base64}'
        }
        auth_data = {'grant_type': 'client_credentials'}

        response = requests.post(auth_url, headers=auth_header, data=auth_data)
        response.raise_for_status()

        return response.json()['access_token']

    def _load_playlist_list_from_raw(self, raw_playlists):
        playlists = []
        for raw_playlist in raw_playlists:
            tracks = []
            for raw_track in raw_playlist['tracks']['items']
                artist = SpotifyArtist(
                    _id=raw_track['artists'][0]['id'],
                    name=raw_track['artists'][0]['name'],
                )

                tracks.append(
                    SpotifyTrack(
                        _id=raw_track['id'],
                        title=raw_track['name'],
                        artist=artist,
                    )
                )

            playlist = SpotifyPlaylist(
                _id=raw_playlist['id'],
                name=raw_playlist['name'],
                tracks=tracks,
            )

            playlists.append(playlist)

        return playlists

    def get_categories(self, limit, excluded_categories):
        headers = {'Authorization': f'Bearer {self.token}'}
        fetched_categories = []
        processed_categories = set()

        while len(fetched_categories) < limit:
            url = 'https://api.spotify.com/v1/browse/categories'
            params = {'limit': limit, 'offset': len(processed_categories)}
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            categories = response.json().get('categories', {}).get('items', [])
            for category in categories:
                category_name = category['name'].lower()
                
                # Skip if the category is in excluded_categories or already processed
                if category_name in excluded_categories or category_name in processed_categories:
                    continue

                fetched_categories.append(category)
                processed_categories.add(category_name)

                if len(fetched_categories) >= limit:
                    break

            if len(categories) == 0:
                break

        return fetched_categories

    def get_playlists_for_artist(self, artist_name, limit):
        url = f'https://api.spotify.com/v1/search'
        headers = {'Authorization': f'Bearer {self.token}'}
        params = {
            'q': artist_name,
            'type': 'playlist',
            'limit': limit
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        raw_playlists = response.json().get('playlists', {}).get('items', [])
        return self._load_playlist_list_from_raw(raw_playlists)

    def get_playlists_for_category(self, category_id, limit):
        url = f'https://api.spotify.com/v1/browse/categories/{category_id}/playlists'
        headers = {'Authorization': f'Bearer {self.token}'}
        params = {'limit': limit}

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        raw_playlists = response.json().get('playlists', {}).get('items', [])
        return self._load_playlist_list_from_raw(raw_playlists)

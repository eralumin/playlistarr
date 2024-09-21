import requests
import base64
import logging
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        logging.info('Authenticating with Spotify API...')
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

        logging.info('Successfully authenticated with Spotify API.')
        return response.json()['access_token']

    def _load_playlist_from_raw(self, raw_playlists):
        playlists = []
        for raw_playlist in raw_playlists.get('items', []):
            tracks = []

            tracks_url = raw_playlist['tracks']['href']
            logging.info(f'Fetching tracks for playlist: {raw_playlist["name"]}')
            response = requests.get(tracks_url, headers={'Authorization': f'Bearer {self.token}'})
            response.raise_for_status()
            raw_tracks = response.json().get('items', [])

            for raw_track_item in raw_tracks:
                raw_track = raw_track_item['track']
                artist = SpotifyArtist(
                    _id=raw_track['artists'][0]['id'],
                    name=raw_track['artists'][0]['name'],
                )

                album = SpotifyAlbum(
                    _id=raw_track['album']['id'],
                    title=raw_track['album']['name'],
                    artist=artist,
                )

                tracks.append(
                    SpotifyTrack(
                        _id=raw_track['id'],
                        title=raw_track['name'],
                        album=album,
                    )
                )

            playlists.append(
                SpotifyPlaylist(
                    _id=raw_playlist['id'],
                    name=raw_playlist['name'],
                    tracks=tracks,
                )
            )

            logging.info(f'Playlist {raw_playlist["name"]} loaded with {len(tracks)} tracks.')

        return playlists

    def get_categories(self, limit, excluded_categories):
        headers = {'Authorization': f'Bearer {self.token}'}
        fetched_categories = []
        processed_categories = set()

        logging.info('Fetching Spotify categories...')
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

                logging.info(f'Fetched category: {category_name}')

                if len(fetched_categories) >= limit:
                    break

            if len(categories) == 0:
                break

        logging.info(f'Total fetched categories: {len(fetched_categories)}')
        return fetched_categories

    def get_playlists_for_artist(self, artist_name, limit):
        logging.info(f'Searching for playlists for artist: {artist_name}')
        url = f'https://api.spotify.com/v1/search'
        headers = {'Authorization': f'Bearer {self.token}'}
        params = {
            'q': artist_name,
            'type': 'playlist',
            'limit': limit
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        raw_playlists = response.json().get('playlists', {})
        logging.info(f'Fetched {len(raw_playlists.get("items", []))} playlists for artist {artist_name}.')
        return self._load_playlist_from_raw(raw_playlists)

    def get_playlists_for_category(self, category_id, limit):
        logging.info(f'Fetching playlists for category: {category_id}')
        url = f'https://api.spotify.com/v1/browse/categories/{category_id}/playlists'
        headers = {'Authorization': f'Bearer {self.token}'}
        params = {'limit': limit}

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        raw_playlists = response.json().get('playlists', {})
        logging.info(f'Fetched {len(raw_playlists.get("items", []))} playlists for category {category_id}.')
        return self._load_playlist_from_raw(raw_playlists)

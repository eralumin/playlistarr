import hashlib
import random
import string
import requests
from dataclasses import dataclass, field

@dataclass
class NavidromeArtist:
    _id: str
    name: str

@dataclass
class NavidromeAlbum:
    _id: str
    artist: NavidromeArtist

@dataclass
class NavidromeTrack:
    _id: str
    title: str
    album: NavidromeAlbum

@dataclass
class NavidromePlaylist:
    _id: str
    name: str
    tracks: list[NavidromeTrack] = field(default_factory=list)

class NavidromeService:
    def __init__(self, navidrome_url, username, password):
        self.navidrome_url = navidrome_url
        self.username = username
        self.password = password

    def generate_salt(self, length=48):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def generate_token(self, salt):
        token_string = self.password + salt
        return hashlib.md5(token_string.encode('utf-8')).hexdigest()

    @property
    def params(self):
        salt = self.generate_salt()
        return {
            'u': self.username,
            't': self.generate_token(salt),
            's': salt,
            'v': '1.16.1',
            'c': 'playlistarr',
            'f': 'json'
        }

    @property
    def artists(self):
        url = f"{self.navidrome_url}/rest/getArtists"
        response = requests.get(url, params=self.params)
        artists = []
        if response.status_code == 200:
            raw_indexes = response.json().get('subsonic-response', {}).get('artists', {}).get('index', [])
            for raw_index in raw_indexes:

                for raw_artist in raw_index["artist"]:
                    artists.append(NavidromeArtist(_id=raw_artist['id'], name=raw_artist['name']))
        else:
            print(f'Failed to fetch artists from Navidrome: {response.content}')

        return artists

    def get_playlist_or_none(self, playlist_name) -> NavidromePlaylist | None:
        """Get playlist by name or return None."""
        url = f"{self.navidrome_url}/rest/getPlaylists"
        response = requests.get(url, params=self.params)
        if response.status_code == 200:
            playlists = response.json().get('subsonic-response', {}).get('playlists', {}).get('playlist', [])
            for playlist in playlists:
                if playlist['name'].lower() == playlist_name.lower():
                    return NavidromePlaylist(
                        _id=playlist['id'],
                        name=playlist['name'],
                        tracks=[]
                    )
        return None

    def create_playlist(self, playlist_name) -> NavidromePlaylist | None:
        """Create a new playlist in Navidrome."""
        url = f"{self.navidrome_url}/rest/createPlaylist"
        params = {
            **self.params,
            'name': playlist_name,
            'public': 'true',
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            playlist_id = response.json()['subsonic-response']['playlist']['id']
            print(f'Created playlist {playlist_name} with ID {playlist_id}')

            return NavidromePlaylist(
                _id=playlist_id,
                name=playlist_name,
            )
        else:
            print(f'Failed to create playlist {playlist_name}: {response.content}')
            return None

    def get_or_create_playlist(self, playlist_name) -> str | None:
        """Create or update a playlist and return its ID."""
        playlist = self.get_playlist_or_none(playlist_name)
        if playlist:
            print(f'Playlist "{playlist_name}" already exists with ID {playlist._id}.')
            return playlist
        else:
            print(f'Creating new playlist: {playlist_name}')
            return self.create_playlist(playlist_name)

    def update_playlist(self, playlist: NavidromePlaylist):
        self.clear_playlist(playlist)
        self.add_tracks_to_playlist(playlist)

    def clear_playlist(self, playlist: NavidromePlaylist):
        url = f"{self.navidrome_url}/rest/updatePlaylist"
        params = {
            **self.params,
            'playlistId': playlist.id,
            'songId': [],
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            print(f'Successfully cleared all tracks from playlist {playlist.name}.')
        else:
            print(f'Failed to clear playlist {playlist.name}: {response.content}')

    def add_tracks_to_playlist(self, playlist: NavidromePlaylist):
        if not playlist.tracks:
            print(f'No tracks to add to playlist "{playlist.name}".')
            return

        url = f"{self.navidrome_url}/rest/updatePlaylist"
        track_ids = [track._id for track in playlist.tracks]
        params = {**self.params, 'playlistId': playlist._id, 'songId': track_ids}

        response = requests.get(url, params=params)
        if response.status_code == 200:
            print(f'Successfully added {len(track_ids)} tracks to playlist "{playlist.name}".')
        else:
            print(f'Failed to add tracks to playlist "{playlist.name}": {response.content}')

    def get_track_or_none(self, artist_name: str, track_title: str) -> NavidromeTrack | None:
        """Search for a track in Navidrome by artist and track name, return a NavidromeTrack dataclass."""
        url = f"{self.navidrome_url}/rest/search3"
        params = {**self.params, 'query': f'{artist_name} {track_title}'}

        response = requests.get(url, params=params)
        if response.status_code == 200:

            search_result = response.json().get('subsonic-response', {}).get('song', [])
            if search_result:
                track = search_result[0]
                artist = NavidromeArtist(_id=track['artistId'], name=track['artist'])
                album = NavidromeAlbum(_id=track['albumId'], artist=artist)

                return NavidromeTrack(_id=track['id'], title=track['title'], album=album)

        return None

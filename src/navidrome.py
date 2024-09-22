import hashlib
import random
import string
import requests
import logging
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
        logging.debug("Initializing NavidromeService...")
        self.navidrome_url = navidrome_url
        self.username = username
        self.password = password
        logging.debug(f"Navidrome URL: {self.navidrome_url}, Username: {self.username}")

    def generate_salt(self, length=48):
        salt = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
        logging.debug(f"Generated salt: {salt}")
        return salt

    def generate_token(self, salt):
        token_string = self.password + salt
        token = hashlib.md5(token_string.encode("utf-8")).hexdigest()
        logging.debug(f"Generated token with salt '{salt}': {token}")
        return token

    @property
    def params(self):
        salt = self.generate_salt()
        params = {
            "u": self.username,
            "t": self.generate_token(salt),
            "s": salt,
            "v": "1.16.1",
            "c": "playlistarr",
            "f": "json",
        }
        logging.debug(f"Generated request parameters: {params}")
        return params

    @property
    def artists(self):
        url = f"{self.navidrome_url}/rest/getArtists"
        logging.debug(f"Fetching artists from Navidrome: {url}")
        response = requests.get(url, params=self.params)
        artists = []
        if response.status_code == 200:
            raw_indexes = (
                response.json()
                .get("subsonic-response", {})
                .get("artists", {})
                .get("index", [])
            )
            logging.debug(f"Raw artist data from Navidrome: {raw_indexes}")
            for raw_index in raw_indexes:
                for raw_artist in raw_index["artist"]:
                    artists.append(
                        NavidromeArtist(_id=raw_artist["id"], name=raw_artist["name"])
                    )
            logging.info(f"Fetched {len(artists)} artists from Navidrome.")
        else:
            logging.error(f"Failed to fetch artists from Navidrome: {response.content}")

        return artists

    def get_playlist_or_none(self, playlist_name) -> NavidromePlaylist | None:
        url = f"{self.navidrome_url}/rest/getPlaylists"
        logging.debug(f"Fetching playlist '{playlist_name}' from Navidrome: {url}")
        response = requests.get(url, params=self.params)
        if response.status_code == 200:
            playlists = (
                response.json()
                .get("subsonic-response", {})
                .get("playlists", {})
                .get("playlist", [])
            )
            logging.debug(f"Raw playlists data: {playlists}")
            for playlist in playlists:
                if playlist["name"].lower() == playlist_name.lower():
                    logging.info(
                        f"Found playlist '{playlist_name}' with ID {playlist['id']}"
                    )
                    return NavidromePlaylist(
                        _id=playlist["id"], name=playlist["name"], tracks=[]
                    )
        else:
            logging.error(f"Failed to fetch playlists: {response.content}")
        return None

    def create_playlist(self, playlist_name) -> NavidromePlaylist | None:
        url = f"{self.navidrome_url}/rest/createPlaylist"
        params = {
            **self.params,
            "name": playlist_name,
            "public": "true",
        }

        logging.debug(f"Creating playlist '{playlist_name}' with params: {params}")
        response = requests.get(url, params=params)
        if response.status_code == 200:
            playlist_id = response.json()["subsonic-response"]["playlist"]["id"]
            logging.info(f"Created playlist '{playlist_name}' with ID {playlist_id}")

            return NavidromePlaylist(
                _id=playlist_id,
                name=playlist_name,
            )
        else:
            logging.error(
                f"Failed to create playlist '{playlist_name}': {response.content}"
            )
            return None

    def get_or_create_playlist(self, playlist_name) -> str | None:
        playlist = self.get_playlist_or_none(playlist_name)
        if playlist:
            logging.info(
                f'Playlist "{playlist_name}" already exists with ID {playlist._id}.'
            )
            return playlist
        else:
            logging.info(f"Creating new playlist: {playlist_name}")
            return self.create_playlist(playlist_name)

    def update_playlist(self, playlist: NavidromePlaylist):
        logging.debug(f"Updating playlist '{playlist.name}'")
        self.clear_playlist(playlist)
        self.add_tracks_to_playlist(playlist)

    def clear_playlist(self, playlist: NavidromePlaylist):
        url = f"{self.navidrome_url}/rest/updatePlaylist"
        params = {
            **self.params,
            "playlistId": playlist._id,
            "songId": [],
        }

        logging.debug(f"Clearing playlist '{playlist.name}' with params: {params}")
        response = requests.get(url, params=params)
        if response.status_code == 200:
            logging.info(
                f"Successfully cleared all tracks from playlist '{playlist.name}'."
            )
        else:
            logging.error(
                f"Failed to clear playlist '{playlist.name}': {response.content}"
            )

    def add_tracks_to_playlist(self, playlist: NavidromePlaylist):
        if not playlist.tracks:
            logging.info(f'No tracks to add to playlist "{playlist.name}".')
            return

        url = f"{self.navidrome_url}/rest/updatePlaylist"
        track_ids = [track._id for track in playlist.tracks]
        params = {**self.params, "playlistId": playlist._id, "songId": track_ids}

        logging.debug(
            f"Adding tracks to playlist '{playlist.name}' with params: {params}"
        )
        response = requests.get(url, params=params)
        if response.status_code == 200:
            logging.info(
                f'Successfully added {len(track_ids)} tracks to playlist "{playlist.name}".'
            )
        else:
            logging.error(
                f'Failed to add tracks to playlist "{playlist.name}": {response.content}'
            )

    def get_track_or_none(
        self, artist_name: str, track_title: str
    ) -> NavidromeTrack | None:
        url = f"{self.navidrome_url}/rest/search3"
        params = {**self.params, "query": f"{artist_name} {track_title}"}

        logging.debug(
            f"Searching for track '{track_title}' by '{artist_name}' with params: {params}"
        )
        response = requests.get(url, params=params)
        if response.status_code == 200:
            search_result = response.json().get("subsonic-response", {}).get("song", [])
            logging.debug(f"Search result for track: {search_result}")
            if search_result:
                track = search_result[0]
                artist = NavidromeArtist(_id=track["artistId"], name=track["artist"])
                album = NavidromeAlbum(_id=track["albumId"], artist=artist)

                return NavidromeTrack(
                    _id=track["id"], title=track["title"], album=album
                )
        else:
            logging.error(
                f"Failed to search for track '{track_title}' by '{artist_name}': {response.content}"
            )
        return None

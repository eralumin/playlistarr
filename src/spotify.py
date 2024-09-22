import base64
import logging
import requests
from dataclasses import dataclass


@dataclass
class SpotifyArtist:
    _id: str
    name: str

    def __str__(self):
        return f"SpotifyArtist(id='{self._id}', name='{self.name}')"


@dataclass
class SpotifyAlbum:
    _id: str
    title: str
    artist: SpotifyArtist

    def __str__(self):
        return (
            f"SpotifyAlbum(id='{self._id}', title='{self.title}', artist={self.artist})"
        )


@dataclass
class SpotifyTrack:
    _id: str
    title: str
    album: SpotifyAlbum

    def __str__(self):
        return (
            f"SpotifyTrack(id='{self._id}', title='{self.title}', album={self.album})"
        )


@dataclass
class SpotifyPlaylist:
    _id: str
    name: str
    tracks: list[SpotifyTrack]

    def __str__(self):
        track_count = len(self.tracks)
        return f"SpotifyPlaylist(id='{self._id}', name='{self.name}', tracks_count={track_count})"


class SpotifyService:
    def __init__(self, client_id, client_secret):
        logging.debug("Initializing SpotifyService...")
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = self._get_access_token()

    def _get_access_token(self):
        """Authenticate with Spotify API and get access token."""
        logging.info("Authenticating with Spotify API...")
        auth_url = "https://accounts.spotify.com/api/token"

        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")
        auth_header = {"Authorization": f"Basic {auth_base64}"}
        auth_data = {"grant_type": "client_credentials"}

        logging.debug(f"Requesting access token with client ID: {self.client_id}")
        response = requests.post(auth_url, headers=auth_header, data=auth_data)
        response.raise_for_status()

        token = response.json()["access_token"]
        logging.info("Successfully authenticated with Spotify API.")
        logging.debug(f"Access token: {token}")
        return token

    def _load_playlist_from_raw(self, raw_playlists):
        logging.debug("Loading playlists from raw data...")
        playlists = []
        for raw_playlist in raw_playlists.get("items", []):
            tracks = []

            tracks_url = raw_playlist["tracks"]["href"]
            logging.info(f'Fetching tracks for playlist: {raw_playlist["name"]}')
            response = requests.get(
                tracks_url, headers={"Authorization": f"Bearer {self.token}"}
            )
            response.raise_for_status()
            raw_tracks = response.json().get("items", [])
            logging.debug(
                f"Fetched {len(raw_tracks)} tracks for playlist '{raw_playlist['name']}'"
            )

            for raw_track_item in raw_tracks:
                raw_track = raw_track_item["track"]
                artist = SpotifyArtist(
                    _id=raw_track["artists"][0]["id"],
                    name=raw_track["artists"][0]["name"],
                )

                album = SpotifyAlbum(
                    _id=raw_track["album"]["id"],
                    title=raw_track["album"]["name"],
                    artist=artist,
                )

                tracks.append(
                    SpotifyTrack(
                        _id=raw_track["id"],
                        title=raw_track["name"],
                        album=album,
                    )
                )

            playlists.append(
                SpotifyPlaylist(
                    _id=raw_playlist["id"],
                    name=raw_playlist["name"],
                    tracks=tracks,
                )
            )

            logging.info(
                f'Playlist {raw_playlist["name"]} loaded with {len(tracks)} tracks.'
            )

        logging.debug(f"Total playlists loaded: {len(playlists)}")
        return playlists

    def get_categories(self, limit, excluded_categories):
        headers = {"Authorization": f"Bearer {self.token}"}
        fetched_categories = []
        processed_categories = set()

        logging.info("Fetching Spotify categories...")
        while len(fetched_categories) < limit:
            url = "https://api.spotify.com/v1/browse/categories"
            params = {"limit": limit, "offset": len(processed_categories)}
            logging.debug(
                f"Fetching categories with offset {len(processed_categories)}"
            )
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            categories = response.json().get("categories", {}).get("items", [])
            logging.debug(f"Fetched categories: {categories}")

            for category in categories:
                category_name = category["name"].lower()

                # Skip if the category is in excluded_categories or already processed
                if (
                    category_name in excluded_categories
                    or category_name in processed_categories
                ):
                    logging.debug(f"Skipping category: {category_name}")
                    continue

                fetched_categories.append(category)
                processed_categories.add(category_name)

                logging.info(f"Fetched category: {category_name}")

                if len(fetched_categories) >= limit:
                    break

            if len(categories) == 0:
                logging.debug("No more categories to fetch.")
                break

        logging.info(f"Total fetched categories: {len(fetched_categories)}")
        return fetched_categories

    def get_playlists_for_artist(self, artist_name, limit):
        logging.info(f"Searching for playlists for artist: {artist_name}")
        url = f"https://api.spotify.com/v1/search"
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {"q": artist_name, "type": "playlist", "limit": limit}

        logging.debug(
            f"Searching playlists for artist '{artist_name}' with limit {limit}"
        )
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        raw_playlists = response.json().get("playlists", {})
        logging.info(
            f'Fetched {len(raw_playlists.get("items", []))} playlists for artist {artist_name}.'
        )
        logging.debug(f"Raw playlist data: {raw_playlists}")
        return self._load_playlist_from_raw(raw_playlists)

    def get_playlists_for_category(self, category_id, limit):
        logging.info(f"Fetching playlists for category: {category_id}")
        url = f"https://api.spotify.com/v1/browse/categories/{category_id}/playlists"
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {"limit": limit}

        logging.debug(
            f"Fetching playlists for category '{category_id}' with limit {limit}"
        )
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        raw_playlists = response.json().get("playlists", {})
        logging.info(
            f'Fetched {len(raw_playlists.get("items", []))} playlists for category {category_id}.'
        )
        logging.debug(f"Raw playlist data: {raw_playlists}")
        return self._load_playlist_from_raw(raw_playlists)

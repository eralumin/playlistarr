import requests
import logging

from dataclasses import dataclass
from enum import Enum


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AlbumType(Enum):
    ALBUM = "Album"
    EP = "EP"
    SINGLE = "Single"

@dataclass
class LidarrArtist:
    name: str
    is_monitored: bool

@dataclass
class LidarrAlbum:
    artist: LidarrArtist
    _id: str
    title: str

    _type: AlbumType | None
    is_monitored: bool
    root_folder: str | None

    @property
    def folder(self):
        if self.root_folder:
            return f'{self.root_folder}/{self.artist.name}'

class LidarrTrack:
    title: str
    album: LidarrAlbum

class LidarrService:
    def __init__(self, lidarr_url, api_key):
        self.lidarr_url = lidarr_url
        self.api_key = api_key
        self.headers = {'X-Api-Key': self.api_key}

    def get_profile_id_by_name(self, profiles, name):
        for profile in profiles:
            if profile['name'].lower() == name.lower():
                return profile['id']
        return None

    @property
    def quality_profiles(self):
        url = f'{self.lidarr_url}/api/v1/qualityprofile'
        response = requests.get(url, headers=self.headers)
        return response.json()

    @property
    def metadata_profiles(self):
        url = f'{self.lidarr_url}/api/v1/metadataprofile'
        response = requests.get(url, headers=self.headers)
        return response.json()

    def get_root_folder_or_none(self):
        url = f'{self.lidarr_url}/api/v1/rootfolder'
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            root_folders = response.json()
            if len(root_folders) > 0:
                return root_folders[0]['path']

        logging.warning("No root folder found or request failed.")
        return None

    def get_artist_or_none(self, artist_name):
        url = f'{self.lidarr_url}/api/v1/artist/lookup?term={artist_name}'
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            raw_artist = response.json()[0]
            if raw_artist:
                return LidarrArtist(
                    name=raw_artist["artistName"],
                    is_monitored=raw_artist["monitored"],
                )
        logging.warning(f"Artist {artist_name} not found.")
        return None

    def get_artist_discography(self, artist_name):
        artist_albums_url = f'{self.lidarr_url}/api/v1/artist/lookup?term={artist_name}'
        response = requests.get(artist_albums_url, headers=self.headers)

        if response.status_code != 200:
            logging.warning(f"Failed to fetch albums for artist {artist_name}.")
            return []

        artist_data = response.json()
        if not artist_data:
            logging.warning(f"No albums found for artist {artist_name}.")
            return []

        artist = self.get_artist_or_none(artist_name)
        if not artist:
            logging.warning(f"Artist {artist_name} not found.")
            return []

        discography = []
        for raw_album in artist_data:
            raw_album_type = raw_album.get('albumType', '').lower()

            match raw_album_type:
                case 'album':
                    album_type = AlbumType.ALBUM
                case 'ep':
                    album_type = AlbumType.EP
                case 'single':
                    album_type = AlbumType.SINGLE
                case _:
                    logging.info(f"Skipping album {raw_album['title']} as it is of type {raw_album_type}.")
                    continue

            album = LidarrAlbum(
                artist=artist,
                _id=raw_album['id'],
                title=raw_album['title'],
                _type=album_type,
                is_monitored=raw_album['monitored'],
                root_folder=self.get_root_folder_or_none()
            )
            discography.append(album)

        logging.info(f"Found {len(discography)} albums/EPs/singles for artist {artist_name}.")
        return discography

    def get_album_tracks(self, album):
        album_tracks_url = f'{self.lidarr_url}/api/v1/album/{album._id}'
        track_response = requests.get(album_tracks_url, headers=self.headers)

        album_tracks = []
        if track_response.status_code == 200:
            raw_album_tracks = track_response.json().get('tracks', [])

            for raw_track in raw_album_tracks:
                album_tracks.append(
                    LidarrTrack(
                        title=raw_track['title'],
                        album=album,
                    )
                )
        else:
            logging.warning(f"Failed to fetch tracks for album {album.title}.")

        return album_tracks

    def get_album_or_none(self, album_title, artist):
        url = f'{self.lidarr_url}/api/v1/album/lookup?term={album_title} {artist.name}'
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            raw_album = response.json()[0]

            return LidarrAlbum(
                artist=artist,
                title=album_title,
                _id=raw_album['foreignAlbumId'],
                is_monitored=raw_album['monitored'],
                root_folder=self.get_root_folder_or_none(),
            )

        logging.warning(f"Album {album_title} by {artist.name} not found.")
        return None

    def find_album_id_by_track(self, track_title, artist_name):
        discography = self.get_artist_discography(artist_name)
        if not discography:
            logging.warning(f"No discography found for artist {artist_name}.")
            return None

        for album in discography:
            logging.info(f"Checking album: {album.title} ({album._type.value})")

            album_tracks = self.get_album_tracks(album)
            for track in album_tracks:
                if track_title.lower() in track['title'].lower():
                    logging.info(f"Track '{track_title}' found in album '{album.title}'.")
                    return album._id

        logging.warning(f"Track '{track_title}' by '{artist_name}' not found in any album, EP, or single.")
        return None

    def add_album(self, album, quality_profile_id, metadata_profile_id):
        add_url = f'{self.lidarr_url}/api/v1/album'
        payload = {
            'foreignAlbumId': album._id,
            'monitored': album.is_monitored,
            'qualityProfileId': quality_profile_id,
            'metadataProfileId': metadata_profile_id,
            'rootFolderPath': album.folder,
        }

        response = requests.post(add_url, json=payload, headers=self.headers)
        if response.status_code == 201:
            logging.info(f'Album {album.title} by {album.artist.name} added successfully.')
        else:
            logging.error(f'Failed to add album: {response.content}')

    def monitor_album(self, album):
        logging.info(f'Album {album.title} by {album.artist.name} exists but is not monitored. Monitoring it now...')

        url = f'{self.lidarr_url}/api/v1/album'
        payload = {'monitored': True}

        response = requests.put(url, json=payload, headers=self.headers)
        if response.status_code == 202:
            logging.info(f'Album {album.title} is now being monitored.')
        else:
            logging.error(f'Failed to update monitoring: {response.content}')

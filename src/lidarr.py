import requests

from dataclasses import dataclass


@dataclass
class LidarrArtist:
    name: str
    is_monitored: bool

@dataclass
class LidarrAlbum:
    artist: LidarrArtist

    _id: str
    title: str

    is_monitored: bool

    root_folder: str | None

    @property
    def folder(self):
        if self.root_folder:
            return f'{self.root_folder}/{self.artist.name}'

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

        return None

    def get_artist_or_none(self, artist_name):
        url = f'{self.lidarr_url}/api/v1/artist/lookup?term={artist_name}'
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            raw_artist = response.json()[0]
            if raw_artist:
                return LidarrArtist(
                    name=raw_artist["name"],
                    is_monitored=raw_artist["monitored"],
                )

        return None

    def get_album_or_none(self, album_title, artist):
        url = f'{self.lidarr_url}/api/v1/album/lookup?term={album_title} {artist.name}'
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            raw_album = response.json()[0]

            return LidarrAlbum(
                artist=artist,
                title=album_title,
                _id = raw_album['foreignAlbumId'],
                is_monitored=raw_album['monitored'],
                root_folder=self.get_root_folder_or_none(),
            )

        return None

    def find_album_id_by_track(self, track_name, artist_name):
        """Return the foreignAlbumId for an album by searching for the track and artist name."""
        url = f'{self.lidarr_url}/api/v1/track/lookup?term={track_name} {artist_name}'
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            tracks = response.json()
            if tracks:
                album = tracks[0].get('album')
                if album:
                    return album.get('foreignAlbumId')

        return None

    def add_album(self, album, quality_profile_id, metadata_profile_id):
        add_url = f'{self.lidarr_url}/api/v1/album'
        payload = {
            'foreignAlbumId': album.id,
            'monitored': album.is_monitored,
            'qualityProfileId': quality_profile_id,
            'metadataProfileId': metadata_profile_id,
            'rootFolderPath': album.folder,
        }

        response = requests.post(add_url, json=payload, headers=self.headers)
        if response.status_code == 201:
            print(f'Album {album.title} by {album.artist.name} added successfully.')
        else:
            print(f'Failed to add album: {response.content}')

    def monitor_album(self, album):
        print(f'Album {album.title} by {album.artist.name} exists but is not monitored. Monitoring it now...')

        url = f'{self.lidarr_url}/api/v1/album'
        payload = {'monitored': True}

        response = requests.put(url, json=payload, headers=self.headers)
        if response.status_code == 202:
            print(f'Album {album.title} is now being monitored.')
        else:
            print(f'Failed to update monitoring: {response.content}')

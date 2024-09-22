import requests
import logging
from dataclasses import dataclass
from musicbrainz import MusicBrainzService


@dataclass
class LidarrArtist:
    name: str
    disambiguation: str
    root_folder: str
    is_monitored: bool

    @property
    def foreign_id(self):
        mb = MusicBrainzService()
        logging.debug(f"Fetching foreign ID for artist: {self.name}")
        foreign_id = mb.get_artist_id(self.name)
        logging.debug(f"Foreign ID for artist '{self.name}': {foreign_id}")
        return foreign_id

    @property
    def folder(self):
        if self.root_folder:
            folder_path = f"{self.root_folder}/{self.name} {self.disambiguation}"
            logging.debug(f"Artist folder path: {folder_path}")
            return folder_path


@dataclass
class LidarrAlbum:
    artist: LidarrArtist
    title: str
    is_monitored: bool

    @property
    def foreign_id(self):
        mb = MusicBrainzService()
        logging.debug(
            f"Fetching foreign ID for album '{self.title}' by artist '{self.artist.name}'"
        )
        foreign_id = mb.get_album_id(self.title, self.artist.name)
        logging.debug(f"Foreign ID for album '{self.title}': {foreign_id}")
        return foreign_id


@dataclass
class LidarrQualityProfile:
    _id: int
    name: str


@dataclass
class LidarrMetadataProfile:
    _id: int
    name: str


class LidarrService:
    def __init__(self, lidarr_url, api_key):
        self.lidarr_url = lidarr_url
        self.api_key = api_key
        self.headers = {"X-Api-Key": self.api_key}

    @property
    def quality_profiles(self):
        url = f"{self.lidarr_url}/api/v1/qualityprofile"
        try:
            logging.debug("Fetching quality profiles from Lidarr...")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            raw_quality_profiles = response.json()

            quality_profiles = []
            for raw_quality_profile in raw_quality_profiles:
                quality_profiles.append(
                    LidarrQualityProfile(
                        _id=raw_quality_profile["id"],
                        name=raw_quality_profile["name"],
                    )
                )
            logging.info(f"Fetched {len(quality_profiles)} quality profiles.")
            return quality_profiles
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching quality profiles: {e}")
            return []

    @property
    def metadata_profiles(self):
        url = f"{self.lidarr_url}/api/v1/metadataprofile"
        try:
            logging.debug("Fetching metadata profiles from Lidarr...")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            raw_metadata_profiles = response.json()

            metadata_profiles = []
            for raw_metadata_profile in raw_metadata_profiles:
                metadata_profiles.append(
                    LidarrMetadataProfile(
                        _id=raw_metadata_profile["id"],
                        name=raw_metadata_profile["name"],
                    )
                )
            logging.info(f"Fetched {len(metadata_profiles)} metadata profiles.")
            return metadata_profiles
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching metadata profiles: {e}")
            return []

    def get_quality_profile_or_none(self, name):
        logging.info(f"Searching for quality profile: {name}")
        quality_profile = next(
            (profile for profile in self.quality_profiles if profile.name == name), None
        )

        if quality_profile:
            logging.info(
                f"Found quality profile '{name}' with ID: {quality_profile._id}"
            )
        else:
            logging.warning(f"Quality profile '{name}' not found.")

        return quality_profile

    def get_metadata_profile_or_none(self, name):
        logging.info(f"Searching for metadata profile: {name}")
        metadata_profile = next(
            (profile for profile in self.metadata_profiles if profile.name == name),
            None,
        )

        if metadata_profile:
            logging.info(
                f"Found metadata profile '{name}' with ID: {metadata_profile._id}"
            )
        else:
            logging.warning(f"Metadata profile '{name}' not found.")

        return metadata_profile

    def get_root_folder_or_none(self):
        url = f"{self.lidarr_url}/api/v1/rootfolder"
        logging.debug("Fetching root folders from Lidarr...")
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            root_folders = response.json()
            if len(root_folders) > 0:
                logging.debug(f"Root folder found: {root_folders[0]['path']}")
                return root_folders[0]["path"]

        logging.warning("No root folder found or request failed.")
        return None

    def get_artist_or_none(self, artist_name):
        url = f"{self.lidarr_url}/api/v1/artist/lookup?term={artist_name}"
        logging.debug(f"Fetching artist '{artist_name}' from Lidarr...")
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            raw_artist = response.json()[0]
            if raw_artist:
                logging.debug(f"Artist found: {raw_artist}")
                return LidarrArtist(
                    name=raw_artist["artistName"],
                    disambiguation=raw_artist["disambiguation"],
                    is_monitored=raw_artist["monitored"],
                    root_folder=self.get_root_folder_or_none(),
                )
        logging.warning(f"Artist '{artist_name}' not found.")
        return None

    def get_album_or_none(self, album_title, artist):
        url = f"{self.lidarr_url}/api/v1/album/lookup?term={album_title} {artist.name}"
        logging.debug(
            f"Fetching album '{album_title}' by artist '{artist.name}' from Lidarr..."
        )
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            raw_album = response.json()[0]
            logging.debug(f"Album found: {raw_album}")
            return LidarrAlbum(
                artist=artist,
                title=album_title,
                foreign_id=raw_album["foreignAlbumId"],
                is_monitored=raw_album["monitored"],
            )

        logging.warning(f"Album '{album_title}' by '{artist.name}' not found.")
        return None

    def add_album(self, album, quality_profile, metadata_profile):
        add_url = f"{self.lidarr_url}/api/v1/album"
        payload = {
            "foreignAlbumId": album.foreign_id,
            "monitored": album.is_monitored,
            "artist": {
                "foreignArtistId": album.artist.foreign_id,
                "qualityProfileId": quality_profile._id,
                "metadataProfileId": metadata_profile._id,
                "rootFolderPath": album.artist.folder,
            },
        }

        logging.debug(f"Adding album with payload: {payload}")
        response = requests.post(add_url, json=payload, headers=self.headers)
        if response.status_code == 201:
            logging.info(
                f"Album {album.title} by {album.artist.name} added successfully."
            )
        else:
            logging.error(f"Failed to add album: {response.content}")

    def monitor_album(self, album):
        logging.info(
            f"Album {album.title} by {album.artist.name} exists but is not monitored. Monitoring it now..."
        )

        url = f"{self.lidarr_url}/api/v1/album"
        payload = {"monitored": True}

        logging.debug(f"Monitoring album '{album.title}' with payload: {payload}")
        response = requests.put(url, json=payload, headers=self.headers)
        if response.status_code == 202:
            logging.info(f"Album {album.title} is now being monitored.")
        else:
            logging.error(f"Failed to update monitoring: {response.content}")

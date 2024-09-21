import requests

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
            artist_data = response.json()
            if artist_data:
                return artist_data[0]

        return None

    def is_artist_monitored(self, artist_name):
        artist_data = self.get_artist_or_none(artist_name)

        return artist_data and artist_data['monitored']

    def get_album_or_none(self, album_title, artist_name):
        """Fetch the album details from Lidarr."""
        url = f'{self.lidarr_url}/api/v1/album/lookup?term={album_title} {artist_name}'
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        return None

    def add_album(self, album_data, quality_profile_id, metadata_profile_id):
        """Add a new album to Lidarr."""
        album_id = album_data[0]['foreignAlbumId']
        artist_name = album_data[0]['artist']['artistName']

        root_folder_path = self.get_root_folder_or_none()
        if root_folder_path:
            root_folder_path = f'{root_folder_path}/{artist_name}'

        add_url = f'{self.lidarr_url}/api/v1/album'
        payload = {
            'foreignAlbumId': album_id,
            'monitored': True,
            'qualityProfileId': quality_profile_id,
            'metadataProfileId': metadata_profile_id,
            'rootFolderPath': root_folder_path,
        }

        response = requests.post(add_url, json=payload, headers=self.headers)
        if response.status_code == 201:
            print(f'Album {album_data[0]["title"]} by {album_data[0]["artist"]["artistName"]} added successfully.')
        else:
            print(f'Failed to add album: {response.content}')

    def monitor_album(self, album_data):
        print(f'Album {album_data[0]["title"]} by {album_data[0]["artist"]["artistName"]} exists but is not monitored. Monitoring it now...')

        url = f'{self.lidarr_url}/api/v1/album'
        payload = {'monitored': True}

        response = requests.put(url, json=payload, headers=self.headers)
        if response.status_code == 202:
            print(f'Album {album_data[0]["title"]} is now being monitored.')
        else:
            print(f'Failed to update monitoring: {response.content}')

    def add_or_monitor_album(self, album_title, artist_name, quality_profile_name, metadata_profile_name):
        quality_profile_id = self.get_profile_id_by_name(self.quality_profiles, quality_profile_name)
        metadata_profile_id = self.get_profile_id_by_name(self.metadata_profiles, metadata_profile_name)

        if quality_profile_id is None:
            print(f'Quality profile "{quality_profile_name}" not found!')
            return
        if metadata_profile_id is None:
            print(f'Metadata profile "{metadata_profile_name}" not found!')
            return

        album_data = self.get_album_or_none(album_title, artist_name)
        if album_data and len(album_data) > 0:
            if not album_data[0]['monitored']:
                self.monitor_album(album_data)
        else:
            print(f'Adding album {album_title} by {artist_name} to Lidarr.')
            self.add_album(album_data, quality_profile_id, metadata_profile_id)

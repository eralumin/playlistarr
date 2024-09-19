import requests

class SpotifyService:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = self._get_access_token()
    
    def _get_access_token(self):
        """Authenticate with Spotify API and get access token."""
        auth_url = 'https://accounts.spotify.com/api/token'
        auth_header = {
            'Authorization': 'Basic ' + (self.client_id + ':' + self.client_secret).encode('utf-8').decode('ascii')
        }
        auth_data = {'grant_type': 'client_credentials'}
        
        response = requests.post(auth_url, headers=auth_header, data=auth_data)
        response.raise_for_status()
        return response.json()['access_token']

    def fetch_playlists(self):
        """Fetch playlists from Spotify API."""
        url = 'https://api.spotify.com/v1/me/playlists'
        headers = {
            'Authorization': f'Bearer {self.token}'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()['items']

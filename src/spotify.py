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

    def get_categories(self, limit, excluded_categories):
        """
        Fetch categories from Spotify, ensuring that excluded categories are filtered out.
        The method will keep fetching categories until it reaches the exact number of non-excluded categories.
        """
        headers = {'Authorization': f'Bearer {self.token}'}
        fetched_categories = []
        processed_categories = set()

        while len(fetched_categories) < limit:
            url = 'https://api.spotify.com/v1/browse/categories'
            params = {'limit': 50, 'offset': len(processed_categories)}  # Fetching in batches of 50
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

                # Stop fetching when we reach the desired number of categories
                if len(fetched_categories) >= limit:
                    break

            # Break the loop if there are no more categories to process
            if len(categories) == 0:
                break

        return fetched_categories

    def get_playlists_for_artist(self, artist_name, limit):
        """Fetch playlists related to an artist from Spotify."""
        url = f'https://api.spotify.com/v1/search'
        headers = {'Authorization': f'Bearer {self.token}'}
        params = {
            'q': artist_name,
            'type': 'playlist',
            'limit': limit
        }
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get('playlists', {}).get('items', [])

    def get_playlists_for_category(self, category_id, limit):
        """Fetch playlists for a given category."""
        url = f'https://api.spotify.com/v1/browse/categories/{category_id}/playlists'
        headers = {'Authorization': f'Bearer {self.token}'}
        params = {'limit': limit}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get('playlists', {}).get('items', [])

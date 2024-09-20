class PlaylistManager:
    def __init__(self, spotify, lidarr, navidrome, artist_playlist_limit, category_playlist_limit, included_categories, excluded_categories, random_category_limit):
        self.spotify = spotify
        self.lidarr = lidarr
        self.navidrome = navidrome
        self.artist_playlist_limit = artist_playlist_limit
        self.category_playlist_limit = category_playlist_limit
        self.included_categories = [cat.lower() for cat in included_categories if cat]
        self.excluded_categories = [cat.lower() for cat in excluded_categories if cat]
        self.random_category_limit = random_category_limit

    def process_playlists(self, quality_profile_name, metadata_profile_name):
        """Process both artist and category playlists."""
        self.process_playlists_by_artists(quality_profile_name, metadata_profile_name)
        self.process_playlists_by_included_categories(quality_profile_name, metadata_profile_name)
        self.process_playlists_by_random_categories(quality_profile_name, metadata_profile_name)

    def process_playlists_by_artists(self, quality_profile_name, metadata_profile_name):
        """Fetch and process playlists for fully monitored artists."""
        for artist in self.navidrome.artists:
            artist_name = artist['name']

            if self.lidarr.is_artist_monitored(artist_name):
                print(f'Fetching playlists for fully monitored artist: {artist_name}')
                playlists = self.spotify.fetch_playlists_for_artist(artist_name, self.artist_playlist_limit)
                for playlist in playlists:
                    self.process_single_playlist(playlist, quality_profile_name, metadata_profile_name)
            else:
                print(f'Skipping artist {artist_name} because they are not fully monitored in Lidarr.')

    def process_playlists_by_included_categories(self, quality_profile_name, metadata_profile_name):
        """Process playlists for the included categories."""
        for included_category in self.included_categories:
            print(f'Fetching playlists for included category: {included_category}')
            playlists = self.spotify.get_playlists_for_category(included_category, self.category_playlist_limit)
            for playlist in playlists:
                self.process_single_playlist(playlist, quality_profile_name, metadata_profile_name)

    def process_playlists_by_random_categories(self, quality_profile_name, metadata_profile_name):
        """Fetch and process random categories."""
        categories = self.spotify.get_categories(limit=self.random_category_limit, excluded_categories=self.excluded_categories)
        for category in categories:
            print(f'Fetching playlists for random category: {category["name"]}')
            playlists = self.spotify.get_playlists_for_category(category['id'], self.category_playlist_limit)
            for playlist in playlists:
                self.process_single_playlist(playlist, quality_profile_name, metadata_profile_name)

    def process_single_playlist(self, playlist, quality_profile_name, metadata_profile_name):
        """Process a single playlist, create or update in Navidrome."""
        print(f'Processing playlist: {playlist["name"]}')
        playlist_tracks = []
        playlist_id = self.navidrome.create_or_update_playlist(playlist["name"])

        if playlist_id:
            playlist_tracks = self.process_tracks_in_playlist(playlist, quality_profile_name, metadata_profile_name)

            # Add tracks to Navidrome playlist if any tracks were found
            if playlist_tracks:
                self.navidrome.add_tracks_to_playlist(playlist_id, playlist_tracks)
            else:
                print(f'No matching tracks found for playlist {playlist["name"]} in Navidrome.')

    def process_tracks_in_playlist(self, playlist, quality_profile_name, metadata_profile_name):
        """Process the tracks within a playlist."""
        playlist_tracks = []
        for track in playlist['tracks']['items']:
            track_name = track['track']['name']
            artist_name = track['track']['artists'][0]['name']
            album_title = track['track']['album']['name']

            self.lidarr.add_or_monitor_album(album_title, artist_name, quality_profile_name, metadata_profile_name)

            track_id = self.navidrome.search_track_in_navidrome(artist_name, track_name)
            if track_id:
                playlist_tracks.append(track_id)

        return playlist_tracks

class PlaylistManager:
    def __init__(self, spotify_service, lidarr_service, navidrome_service):
        self.spotify_service = spotify_service
        self.lidarr_service = lidarr_service
        self.navidrome_service = navidrome_service

    def process_playlists(self, quality_profile, metadata_profile):
        """Process all Spotify playlists, add albums to Lidarr, and create Navidrome playlists."""
        playlists = self.spotify_service.fetch_playlists()

        for playlist in playlists:
            self.process_single_playlist(playlist, quality_profile, metadata_profile)

    def process_single_playlist(self, playlist, quality_profile, metadata_profile):
        """Process a single playlist: handle albums in Lidarr and tracks in Navidrome."""
        print(f'Processing playlist: {playlist["name"]}')
        playlist_tracks = []
        playlist_id = self.navidrome_service.create_playlist(playlist["name"])

        if playlist_id:
            playlist_tracks = self.process_tracks_in_playlist(playlist, quality_profile, metadata_profile)

            if playlist_tracks:
                self.navidrome_service.add_tracks_to_playlist(playlist_id, playlist_tracks)
            else:
                print(f'No matching tracks found for playlist {playlist["name"]} in Navidrome.')

    def process_tracks_in_playlist(self, playlist, quality_profile, metadata_profile):
        """Process the tracks within a playlist: handle albums and track IDs."""
        playlist_tracks = []
        for track in playlist['tracks']['items']:
            track_name = track['track']['name']
            artist_name = track['track']['artists'][0]['name']
            album_title = track['track']['album']['name']

            self.handle_lidarr_album(album_title, artist_name, quality_profile, metadata_profile)

            track_id = self.handle_navidrome_track(artist_name, track_name)
            if track_id:
                playlist_tracks.append(track_id)
        return playlist_tracks

    def handle_lidarr_album(self, album_title, artist_name, quality_profile, metadata_profile):
        """Check and add or monitor an album in Lidarr."""
        print(f'Checking album: {album_title} by {artist_name}')
        self.lidarr_service.add_or_monitor_album(album_title, artist_name, quality_profile, metadata_profile)

    def handle_navidrome_track(self, artist_name, track_name):
        """Find and return the track ID from Navidrome."""
        track_id = self.navidrome_service.search_track_in_navidrome(artist_name, track_name)
        if track_id:
            print(f'Found track {track_name} by {artist_name} in Navidrome with ID {track_id}')
        else:
            print(f'Could not find track {track_name} by {artist_name} in Navidrome.')
        return track_id

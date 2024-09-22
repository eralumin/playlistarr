import logging
import sys
from lidarr import LidarrAlbum, LidarrArtist
from navidrome import NavidromePlaylist, NavidromeTrack
from spotify import SpotifyPlaylist


class PlaylistManager:
    def __init__(
        self,
        spotify,
        lidarr,
        navidrome,
        artist_playlist_limit,
        category_playlist_limit,
        included_categories,
        excluded_categories,
        random_category_limit,
        quality_profile_name,
        metadata_profile_name,
    ):
        logging.debug("Initializing PlaylistManager...")
        self.spotify = spotify
        self.lidarr = lidarr
        self.navidrome = navidrome
        self.artist_playlist_limit = artist_playlist_limit
        self.category_playlist_limit = category_playlist_limit
        self.included_categories = [cat.lower() for cat in included_categories if cat]
        self.excluded_categories = [cat.lower() for cat in excluded_categories if cat]
        self.random_category_limit = random_category_limit

        logging.debug(f"Included categories: {self.included_categories}")
        logging.debug(f"Excluded categories: {self.excluded_categories}")

        # Fetch quality profile
        logging.info(f"Looking for quality profile: '{quality_profile_name}'")
        self.quality_profile = self.lidarr.get_quality_profile_or_none(
            quality_profile_name
        )

        if not self.quality_profile:
            logging.error(
                f"Quality profile '{quality_profile_name}' not found. Exiting."
            )
            sys.exit(1)

        logging.info(
            f"Quality profile '{quality_profile_name}' found with ID: {self.quality_profile._id}"
        )

        # Fetch metadata profile
        logging.info(f"Looking for metadata profile: '{metadata_profile_name}'")
        self.metadata_profile = self.lidarr.get_metadata_profile_or_none(
            metadata_profile_name
        )

        if not self.metadata_profile:
            logging.error(
                f"Metadata profile '{metadata_profile_name}' not found. Exiting."
            )
            sys.exit(1)

        logging.info(
            f"Metadata profile '{metadata_profile_name}' found with ID: {self.metadata_profile._id}"
        )

    def process(self):
        logging.debug(
            "Starting to process playlists by artists, categories, and random categories."
        )
        self.process_playlists_by_artists()
        self.process_playlists_by_included_categories()
        self.process_playlists_by_random_categories()

    def process_playlists_by_artists(self):
        logging.debug("Processing playlists by artists.")
        for artist in self.navidrome.artists:
            lidarr_artist = self.lidarr.get_artist_or_none(artist.name)
            logging.debug(f"Fetched Lidarr artist: {lidarr_artist}")
            if lidarr_artist and lidarr_artist.is_monitored:
                logging.info(
                    f"Fetching playlists for fully monitored artist: {artist.name}"
                )
                spotify_playlists = self.spotify.get_playlists_for_artist(
                    artist.name, self.artist_playlist_limit
                )
                logging.debug(
                    f"Fetched Spotify playlists for artist '{artist.name}': {spotify_playlists}"
                )
                self.process_playlists(spotify_playlists)
            else:
                logging.info(
                    f"Skipping artist {artist.name} because they are not fully monitored in Lidarr."
                )

    def process_playlists_by_included_categories(self):
        logging.debug("Processing playlists by included categories.")
        for spotify_included_category in self.included_categories:
            logging.info(
                f"Fetching playlists for included category: {spotify_included_category}"
            )
            spotify_playlists = self.spotify.get_playlists_for_category(
                spotify_included_category, self.category_playlist_limit
            )
            logging.debug(
                f"Fetched Spotify playlists for category '{spotify_included_category}': {spotify_playlists}"
            )
            self.process_playlists(spotify_playlists)

    def process_playlists_by_random_categories(self):
        logging.debug("Processing playlists by random categories.")
        spotify_categories = self.spotify.get_categories(
            limit=self.random_category_limit,
            excluded_categories=self.excluded_categories,
        )
        logging.debug(f"Fetched Spotify categories: {spotify_categories}")
        for spotify_category in spotify_categories:
            logging.info(
                f'Fetching playlists for random category: {spotify_category["name"]}'
            )
            spotify_playlists = self.spotify.get_playlists_for_category(
                spotify_category["id"], self.category_playlist_limit
            )
            logging.debug(
                f"Fetched Spotify playlists for random category '{spotify_category['name']}': {spotify_playlists}"
            )
            self.process_playlists(spotify_playlists)

    def process_playlists(self, spotify_playlists: list[SpotifyPlaylist]):
        logging.debug(f"Processing {len(spotify_playlists)} playlists.")
        for spotify_playlist in spotify_playlists:
            self.process_playlist(spotify_playlist)

    def process_playlist(self, spotify_playlist: SpotifyPlaylist):
        logging.info(f"Processing playlist: {spotify_playlist.name}")

        navidrome_playlist = self.navidrome.get_or_create_playlist(
            spotify_playlist.name
        )
        logging.debug(f"Fetched or created Navidrome playlist: {navidrome_playlist}")
        navidrome_playlist.tracks = self.process_tracks_in_playlist(spotify_playlist)

        self.navidrome.update_playlist(navidrome_playlist)

    def process_tracks_in_playlist(self, spotify_playlist: SpotifyPlaylist):
        logging.debug(f"Processing tracks in playlist: {spotify_playlist.name}")
        navidrome_tracks = []
        for spotify_track in spotify_playlist.tracks:
            lidarr_artist = self.lidarr.get_artist_or_none(
                spotify_track.album.artist.name
            )
            logging.debug(
                f"Fetched Lidarr artist for track '{spotify_track.title}': {lidarr_artist}"
            )

            lidarr_album = None
            if not lidarr_artist:
                logging.error(
                    f"No matching artist found for track '{spotify_track.title}' by '{spotify_track.album.artist.name}' in Lidarr."
                )
                continue

            lidarr_album = self.lidarr.get_album_or_none(
                spotify_track.album.title, spotify_track.album.artist.name
            )

            if not lidarr_album:
                logging.info(
                    f"No matching local album found for track '{spotify_track.title}' by '{spotify_track.album.artist.name}' in Lidarr."
                )
                lidarr_album = LidarrAlbum(
                    artist=lidarr_artist,
                    title=spotify_track.album.title,
                    is_monitored=True,
                )

                self.lidarr.add_album(
                    lidarr_album, self.quality_profile, self.metadata_profile
                )
                logging.debug(f"Created Lidarr album: {lidarr_album}")

            self.lidarr.monitor_album(lidarr_album)

            navidrome_track = self.navidrome.get_track_or_none(
                spotify_track.album.artist.name, spotify_track.title
            )
            if navidrome_track:
                logging.debug(f"Adding Navidrome track: {navidrome_track.title}")
                navidrome_tracks.append(navidrome_track)

        return navidrome_tracks

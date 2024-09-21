import logging

from lidarr import LidarrAlbum, LidarrArtist
from navidrome import NavidromePlaylist, NavidromeTrack
from spotify import SpotifyPlaylist

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PlaylistManager:
    def __init__(self, spotify, lidarr, navidrome, musicbrainz, artist_playlist_limit, category_playlist_limit, included_categories, excluded_categories, random_category_limit, quality_profile_name, metadata_profile_name):
        self.spotify = spotify
        self.lidarr = lidarr
        self.navidrome = navidrome
        self.musicbrainz = musicbrainz
        self.artist_playlist_limit = artist_playlist_limit
        self.category_playlist_limit = category_playlist_limit
        self.included_categories = [cat.lower() for cat in included_categories if cat]
        self.excluded_categories = [cat.lower() for cat in excluded_categories if cat]
        self.random_category_limit = random_category_limit

        self.quality_profile_id = self.lidarr.get_profile_id_by_name(self.lidarr.quality_profiles, quality_profile_name)
        self.metadata_profile_id = self.lidarr.get_profile_id_by_name(self.lidarr.metadata_profiles, metadata_profile_name)

    def process(self):
        self.process_playlists_by_artists()
        self.process_playlists_by_included_categories()
        self.process_playlists_by_random_categories()

    def process_playlists_by_artists(self):
        for artist in self.navidrome.artists:
            lidarr_artist = self.lidarr.get_artist_or_none(artist.name)
            if lidarr_artist and lidarr_artist.is_monitored:
                logging.info(f'Fetching playlists for fully monitored artist: {artist.name}')
                spotify_playlists = self.spotify.get_playlists_for_artist(artist.name, self.artist_playlist_limit)

                self.process_playlists(spotify_playlists)
            else:
                logging.info(f'Skipping artist {artist.name} because they are not fully monitored in Lidarr.')

    def process_playlists_by_included_categories(self):
        for spotify_included_category in self.included_categories:
            logging.info(f'Fetching playlists for included category: {spotify_included_category}')
            spotify_playlists = self.spotify.get_playlists_for_category(spotify_included_category, self.category_playlist_limit)

            self.process_playlists(spotify_playlists)

    def process_playlists_by_random_categories(self):
        spotify_categories = self.spotify.get_categories(limit=self.random_category_limit, excluded_categories=self.excluded_categories)
        for spotify_category in spotify_categories:
            logging.info(f'Fetching playlists for random category: {spotify_category["name"]}')
            spotify_playlists = self.spotify.get_playlists_for_category(spotify_category['id'], self.category_playlist_limit)

            self.process_playlists(spotify_playlists)

    def process_playlists(self, spotify_playlists: list[SpotifyPlaylist]):
        for spotify_playlist in spotify_playlists:
            self.process_playlist(spotify_playlist)

    def process_playlist(self, spotify_playlist: SpotifyPlaylist):
        logging.info(f'Processing playlist: {spotify_playlist.name}')

        navidrome_playlist = self.navidrome.get_or_create_playlist(spotify_playlist.name)
        navidrome_playlist.tracks = self.process_tracks_in_playlist(spotify_playlist)

        self.navidrome.update_playlist(navidrome_playlist)

    def process_tracks_in_playlist(self, spotify_playlist: SpotifyPlaylist):
        navidrome_tracks = []
        for spotify_track in spotify_playlist.tracks:
            lidarr_artist = self.lidarr.get_artist_or_none(spotify_track.album.artist.name)
            lidarr_album = None
            if not lidarr_artist:
                logging.info(f"No matching artist found for track '{spotify_track.title}' by '{spotify_track.album.artist.name}' in Lidarr.")

                lidarr_album = self.lidarr.get_album_or_none(spotify_track.album.title, spotify_track.album.artist.name)
                if not lidarr_album:
                    logging.info(f"No matching album found for track '{spotify_track.title}' by '{spotify_track.album.artist.name}' in Lidarr.")

            if lidarr_album:
                self.lidarr.monitor_album(lidarr_album)
            else:
                lidarr_artist = LidarrArtist(
                    name=spotify_track.album.artist.name,
                    is_monitored=False,
                )
                lidarr_album = LidarrAlbum(
                    artist=lidarr_artist,
                    foreign_id=self.musicbrainz.get_album_id(spotify_track.album.title, spotify_track.album.artist.name),
                    title=spotify_track.album.title,
                    is_monitored=True,
                    root_folder=self.lidarr.get_root_folder_or_none(),
                )

            self.lidarr.add_album(lidarr_album, self.quality_profile_id, self.metadata_profile_id)

            navidrome_track = self.navidrome.get_track_or_none(spotify_track.album.artist.name, spotify_track.title)
            if navidrome_track:
                navidrome_tracks.append(navidrome_track)

        return navidrome_tracks

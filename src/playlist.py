from navidrome import NavidromePlaylist, NavidromeTrack
from spotify import SpotifyPlaylist

class PlaylistManager:
    def __init__(self, spotify, lidarr, navidrome, artist_playlist_limit, category_playlist_limit, included_categories, excluded_categories, random_category_limit, quality_profile_name, metadata_profile_name):
        self.spotify = spotify
        self.lidarr = lidarr
        self.navidrome = navidrome
        self.artist_playlist_limit = artist_playlist_limit
        self.category_playlist_limit = category_playlist_limit
        self.included_categories = [cat.lower() for cat in included_categories if cat]
        self.excluded_categories = [cat.lower() for cat in excluded_categories if cat]
        self.random_category_limit = random_category_limit

        self.quality_profile_name = quality_profile_name
        self.metadata_profile_name = metadata_profile_name

    def process(self):
        self.process_playlists_by_artists()
        self.process_playlists_by_included_categories()
        self.process_playlists_by_random_categories()

    def process_playlists_by_artists(self):
        for artist in self.navidrome.artists:
            lidarr_artist = self.lidarr.get_artist_or_none(artist.name)
            if lidarr_artist and lidarr_artist.is_monitored:
                print(f'Fetching playlists for fully monitored artist: {artist.name}')
                spotify_playlists = self.spotify.get_playlists_for_artist(artist.name, self.artist_playlist_limit)

                self.process_playlists(spotify_playlists)
            else:
                print(f'Skipping artist {artist.name} because they are not fully monitored in Lidarr.')

    def process_playlists_by_included_categories(self):
        for spotify_included_category in self.included_categories:
            print(f'Fetching playlists for included category: {spotify_included_category}')
            spotify_playlists = self.spotify.get_playlists_for_category(spotify_included_category, self.category_playlist_limit)

            self.process_playlists(spotify_playlists)

    def process_playlists_by_random_categories(self):
        spotify_categories = self.spotify.get_categories(limit=self.random_category_limit, excluded_categories=self.excluded_categories)
        for spotify_category in spotify_categories:
            print(f'Fetching playlists for random category: {spotify_category["name"]}')
            spotify_playlists = self.spotify.get_playlists_for_category(spotify_category['id'], self.category_playlist_limit)

            self.process_playlists(spotify_playlists)

    def process_playlists(self, spotify_playlists: list[SpotifyPlaylist]):
        for spotify_playlist in spotify_playlists:
            self.process_playlist(spotify_playlist)

    def process_playlist(self, spotify_playlist: SpotifyPlaylist):
        print(f'Processing playlist: {spotify_playlist.name}')

        navidrome_playlist = self.navidrome.get_or_create_playlist(spotify_playlist.name)
        navidrome_playlist.tracks = self.process_tracks_in_playlist(spotify_playlist)

        self.navidrome.update_playlist(navidrome_playlist)

    def process_tracks_in_playlist(self, spotify_playlist: SpotifyPlaylist):
        navidrome_playlist.tracks = []
        for spotify_track in spotify_playlist.tracks:
            lidarr_artist = self.lidarr.get_artist_or_none(spotify_track.album.artist.name)
            if not lidarr_artist:
                print(f"No matching artist found for track '{spotify_track.title}' by '{spotify_track.album.artist.name}' in Lidarr.")

                lidarr_album = self.lidarr.get_album_or_none(spotify_track.album.title, spotify_track.album.artist.name)
                if not lidarr_album:
                    print(f"No matching album found for track '{spotify_track.title}' by '{spotify_track.album.artist.name}' in Lidarr.")

            if lidarr_album:
                self.lidarr.monitor_album(lidarr_album)
            else:
                lidarr_album = self.lidarr.find_album_id_by_track(spotify_track.title, spotify_track.album.artist.name)
                self.lidarr.add_album(lidarr_album, quality_profile_id, metadata_profile_id)

            spotify_track = self.navidrome.get_track_or_none(spotify_track.artist.name, spotify_track.title)
            if spotify_track:
                navidrome_playlist.tracks.append(spotify_track)

        return navidrome_playlist

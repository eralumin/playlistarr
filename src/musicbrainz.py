import musicbrainzngs
import logging


class MusicBrainzService:
    def __init__(self):
        logging.debug("Initializing MusicBrainzService...")
        musicbrainzngs.set_useragent(
            "playlistarr", "1.0", "https://github.com/eralumin/playlistarr"
        )
        logging.debug("MusicBrainz user agent set successfully.")

    def get_album_id(self, album_title: str, artist_name: str) -> str | None:
        logging.debug(
            f"Searching for album '{album_title}' by artist '{artist_name}' in MusicBrainz."
        )
        try:
            result = musicbrainzngs.search_release_groups(
                artist=artist_name, release=album_title
            )
            logging.debug(f"Raw response from MusicBrainz for album search: {result}")

            album_id = result.get("release-group-list", [{}])[0].get("id")
            if album_id:
                logging.debug(
                    f"Found MusicBrainz ID for album '{album_title}': {album_id}"
                )
                return album_id
            else:
                logging.warning(
                    f"No matching MusicBrainz ID found for album '{album_title}' by '{artist_name}'."
                )
                return None
        except Exception as e:
            logging.error(
                f"Error fetching MusicBrainz ID for album '{album_title}' by '{artist_name}': {e}"
            )
            return None

    def get_artist_id(self, artist_name: str) -> str | None:
        logging.debug(f"Searching for artist '{artist_name}' in MusicBrainz.")
        try:
            result = musicbrainzngs.search_artists(artist=artist_name)
            logging.debug(f"Raw response from MusicBrainz for artist search: {result}")

            artist_id = result.get("artist-list", [{}])[0].get("id")
            if artist_id:
                logging.debug(
                    f"Found MusicBrainz ID for artist '{artist_name}': {artist_id}"
                )
                return artist_id
            else:
                logging.warning(
                    f"No matching MusicBrainz ID found for artist '{artist_name}'."
                )
                return None
        except Exception as e:
            logging.error(
                f"Error fetching MusicBrainz ID for artist '{artist_name}': {e}"
            )
            return None

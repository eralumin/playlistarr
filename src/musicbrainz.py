import musicbrainzngs
import logging

class MusicBrainzService:
    def __init__(self, ):
        musicbrainzngs.set_useragent("playlistarr", "1.0", "https://github.com/eralumin/playlistarr")
    
    def get_album_id(self, album_title: str, artist_name: str) -> str | None:
        try:
            result = musicbrainzngs.search_release_groups(artist=artist_name, release=album_title)

            album_id = result.get('release-group-list', [{}])[0].get('id')
            if album_id:
                return album_id
            else:
                logging.warning(f"No matching MusicBrainz ID found for album '{album_title}' by '{artist_name}'.")
                return None
        except Exception as e:
            logging.error(f"Error fetching MusicBrainz ID for album '{album_title}' by '{artist_name}': {e}")
            return None

    def get_artist_id(self, artist_name: str) -> str | None:
        try:
            result = musicbrainzngs.search_artists(artist=artist_name)
            
            artist_id = result.get('artist-list', [{}])[0].get('id')
            if artist_id:
                return artist_id
            else:
                logging.warning(f"No matching MusicBrainz ID found for artist '{artist_name}'.")

                return None
        except Exception as e:
            logging.error(f"Error fetching MusicBrainz ID for artist '{artist_name}': {e}")
            return None
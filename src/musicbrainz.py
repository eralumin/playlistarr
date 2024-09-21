import musicbrainzngs
import logging

class MusicBrainzService:
    def __init__(self, ):
        musicbrainzngs.set_useragent("playlistarr", "1.0", "https://github.com/eralumin/playlistarr")
    
    def get_album_id(self, album_title: str, artist_name: str) -> str | None:
        try:
            result = musicbrainzngs.search_releases(artist=artist_name, release=album_title)
            if result['release-list']:
                return result['release-list'][0]['id']
            else:
                logging.warning(f"No matching MusicBrainz ID found for album '{album_title}' by '{artist_name}'.")
                return None
        except Exception as e:
            logging.error(f"Error fetching MusicBrainz ID for album '{album_title}' by '{artist_name}': {e}")
            return None

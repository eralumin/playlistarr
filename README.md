# Playlistarr - Playlist Manager for Lidarr and Navidrome

This project automates the process of fetching playlists from Spotify, adding corresponding albums to **Lidarr**, and creating playlists in **Navidrome** using the **Subsonic API**. The application supports dynamic configuration through environment variables, making it easy to customize the quality and metadata profiles used in Lidarr.

## Features

- **Fetch playlists from Spotify** using the Spotify API.
- **Add albums to Lidarr** and monitor them, using user-specified quality and metadata profiles.
- **Create playlists in Navidrome** using the Subsonic API and add matching tracks.
- Automated **Docker image build** and deployment using GitHub Actions with versioned tags.

## Prerequisites

- Docker
- Docker Compose
- Spotify API credentials (client ID and secret)
- Lidarr API key
- Navidrome API (Subsonic API) credentials

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-repo/playlist-manager.git
cd playlist-manager
```

### 2. Set Up Environment Variables
Create a .env file at the root of your project to provide the required environment variables. Below is an example of the environment variables:

```bash
# Spotify API Credentials
SPOTIFY_CLIENT_ID=your-spotify-client-id
SPOTIFY_CLIENT_SECRET=your-spotify-client-secret

# Lidarr Configuration
LIDARR_URL=http://localhost:8686
LIDARR_API_KEY=your-lidarr-api-key

# Navidrome Configuration (Subsonic API)
NAVIDROME_URL=http://localhost:4533
NAVIDROME_USERNAME=your-username
NAVIDROME_PASSWORD=your-encoded-password

# Profiles for Lidarr
QUALITY_PROFILE_NAME=HQ
METADATA_PROFILE_NAME=Standard
```

### 3. Running the Application
You can run the application using Docker Compose. The docker-compose.yml file will allow you to build the Docker image and start the service with the proper environment variables.

```bash
docker-compose up --build
```

This command will build the Docker image, run the service, and the logs will show the process of fetching Spotify playlists, adding albums to Lidarr, and creating playlists in Navidrome.

## Docker Compose Example
Below is an example docker-compose.yml file. You can use this file to set up the environment and build the Docker image.

```yaml
version: '3.8'

services:
  playlist-manager:
    build: .
    container_name: playlist-manager
    env_file: .env
    environment:
      - SPOTIFY_CLIENT_ID=${SPOTIFY_CLIENT_ID}
      - SPOTIFY_CLIENT_SECRET=${SPOTIFY_CLIENT_SECRET}
      - LIDARR_URL=${LIDARR_URL}
      - LIDARR_API_KEY=${LIDARR_API_KEY}
      - NAVIDROME_URL=${NAVIDROME_URL}
      - NAVIDROME_USERNAME=${NAVIDROME_USERNAME}
      - NAVIDROME_PASSWORD=${NAVIDROME_PASSWORD}
      - QUALITY_PROFILE_NAME=${QUALITY_PROFILE_NAME}
      - METADATA_PROFILE_NAME=${METADATA_PROFILE_NAME}
    volumes:
      - ./src:/app/src
    command: ["python", "/app/src/your_scripts.py"]
```

## Project Structure

```bash
.
├── Dockerfile                           # Dockerfile to build the container
├── .github/workflows/docker-build.yml   # GitHub Actions workflow
├── docker-compose.yml                   # Docker Compose file to build and run the container
├── requirements.txt                     # Python dependencies
├── src                                  # Application source code
│   ├── your_scripts.py                  # Main Python script for managing playlists
├── .env.example                         # Example environment variables file
```

## How It Works
- **Spotify Playlists**: The application fetches playlists from Spotify.
- **Lidarr Integration**: For each track in the playlist, the corresponding album is added to Lidarr if it's not already monitored, using the profiles specified in the environment variables.
- **Navidrome Playlists**: The application searches for each track in Navidrome and creates playlists using the Subsonic API.
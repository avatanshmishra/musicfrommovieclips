const API_BASE = import.meta.env.VITE_API_BASE_URL

export default function CreateSpotifyPlaylist({ tracks }) {
  const createPlaylist = async () => {
    const accessToken = localStorage.getItem('spotify_token')
    const trackUris = tracks.map((track) => track.uri).filter(Boolean)

    if (!accessToken) {
      alert('Please connect Spotify first')
      return
    }

    if (!trackUris.length) {
      alert('No Spotify track URIs found')
      return
    }

    const res = await fetch(`${API_BASE}/api/spotify/create-playlist`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        access_token: accessToken,
        playlist_name: 'AI Movie Scene Playlist',
        description: 'Generated from movie scene analysis',
        track_uris: trackUris,
      }),
    })

    const data = await res.json()

    if (data.playlist_url) {
      window.open(data.playlist_url, '_blank')
    } else {
      alert(data.error || 'Failed to create playlist')
    }
  }

  return (
    <button onClick={createPlaylist} className="primary-btn">
      Create Spotify Playlist
    </button>
  )
}
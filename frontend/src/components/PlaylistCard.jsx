import { ExternalLink, Play, Pause } from 'lucide-react'

export default function PlaylistCard({ track, index, activeTrack, setActiveTrack }) {
  const isActive = activeTrack === index

  const handlePreviewToggle = () => {
    if (!track.preview_url) return

    if (isActive) {
      setActiveTrack(null)
    } else {
      setActiveTrack(index)
    }
  }

  return (
    <div className="playlist-card glass">
      {track.image && (
        <img
          src={track.image}
          alt={track.title}
          className="playlist-cover"
          style={{ width: '100%', borderRadius: '12px', marginBottom: '12px' }}
        />
      )}

      <h3>{track.title}</h3>
      <p>{track.artist}</p>

      <div style={{ display: 'flex', gap: '10px', marginTop: '12px', flexWrap: 'wrap' }}>
        {track.preview_url && (
          <button onClick={handlePreviewToggle} className="mode-btn" type="button">
            {isActive ? <Pause size={16} /> : <Play size={16} />}
            {isActive ? 'Stop Preview' : 'Play Preview'}
          </button>
        )}

        {track.spotify_url && (
          <a
            href={track.spotify_url}
            target="_blank"
            rel="noreferrer"
            className="mode-btn"
            style={{ textDecoration: 'none' }}
          >
            <ExternalLink size={16} />
            Open in Spotify
          </a>
        )}
      </div>

      {isActive && track.preview_url && (
        <audio
          src={track.preview_url}
          controls
          autoPlay
          style={{ width: '100%', marginTop: '12px' }}
          onEnded={() => setActiveTrack(null)}
        />
      )}
    </div>
  )
}
import { ExternalLink, Pause, Play, Volume2 } from 'lucide-react'
import { useMemo, useRef, useState } from 'react'

export default function PlaylistCard({ track, index, activeTrack, setActiveTrack }) {
  const audioRef = useRef(null)
  const [playing, setPlaying] = useState(false)
  const isActive = activeTrack === `${track.title}-${index}`

  const spotifyEmbed = useMemo(() => track.embed_url, [track.embed_url])

  const toggleAudio = async () => {
    if (!track.preview_url) return

    if (!audioRef.current) {
      audioRef.current = new Audio(track.preview_url)
      audioRef.current.addEventListener('ended', () => {
        setPlaying(false)
        setActiveTrack(null)
      })
      audioRef.current.addEventListener('pause', () => setPlaying(false))
      audioRef.current.addEventListener('play', () => setPlaying(true))
    }

    if (isActive && playing) {
      audioRef.current.pause()
      return
    }

    setActiveTrack(`${track.title}-${index}`)
    await audioRef.current.play()
  }

  return (
    <div className="track-card">
      <div className="track-cover">
        {track.image ? <img src={track.image} alt={track.title} /> : <div className="track-cover-fallback">{index + 1}</div>}
      </div>
      <div className="track-meta">
        <h4>{track.title}</h4>
        <p>{track.artist}</p>
        <span>{track.album}</span>
        <div className="track-note">
          {track.preview_url ? 'Instant 30-sec preview available' : spotifyEmbed ? 'Open the embed to listen on Spotify' : 'Preview depends on music provider'}
        </div>
        {spotifyEmbed && (
          <iframe
            className="spotify-embed"
            src={spotifyEmbed}
            title={`${track.title} embed`}
            allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
            loading="lazy"
          />
        )}
      </div>
      <div className="track-actions">
        {track.preview_url && (
          <button type="button" className="icon-btn" onClick={toggleAudio} aria-label="Play preview">
            {isActive && playing ? <Pause size={16} /> : <Play size={16} />}
          </button>
        )}
        {track.external_url && (
          <a href={track.external_url} target="_blank" rel="noreferrer" className="icon-btn" aria-label="Open source link">
            {track.preview_url ? <Volume2 size={16} /> : <ExternalLink size={16} />}
          </a>
        )}
      </div>
    </div>
  )
}

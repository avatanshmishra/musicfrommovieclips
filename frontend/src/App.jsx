import { motion } from 'framer-motion'
import { Sparkles, AudioLines, Clapperboard, Upload, Video } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import SpaceScene from './components/SpaceScene'
import PlaylistCard from './components/PlaylistCard'
import SpotifyLogin from './components/SpotifyLogin'
import CreateSpotifyPlaylist from './components/CreateSpotifyPlaylist'
import { generatePlaylist, generatePlaylistFromClip } from './api'

const initialForm = {
  movie_title: '',
  scene_description:
    '',
  preferred_language: 'any',
  tracks_count: 12,
}

export default function App() {
  const [mode, setMode] = useState('clip')
  const [form, setForm] = useState(initialForm)
  const [clip, setClip] = useState(null)
  const [clipUrl, setClipUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [activeTrack, setActiveTrack] = useState(null)
  const [spotifyToken, setSpotifyToken] = useState(null)

  const tags = useMemo(() => result?.scene_profile?.moods || [], [result])

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const token = params.get('spotify_token')

    if (token) {
      setSpotifyToken(token)
      localStorage.setItem('spotify_token', token)

      const cleanUrl = window.location.origin + window.location.pathname
      window.history.replaceState({}, document.title, cleanUrl)
    } else {
      const savedToken = localStorage.getItem('spotify_token')
      if (savedToken) {
        setSpotifyToken(savedToken)
      }
    }
  }, [])

  useEffect(() => {
    return () => {
      if (clipUrl) URL.revokeObjectURL(clipUrl)
    }
  }, [clipUrl])

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: name === 'tracks_count' ? Number(value) : value }))
  }

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (clipUrl) URL.revokeObjectURL(clipUrl)
    setClip(file)
    setClipUrl(URL.createObjectURL(file))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setActiveTrack(null)

    try {
      let data
      if (mode === 'clip') {
        if (!clip) throw new Error('Upload a movie clip first')
        data = await generatePlaylistFromClip({ ...form, clip })
      } else {
        data = await generatePlaylist(form)
      }
      setResult(data)
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-shell">
      <SpaceScene />
      <div className="overlay" />

      <main className="page">
        <motion.section
          className="hero glass"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <div className="eyebrow">INTERSTELLAR MODE • MOVIE CLIP TO MUSIC</div>
          <h1>Upload a movie clip and turn it into a playable cosmic playlist.</h1>
          <p>
            The AI samples frames from your video, reads motion and visuals, blends that with your note, then returns music you can preview right inside the app.
          </p>

          <div className="hero-badges">
            <span><Video size={16} /> Video understanding</span>
            <span><Sparkles size={16} /> AI vibe extraction</span>
            <span><AudioLines size={16} /> Playable soundtrack</span>
          </div>

          <div className="spotify-auth-row" style={{ marginTop: '16px' }}>
            {!spotifyToken ? (
              <SpotifyLogin />
            ) : (
              <div className="spotify-connected">Spotify Connected ✅</div>
            )}
          </div>
        </motion.section>

        <div className="mode-switch glass">
          <button className={mode === 'clip' ? 'mode-btn active' : 'mode-btn'} onClick={() => setMode('clip')} type="button">
            <Upload size={16} /> Upload Clip
          </button>
          <button className={mode === 'text' ? 'mode-btn active' : 'mode-btn'} onClick={() => setMode('text')} type="button">
            <Clapperboard size={16} /> Text Only
          </button>
        </div>

        <div className="grid">
          <motion.section className="panel glass" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.15, duration: 0.7 }}>
            <h2>{mode === 'clip' ? 'Clip Input' : 'Scene Input'}</h2>
            <form onSubmit={handleSubmit} className="form">
              <label>
                Movie title
                <input name="movie_title" value={form.movie_title} onChange={handleChange} placeholder="Enter movie title(optional)" />
              </label>

              <label>
                Director note for the AI
                <textarea
                  name="scene_description"
                  value={form.scene_description}
                  onChange={handleChange}
                  rows="7"
                  placeholder="Describe what matters emotionally e.g, loss, awe, reunion, dread, romance, silence...(optional)"
                />
              </label>

              {mode === 'clip' && (
                <label className="upload-box">
                  Upload movie clip
                  <input type="file" accept="video/*" onChange={handleFileChange} />
                  <div className="upload-meta">MP4, MOV, WebM all work best for this starter. Short clips under 60s feel fastest.</div>
                </label>
              )}

              {clipUrl && mode === 'clip' && (
                <div className="video-preview-wrap">
                  <video className="video-preview" src={clipUrl} controls />
                </div>
              )}

              <div className="row-2">
                <label>
                  Language hint
                  <input name="preferred_language" value={form.preferred_language} onChange={handleChange} placeholder="any / English / Hindi" />
                </label>
                <label>
                  Number of tracks
                  <input name="tracks_count" type="number" min="5" max="20" value={form.tracks_count} onChange={handleChange} />
                </label>
              </div>

              <button disabled={loading} className="primary-btn" type="submit">
                {loading ? 'Scanning the wormhole...' : mode === 'clip' ? 'Analyze Clip + Generate Playlist' : 'Generate Playlist'}
              </button>

              {error && <div className="error-box">{error}</div>}
            </form>
          </motion.section>

          <motion.section className="panel glass" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.25, duration: 0.7 }}>
            <h2>AI Analysis</h2>
            {result ? (
              <div className="analysis-wrap">
                <p className="summary">{result.scene_profile.summary}</p>

                <div className="chips">
                  {tags.map((tag) => (
                    <span key={tag} className="chip">{tag}</span>
                  ))}
                </div>

                <div className="stats-grid">
                  <div className="stat-box">
                    <span>Source</span>
                    <strong>{result.scene_profile.source_type}</strong>
                  </div>
                  <div className="stat-box">
                    <span>Energy</span>
                    <strong>{result.scene_profile.energy}</strong>
                  </div>
                  <div className="stat-box">
                    <span>Valence</span>
                    <strong>{result.scene_profile.valence}</strong>
                  </div>
                  <div className="stat-box">
                    <span>Tempo</span>
                    <strong>{result.scene_profile.tempo}</strong>
                  </div>
                </div>

                {result.scene_profile.dominant_visuals?.length > 0 && (
                  <div className="query-box">
                    <div className="query-title">Dominant visuals from the clip</div>
                    <div className="chips compact">
                      {result.scene_profile.dominant_visuals.map((visual) => (
                        <span className="chip" key={visual}>{visual}</span>
                      ))}
                    </div>
                  </div>
                )}

                {(result.scene_profile.clip_duration_seconds || result.scene_profile.sampled_frames) && (
                  <div className="query-box">
                    <div className="query-title">Clip processing stats</div>
                    <ul>
                      {result.scene_profile.clip_duration_seconds ? <li>Clip duration: {result.scene_profile.clip_duration_seconds}s</li> : null}
                      {result.scene_profile.sampled_frames ? <li>Frames analyzed: {result.scene_profile.sampled_frames}</li> : null}
                    </ul>
                  </div>
                )}

                <div className="query-box">
                  <div className="query-title">Generated search signals</div>
                  <ul>
                    {result.scene_profile.search_queries.map((query) => (
                      <li key={query}>{query}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : (
              <div className="empty-state">Upload a clip and the AI will break down its emotion, pace, and visuals.</div>
            )}
          </motion.section>
        </div>

        <motion.section className="playlist glass" initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35, duration: 0.7 }}>
          <div className="section-head">
            <h2>Generated Playlist</h2>
            <span>{result?.tracks?.length || 0} tracks</span>
          </div>

          {spotifyToken && result?.tracks?.length > 0 && (
            <div style={{ marginBottom: '16px' }}>
              <CreateSpotifyPlaylist tracks={result.tracks} />
            </div>
          )}

          <div className="playlist-grid">
            {result?.tracks?.length ? (
              result.tracks.map((track, index) => (
                <PlaylistCard
                  key={`${track.title}-${index}`}
                  track={track}
                  index={index}
                  activeTrack={activeTrack}
                  setActiveTrack={setActiveTrack}
                />
              ))
            ) : (
              <div className="empty-state large">Your playlist will appear here like a signal from deep space.</div>
            )}
          </div>

          <div className="playlist-footnote">
            Playback inside the app uses provider previews when available. Full listening can continue through the Spotify link or embed.
          </div>
        </motion.section>
      </main>
    </div>
  )
}
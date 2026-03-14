const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://avatanshmishra-musicplaylist.hf.space'

export async function generatePlaylist(payload) {
  const response = await fetch(`${API_BASE_URL}/api/generate-playlist`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(data?.detail || 'Failed to generate playlist')
  }

  return data
}

export async function generatePlaylistFromClip(payload) {
  const formData = new FormData()
  formData.append('movie_title', payload.movie_title)
  formData.append('scene_description', payload.scene_description)
  formData.append('preferred_language', payload.preferred_language)
  formData.append('tracks_count', String(payload.tracks_count))
  formData.append('clip', payload.clip)

  const response = await fetch(`${API_BASE_URL}/api/generate-from-clip`, {
    method: 'POST',
    body: formData,
  })

  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(data?.detail || 'Failed to analyze video clip')
  }

  return data
}

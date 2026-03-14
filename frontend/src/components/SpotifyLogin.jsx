import React from "react"

const API_BASE = import.meta.env.VITE_API_BASE_URL

export default function SpotifyLogin() {

  const handleLogin = async () => {
    const res = await fetch(`${API_BASE}/api/spotify/login`)
    const data = await res.json()

    window.location.href = data.auth_url
  }

  return (
    <button
      onClick={handleLogin}
      style={{
        padding: "10px 20px",
        background: "#1DB954",
        color: "white",
        border: "none",
        borderRadius: "8px",
        cursor: "pointer"
      }}
    >
      Connect Spotify
    </button>
  )
}
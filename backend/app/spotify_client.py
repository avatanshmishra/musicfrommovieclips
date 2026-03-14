import base64
import os
from typing import List
from urllib.parse import quote

import httpx

from .schemas import Track


class SpotifyClient:
    token_url = "https://accounts.spotify.com/api/token"
    search_url = "https://api.spotify.com/v1/search"

    def __init__(self) -> None:
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID", "")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "")

    async def _get_token(self) -> str | None:
        if not self.client_id or not self.client_secret:
            return None

        basic = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode("utf-8")
        ).decode("utf-8")

        headers = {
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"grant_type": "client_credentials"}

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(self.token_url, headers=headers, data=data)
            response.raise_for_status()
            return response.json().get("access_token")

    async def search_tracks(self, queries: List[str], limit: int = 12) -> List[Track]:
        token = await self._get_token()
        if not token:
            return self._mock_tracks(queries, limit)

        headers = {"Authorization": f"Bearer {token}"}
        collected: list[Track] = []
        seen: set[str] = set()

        async with httpx.AsyncClient(timeout=20) as client:
            for query in queries:
                params = {"q": query, "type": "track", "limit": 10, "market": "US"}
                response = await client.get(self.search_url, headers=headers, params=params)
                response.raise_for_status()
                items = response.json().get("tracks", {}).get("items", [])

                for item in items:
                    key = f"{item['name']}::{','.join(a['name'] for a in item['artists'])}"
                    if key in seen:
                        continue
                    seen.add(key)
                    external_url = item.get("external_urls", {}).get("spotify")
                    collected.append(
                        Track(
                            title=item["name"],
                            artist=", ".join(a["name"] for a in item["artists"]),
                            album=item["album"]["name"],
                            image=(item["album"]["images"][0]["url"] if item["album"].get("images") else None),
                            preview_url=item.get("preview_url"),
                            external_url=external_url,
                            embed_url=self._spotify_embed_url(item.get("id"), external_url),
                        )
                    )
                    if len(collected) >= limit:
                        return collected[:limit]

        if not collected:
            return self._mock_tracks(queries, limit)
        return collected[:limit]

    def _spotify_embed_url(self, track_id: str | None, external_url: str | None) -> str | None:
        if track_id:
            return f"https://open.spotify.com/embed/track/{track_id}"
        if external_url and "/track/" in external_url:
            return external_url.replace("open.spotify.com/track/", "open.spotify.com/embed/track/")
        return None

    def _mock_tracks(self, queries: List[str], limit: int) -> List[Track]:
        seed_names = [
            "Cornfield Signal",
            "Event Horizon Heartbeat",
            "Murph's Promise",
            "Dust and Gravity",
            "Falling Through Saturn",
            "Docking Sequence Dream",
            "Signal Beyond Time",
            "Ocean of Silence",
            "The Last Transmission",
            "Axiom of Hope",
            "Dark Matter Lullaby",
            "Redshift Run",
        ]
        artists = [
            "Nova Archive",
            "Graviton Bloom",
            "Celestial Static",
            "Kepler Hearts",
            "Wormhole Cinema",
            "Saturnine",
        ]

        tracks = []
        for i in range(limit):
            q = queries[i % len(queries)] if queries else "cinematic ambient"
            title = seed_names[i % len(seed_names)]
            artist = artists[i % len(artists)]
            search_url = f"https://open.spotify.com/search/{quote(f'{title} {artist} {q}') }"
            tracks.append(
                Track(
                    title=title,
                    artist=artist,
                    album=f"Generated from {q[:28]}",
                    image=f"https://picsum.photos/seed/interstellar-{i}/300/300",
                    preview_url=None,
                    external_url=search_url,
                    embed_url=None,
                )
            )
        return tracks

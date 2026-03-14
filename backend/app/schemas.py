from typing import List, Optional
from pydantic import BaseModel, Field


class PlaylistRequest(BaseModel):
    movie_title: str = Field(..., min_length=1, max_length=120)
    scene_description: str = Field(..., min_length=10, max_length=4000)
    preferred_language: Optional[str] = "any"
    tracks_count: int = Field(default=12, ge=5, le=20)


class SceneProfile(BaseModel):
    summary: str
    moods: List[str]
    genres: List[str]
    energy: float
    valence: float
    tempo: str
    search_queries: List[str]
    dominant_visuals: List[str] = []
    source_type: str = "text"
    clip_duration_seconds: Optional[float] = None
    sampled_frames: Optional[int] = None


class Track(BaseModel):
    title: str
    artist: str
    album: str
    image: Optional[str] = None
    preview_url: Optional[str] = None
    external_url: Optional[str] = None
    embed_url: Optional[str] = None


class PlaylistResponse(BaseModel):
    scene_profile: SceneProfile
    tracks: List[Track]

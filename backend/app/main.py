import os

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .clip_analyzer import ClipAnalyzer, save_upload_to_temp
from .model_pipeline import SceneToPlaylistModel
from .schemas import PlaylistRequest, PlaylistResponse
from .spotify_client import SpotifyClient

load_dotenv()

app = FastAPI(title="AI Movie Clip Playlist Generator", version="2.0.0")

frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = SceneToPlaylistModel()
spotify = SpotifyClient()
clip_analyzer = ClipAnalyzer()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/api/generate-playlist", response_model=PlaylistResponse)
async def generate_playlist(payload: PlaylistRequest) -> PlaylistResponse:
    profile = model.analyze_scene(
        movie_title=payload.movie_title,
        scene_description=payload.scene_description,
        preferred_language=payload.preferred_language or "any",
    )
    tracks = await spotify.search_tracks(profile.search_queries, limit=payload.tracks_count)
    return PlaylistResponse(scene_profile=profile, tracks=tracks)


@app.post("/api/generate-from-clip", response_model=PlaylistResponse)
async def generate_from_clip(
    movie_title: str = Form(...),
    scene_description: str = Form(...),
    preferred_language: str = Form("any"),
    tracks_count: int = Form(12),
    clip: UploadFile = File(...),
) -> PlaylistResponse:
    if not clip.content_type or not clip.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Please upload a valid video file")

    temp_path = None
    try:
        temp_path = save_upload_to_temp(clip)
        clip_analysis = clip_analyzer.analyze(
            temp_path,
            movie_title=movie_title,
            extra_context=scene_description,
        )
        profile = model.analyze_scene(
            movie_title=movie_title,
            scene_description=scene_description,
            preferred_language=preferred_language or "any",
            clip_analysis=clip_analysis,
        )
        tracks = await spotify.search_tracks(profile.search_queries, limit=tracks_count)
        return PlaylistResponse(scene_profile=profile, tracks=tracks)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Video analysis failed: {exc}") from exc
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        await clip.close()

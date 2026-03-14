# AI Music Playlist Generator from Movie Scenes

A full-stack app that turns a movie scene description into a playlist.

## Stack
- **Frontend:** React + Vite + Framer Motion + Three.js (`@react-three/fiber` / `drei`)
- **Backend:** FastAPI
- **Model:** Hugging Face zero-shot emotion classification + scene-to-music mapping
- **Music Source:** Spotify Search API (falls back to mock tracks if Spotify keys are missing)

## Project Structure
```text
interstellar_playlist_ai/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── model_pipeline.py
│   │   ├── schemas.py
│   │   └── spotify_client.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   └── styles.css
│   ├── package.json
│   └── .env.example
└── docker-compose.yml
```

## 1) Local setup

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend
Open a new terminal:
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Now open:
- Frontend: `http://localhost:5173`
- Backend docs: `http://localhost:8000/docs`

## 2) How the app works
1. User writes a movie scene in the frontend.
2. Frontend sends JSON to `POST /api/generate-playlist`.
3. Backend sends the text to the AI scene model.
4. The model predicts moods like `hopeful`, `tense`, `melancholic`, `epic`.
5. The backend converts those moods into music search queries.
6. Spotify search returns tracks.
7. Backend sends the playlist JSON back.
8. Frontend renders the scene analysis + playlist cards.

## 3) API Request Example
```json
{
  "movie_title": "Interstellar",
  "scene_description": "Cooper leaves Murph behind and drives into the dust storm toward NASA.",
  "preferred_language": "any",
  "tracks_count": 12
}
```

## 4) API Response Example
```json
{
  "scene_profile": {
    "summary": "For 'Interstellar', the scene reads as melancholic, hopeful, epic...",
    "moods": ["melancholic", "hopeful", "epic"],
    "genres": ["ambient piano", "neo-classical", "slow electronic", "orchestral"],
    "energy": 0.57,
    "valence": 0.59,
    "tempo": "mid",
    "search_queries": [
      "Interstellar melancholic cinematic soundtrack",
      "ambient piano hopeful mid",
      "space ambient emotional score"
    ]
  },
  "tracks": [
    {
      "title": "Track Name",
      "artist": "Artist",
      "album": "Album",
      "image": "...",
      "preview_url": "...",
      "external_url": "..."
    }
  ]
}
```

## 5) Easy step-by-step: how frontend connects to backend and model

### Step A — Frontend form
In `frontend/src/App.jsx`, the button calls `handleSubmit()`.

### Step B — API helper
`handleSubmit()` calls:
```js
generatePlaylist(form)
```
This is defined in `frontend/src/api.js`.

### Step C — Fetch request
`frontend/src/api.js` sends:
```js
fetch(`${API_BASE_URL}/api/generate-playlist`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload),
})
```
So the frontend talks to your backend using HTTP.

### Step D — Backend route
In `backend/app/main.py`:
```python
@app.post("/api/generate-playlist")
async def generate_playlist(payload: PlaylistRequest):
```
This endpoint receives the JSON from the frontend.

### Step E — Backend calls the AI model
Still in `main.py`:
```python
profile = model.analyze_scene(...)
```
That calls `SceneToPlaylistModel` from `model_pipeline.py`.

### Step F — Model understands the scene
Inside `model_pipeline.py`, the zero-shot classifier reads the scene text and predicts moods.
Then it creates genres, energy, valence, tempo, and search queries.

### Step G — Backend gets songs
Then `main.py` calls:
```python
tracks = await spotify.search_tracks(profile.search_queries, limit=payload.tracks_count)
```
That uses the generated queries to fetch songs from Spotify.

### Step H — Backend sends results back
`main.py` returns:
```python
return PlaylistResponse(scene_profile=profile, tracks=tracks)
```

### Step I — Frontend renders response
Back in `App.jsx`, the response is stored in React state:
```js
setResult(data)
```
Then React displays mood chips, scene stats, and playlist cards.

## 6) How to change the model later
If you want a more advanced AI model later, you have 3 easy upgrade paths:

### Option 1 — Keep current open-source setup
Good for MVP and cheap deployment.

### Option 2 — Use an LLM API
Replace `analyze_scene()` so it asks an LLM to return JSON like:
- moods
- genres
- tempo
- track keywords

### Option 3 — Fine-tune your own model
Train on movie-scene-to-playlist data and replace `SceneToPlaylistModel`.

## 7) Spotify setup
1. Go to Spotify Developer Dashboard.
2. Create an app.
3. Copy `Client ID` and `Client Secret`.
4. Put them in `backend/.env`:
```env
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
FRONTEND_ORIGIN=http://localhost:5173
```
If you skip this, the app still works using mock generated tracks.

## 8) Docker deployment

### backend/Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### frontend/Dockerfile
```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### docker-compose.yml
```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      SPOTIFY_CLIENT_ID: ${SPOTIFY_CLIENT_ID}
      SPOTIFY_CLIENT_SECRET: ${SPOTIFY_CLIENT_SECRET}
      FRONTEND_ORIGIN: http://localhost:5173

  frontend:
    build:
      context: ./frontend
      args:
        VITE_API_BASE_URL: http://localhost:8000
    ports:
      - "5173:80"
    depends_on:
      - backend
```

Run:
```bash
docker compose up --build
```

## 9) Easiest production deployment

### Frontend on Vercel
1. Push project to GitHub.
2. Import the `frontend` folder into Vercel.
3. Add env variable:
   - `VITE_API_BASE_URL=https://your-backend-url`
4. Deploy.

### Backend on Render or Railway
1. Create a new Web Service.
2. Point it to the `backend` folder.
3. Start command:
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```
4. Add environment variables:
   - `SPOTIFY_CLIENT_ID`
   - `SPOTIFY_CLIENT_SECRET`
   - `FRONTEND_ORIGIN=https://your-vercel-domain.vercel.app`
5. Deploy.

## 10) Important deployment note
The backend downloads Hugging Face models on first start. That can make the first boot slower.
For smaller hosting plans, this may be heavy. If deployment feels too slow, you can:
- switch to an API-based LLM model
- prebuild the model into the Docker image
- keep only one smaller model

## 11) Quick production checklist
- Set correct CORS origin in backend
- Set correct `VITE_API_BASE_URL` in frontend
- Add Spotify keys
- Test `/health`
- Test one real scene from the frontend


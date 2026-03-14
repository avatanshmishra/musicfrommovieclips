from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import pipeline

from .clip_analyzer import ClipAnalysis
from .schemas import SceneProfile


MOOD_LABELS = [
    "hopeful",
    "melancholic",
    "tense",
    "romantic",
    "epic",
    "lonely",
    "mysterious",
    "triumphant",
    "sad",
    "dreamy",
    "urgent",
    "warm",
]

GENRE_BANK = {
    "hopeful": ["cinematic ambient", "post-rock", "orchestral"],
    "melancholic": ["ambient piano", "neo-classical", "slow electronic"],
    "tense": ["dark synth", "trailer score", "industrial ambient"],
    "romantic": ["dream pop", "orchestral", "indie electronic"],
    "epic": ["orchestral", "cinematic electronic", "post-rock"],
    "lonely": ["minimal ambient", "piano", "space ambient"],
    "mysterious": ["ambient", "sci-fi synth", "experimental"],
    "triumphant": ["anthemic score", "post-rock", "uplifting electronic"],
    "sad": ["piano", "slowcore", "ambient"],
    "dreamy": ["dream pop", "ethereal ambient", "downtempo"],
    "urgent": ["percussion score", "electronic", "hybrid cinematic"],
    "warm": ["indie folk", "soft ambient", "acoustic cinematic"],
}


@dataclass
class ModelBundle:
    emotion_classifier: object
    embedder: SentenceTransformer


@lru_cache(maxsize=1)
def get_models() -> ModelBundle:
    emotion_classifier = pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli",
        device=-1,
    )
    embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return ModelBundle(emotion_classifier=emotion_classifier, embedder=embedder)


class SceneToPlaylistModel:
    def __init__(self) -> None:
        self.models = get_models()

    def analyze_scene(
        self,
        movie_title: str,
        scene_description: str,
        preferred_language: str = "any",
        clip_analysis: Optional[ClipAnalysis] = None,
    ) -> SceneProfile:
        joined = f"Movie: {movie_title}. Scene: {scene_description}"
        clf = self.models.emotion_classifier(
            joined,
            MOOD_LABELS,
            multi_label=True,
            hypothesis_template="This movie scene feels {}.",
        )

        ranked = sorted(zip(clf["labels"], clf["scores"]), key=lambda x: x[1], reverse=True)
        moods = [label for label, _ in ranked[:4]]
        if clip_analysis:
            moods = self._blend_moods(moods, clip_analysis.moods)

        genre_candidates: list[str] = []
        for mood in moods:
            genre_candidates.extend(GENRE_BANK.get(mood, []))
        genres = list(dict.fromkeys(genre_candidates))[:4]

        energy = self._estimate_energy(moods, scene_description, clip_analysis)
        valence = self._estimate_valence(moods)
        tempo = self._tempo_from_energy(energy)

        summary = self._build_summary(movie_title, scene_description, moods, clip_analysis)
        search_queries = self._build_queries(movie_title, moods, genres, tempo, preferred_language, clip_analysis)

        return SceneProfile(
            summary=summary,
            moods=moods,
            genres=genres,
            energy=round(energy, 2),
            valence=round(valence, 2),
            tempo=tempo,
            search_queries=search_queries,
            dominant_visuals=(clip_analysis.dominant_labels if clip_analysis else []),
            source_type="video" if clip_analysis else "text",
            clip_duration_seconds=(clip_analysis.duration_seconds if clip_analysis else None),
            sampled_frames=(clip_analysis.sampled_frames if clip_analysis else None),
        )

    def _blend_moods(self, text_moods: List[str], clip_moods: List[str]) -> List[str]:
        merged: list[str] = []
        for mood in clip_moods + text_moods:
            if mood not in merged:
                merged.append(mood)
        return merged[:4]

    def _estimate_energy(self, moods: List[str], text: str, clip_analysis: Optional[ClipAnalysis] = None) -> float:
        text_low = text.lower()
        energy = 0.45
        energetic_terms = ["chase", "explosion", "run", "panic", "fight", "storm", "launch", "escape"]
        calm_terms = ["whisper", "silence", "look", "memory", "slow", "space", "quiet"]

        energy += 0.12 * sum(m in {"epic", "urgent", "tense", "triumphant"} for m in moods)
        energy -= 0.08 * sum(m in {"lonely", "dreamy", "melancholic", "sad"} for m in moods)
        energy += 0.03 * sum(term in text_low for term in energetic_terms)
        energy -= 0.03 * sum(term in text_low for term in calm_terms)

        if clip_analysis:
            energy += (clip_analysis.motion - 0.1) * 0.9
            if "explosion" in clip_analysis.dominant_labels or "chase" in clip_analysis.dominant_labels:
                energy += 0.08

        return float(np.clip(energy, 0.15, 0.95))

    def _estimate_valence(self, moods: List[str]) -> float:
        score_map = {
            "hopeful": 0.75,
            "melancholic": 0.35,
            "tense": 0.25,
            "romantic": 0.72,
            "epic": 0.68,
            "lonely": 0.22,
            "mysterious": 0.45,
            "triumphant": 0.88,
            "sad": 0.18,
            "dreamy": 0.58,
            "urgent": 0.4,
            "warm": 0.78,
        }
        vals = [score_map[m] for m in moods if m in score_map]
        return float(np.mean(vals)) if vals else 0.5

    def _tempo_from_energy(self, energy: float) -> str:
        if energy < 0.35:
            return "slow"
        if energy < 0.65:
            return "mid"
        return "fast"

    def _build_summary(
        self,
        movie_title: str,
        scene_description: str,
        moods: List[str],
        clip_analysis: Optional[ClipAnalysis] = None,
    ) -> str:
        cleaned = scene_description.strip().replace("\n", " ")
        lead = cleaned[:180] + ("..." if len(cleaned) > 180 else "")
        if clip_analysis:
            return (
                f"For '{movie_title}', the uploaded video reads as {', '.join(moods)}. "
                f"The system combined frame-level visual analysis with your notes. {clip_analysis.description} "
                f"User context: {lead}"
            )
        return (
            f"For '{movie_title}', the scene reads as {', '.join(moods)}. "
            f"The system detected a cinematic emotional arc from this description: {lead}"
        )

    def _build_queries(
        self,
        movie_title: str,
        moods: List[str],
        genres: List[str],
        tempo: str,
        preferred_language: str,
        clip_analysis: Optional[ClipAnalysis] = None,
    ) -> List[str]:
        lang_part = "" if preferred_language in {None, "", "any"} else f" {preferred_language}"
        visuals = ""
        if clip_analysis and clip_analysis.dominant_labels:
            visuals = f" {' '.join(clip_analysis.dominant_labels[:2])}"
        queries = [
            f"{movie_title} {moods[0]} cinematic soundtrack{visuals}{lang_part}",
            f"{genres[0]} {moods[1] if len(moods) > 1 else moods[0]} {tempo}{lang_part}",
            f"space ambient emotional score{visuals}{lang_part}",
            f"{genres[-1]} {moods[-1]} movie score{lang_part}",
        ]
        return list(dict.fromkeys(queries))

from __future__ import annotations

import math
import os
import tempfile
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from typing import List

import cv2
import numpy as np
from PIL import Image
from transformers import pipeline


VISUAL_LABELS = [
    "space",
    "stars",
    "planet",
    "ocean",
    "city",
    "desert",
    "forest",
    "night",
    "sunrise",
    "storm",
    "fire",
    "explosion",
    "war",
    "romance",
    "family",
    "tears",
    "loneliness",
    "suspense",
    "chase",
    "silence",
    "dream",
    "technology",
    "car",
    "rain",
    "snow",
]


@dataclass
class ClipAnalysis:
    description: str
    moods: List[str]
    dominant_labels: List[str]
    brightness: float
    motion: float
    duration_seconds: float
    sampled_frames: int


@lru_cache(maxsize=1)
def get_visual_classifier():
    return pipeline(
        "zero-shot-image-classification",
        model="openai/clip-vit-base-patch32",
        device=-1,
    )


class ClipAnalyzer:
    def __init__(self) -> None:
        self.classifier = get_visual_classifier()

    def analyze(self, file_path: str, movie_title: str = "Unknown Movie", extra_context: str = "") -> ClipAnalysis:
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            raise ValueError("Could not open uploaded video clip")

        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration = frame_count / fps if fps > 0 and frame_count > 0 else 0.0

        target_samples = min(8, max(3, int(duration // 3) + 1)) if duration else 5
        frame_indexes = self._sample_indexes(frame_count, target_samples)

        brightness_scores: list[float] = []
        saturation_scores: list[float] = []
        motion_scores: list[float] = []
        label_counter: Counter[str] = Counter()
        prev_gray = None

        for idx in frame_indexes:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if not ok or frame is None:
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil = Image.fromarray(rgb)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            brightness_scores.append(float(np.mean(gray) / 255.0))
            saturation_scores.append(float(np.mean(hsv[:, :, 1]) / 255.0))

            if prev_gray is not None:
                diff = cv2.absdiff(prev_gray, gray)
                motion_scores.append(float(np.mean(diff) / 255.0))
            prev_gray = gray

            try:
                predictions = self.classifier(pil, candidate_labels=VISUAL_LABELS)
                for item in predictions[:3]:
                    if item["score"] >= 0.16:
                        label_counter[item["label"]] += 1
            except Exception:
                pass

        cap.release()

        brightness = float(np.mean(brightness_scores)) if brightness_scores else 0.45
        saturation = float(np.mean(saturation_scores)) if saturation_scores else 0.4
        motion = float(np.mean(motion_scores)) if motion_scores else 0.18
        labels = [label for label, _ in label_counter.most_common(4)] or self._fallback_labels(brightness, motion, saturation)
        moods = self._infer_moods(labels, brightness, motion, saturation)
        description = self._build_description(movie_title, labels, moods, brightness, motion, duration, extra_context)

        return ClipAnalysis(
            description=description,
            moods=moods,
            dominant_labels=labels,
            brightness=round(brightness, 2),
            motion=round(motion, 2),
            duration_seconds=round(duration, 2),
            sampled_frames=len(brightness_scores),
        )

    def _sample_indexes(self, frame_count: int, target_samples: int) -> list[int]:
        if frame_count <= 0:
            return [0]
        if frame_count <= target_samples:
            return list(range(frame_count))
        return sorted({int(x) for x in np.linspace(0, frame_count - 1, target_samples)})

    def _fallback_labels(self, brightness: float, motion: float, saturation: float) -> list[str]:
        labels = []
        if brightness < 0.28:
            labels.append("night")
        if motion > 0.18:
            labels.append("chase")
        if saturation < 0.28:
            labels.append("silence")
        if brightness > 0.65:
            labels.append("sunrise")
        if not labels:
            labels.append("dream")
        return labels[:4]

    def _infer_moods(self, labels: list[str], brightness: float, motion: float, saturation: float) -> list[str]:
        moods: list[str] = []
        label_set = set(labels)

        if {"space", "stars", "planet"} & label_set:
            moods += ["epic", "dreamy", "lonely"]
        if {"romance", "family"} & label_set:
            moods += ["warm", "hopeful"]
        if {"war", "explosion", "storm", "chase"} & label_set:
            moods += ["tense", "urgent", "epic"]
        if {"tears", "loneliness", "silence", "night"} & label_set:
            moods += ["melancholic", "lonely", "mysterious"]
        if {"technology", "city"} & label_set:
            moods += ["mysterious"]
        if {"dream", "sunrise", "ocean"} & label_set:
            moods += ["dreamy", "hopeful"]

        if brightness < 0.3:
            moods.append("mysterious")
        if brightness > 0.62:
            moods.append("hopeful")
        if motion > 0.16:
            moods.append("urgent")
        if motion < 0.06:
            moods.append("lonely")
        if saturation < 0.25:
            moods.append("melancholic")

        if not moods:
            moods = ["dreamy", "mysterious", "hopeful"]

        # preserve order, dedupe
        seen = set()
        ordered = []
        for mood in moods:
            if mood not in seen:
                seen.add(mood)
                ordered.append(mood)
        return ordered[:4]

    def _build_description(
        self,
        movie_title: str,
        labels: list[str],
        moods: list[str],
        brightness: float,
        motion: float,
        duration: float,
        extra_context: str,
    ) -> str:
        visual_read = ", ".join(labels[:3])
        mood_read = ", ".join(moods[:3])
        pace = "slow and meditative" if motion < 0.08 else "restless and kinetic" if motion > 0.18 else "steady and cinematic"
        light = "dark" if brightness < 0.35 else "luminous" if brightness > 0.62 else "dim"
        context = f" Extra context: {extra_context.strip()}" if extra_context.strip() else ""
        return (
            f"The uploaded clip from '{movie_title}' looks {light}, with visual signals around {visual_read}. "
            f"Its pacing feels {pace}, and the overall emotion reads as {mood_read}. "
            f"The analyzer sampled key frames across roughly {math.ceil(duration) if duration else 'the'} second(s) of footage.{context}"
        )


def save_upload_to_temp(upload_file) -> str:
    suffix = os.path.splitext(upload_file.filename or "clip.mp4")[1] or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(upload_file.file.read())
        return temp_file.name

"""
Remodax - Interview DTOs
Data Transfer Objects for interview flows and live Q&A presentation.
"""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class QuestionAnswerDTO:
    id: str
    session_id: Optional[str]
    question_text: str
    answer_text: str
    timestamp_str: str
    ai_provider: str
    ai_model: str
    response_latency_ms: float
    context_used: bool


@dataclass
class InterviewSessionDTO:
    id: str
    title: str
    started_at_str: str
    ended_at_str: Optional[str]
    audio_source: str
    qa_count: int


@dataclass
class LiveTranscriptionDTO:
    partial_text: str
    is_final: bool

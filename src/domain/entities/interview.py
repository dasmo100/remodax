"""
Remodax - Interview Domain Entities
Models interview sessions and transcribed question/answer interactions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
import uuid


@dataclass
class QuestionAnswer:
    """Represents an individual interview Q&A entry."""
    question_text: str
    answer_text: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    ai_provider: str = ""
    ai_model: str = ""
    response_latency_ms: float = 0.0
    context_used: bool = False

    def is_complete(self) -> bool:
        """Determines if the answer has completed streaming and is recorded."""
        return bool(self.question_text and self.answer_text)


@dataclass
class InterviewSession:
    """Represents an entire active or archived interview session."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Nueva Sesión de Entrevista"
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    audio_source: str = "WASAPI Loopback"
    qa_list: List[QuestionAnswer] = field(default_factory=list)

    def add_qa(self, qa: QuestionAnswer) -> None:
        qa.session_id = self.id
        self.qa_list.append(qa)

    def close_session(self) -> None:
        self.ended_at = datetime.now()

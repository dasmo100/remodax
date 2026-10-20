"""
Remodax - History & Audit Use Cases
Enables querying, searching, and managing locally stored interview history.
"""

from typing import List
from src.domain.ports.storage_port import IHistoryRepository
from src.application.dtos.interview_dto import InterviewSessionDTO, QuestionAnswerDTO


class HistoryManagementUseCase:
    """Manages local retrieval and search of interview records."""

    def __init__(self, history_repo: IHistoryRepository):
        self._history_repo = history_repo

    def get_recent_sessions(self, limit: int = 50) -> List[InterviewSessionDTO]:
        sessions = self._history_repo.list_sessions(limit=limit)
        return [
            InterviewSessionDTO(
                id=s.id,
                title=s.title,
                started_at_str=s.started_at.strftime("%Y-%m-%d %H:%M"),
                ended_at_str=s.ended_at.strftime("%Y-%m-%d %H:%M") if s.ended_at else "En curso",
                audio_source=s.audio_source,
                qa_count=len(s.qa_list)
            )
            for s in sessions
        ]

    def search_qa_history(self, search_term: str) -> List[QuestionAnswerDTO]:
        records = self._history_repo.search_history(search_term)
        return [
            QuestionAnswerDTO(
                id=r.id,
                session_id=r.session_id,
                question_text=r.question_text,
                answer_text=r.answer_text,
                timestamp_str=r.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                ai_provider=r.ai_provider,
                ai_model=r.ai_model,
                response_latency_ms=r.response_latency_ms,
                context_used=r.context_used
            )
            for r in records
        ]

    def delete_session(self, session_id: str) -> bool:
        return self._history_repo.delete_session(session_id)

    def clear_all_history(self) -> bool:
        return self._history_repo.clear_all_history()

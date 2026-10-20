"""
Remodax - Storage Domain Ports
Abstract interfaces for SQLite history, Q&A records, and configuration persistence.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities.interview import InterviewSession, QuestionAnswer
from src.domain.entities.settings_entity import UserSettings


class IHistoryRepository(ABC):
    """Port for persisting and retrieving interview sessions and Q&A history."""

    @abstractmethod
    def save_session(self, session: InterviewSession) -> None:
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[InterviewSession]:
        pass

    @abstractmethod
    def list_sessions(self, limit: int = 50, offset: int = 0) -> List[InterviewSession]:
        pass

    @abstractmethod
    def save_qa(self, qa: QuestionAnswer) -> None:
        pass

    @abstractmethod
    def search_history(self, query: str) -> List[QuestionAnswer]:
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        pass

    @abstractmethod
    def clear_all_history(self) -> bool:
        pass


class ISettingsRepository(ABC):
    """Port for persisting user settings locally."""

    @abstractmethod
    def load_settings(self) -> UserSettings:
        pass

    @abstractmethod
    def save_settings(self, settings: UserSettings) -> None:
        pass

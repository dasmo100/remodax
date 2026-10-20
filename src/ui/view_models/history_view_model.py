"""
Remodax - History ViewModel
Bridges SQLite Q&A history storage with UI display and search filter.
"""

from PySide6.QtCore import QObject, Signal
from src.application.use_cases.history_use_cases import HistoryManagementUseCase


class HistoryViewModel(QObject):
    """Manages history records, search queries, and cleanup."""

    historyLoaded = Signal(list)    # List[QuestionAnswerDTO]
    errorOccurred = Signal(str)

    def __init__(self, history_use_cases: HistoryManagementUseCase):
        super().__init__()
        self._history = history_use_cases

    def load_recent_history(self) -> None:
        try:
            records = self._history.search_qa_history("")
            self.historyLoaded.emit(records)
        except Exception as ex:
            self.errorOccurred.emit(f"Error cargando historial: {str(ex)}")

    def search(self, term: str) -> None:
        try:
            records = self._history.search_qa_history(term)
            self.historyLoaded.emit(records)
        except Exception as ex:
            self.errorOccurred.emit(f"Error en búsqueda de historial: {str(ex)}")

    def clear_all(self) -> None:
        try:
            self._history.clear_all_history()
            self.load_recent_history()
        except Exception as ex:
            self.errorOccurred.emit(f"Error borrando historial: {str(ex)}")

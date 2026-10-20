"""
Remodax - Unit Tests: Domain Entities
Verifies invariants of QuestionAnswer, InterviewSession, and Document models.
"""

from src.domain.entities.interview import QuestionAnswer, InterviewSession
from src.domain.entities.document import Document, DocumentChunk
from src.domain.entities.settings_entity import UserSettings, AudioSourceType
from src.domain.entities.ai_models import AIRequest


def test_question_answer_entity():
    qa = QuestionAnswer(
        question_text="¿Qué es Dependency Inversion?",
        answer_text="Los módulos de alto nivel no deben depender de los de bajo nivel."
    )
    assert qa.is_complete() is True
    assert qa.id is not None
    assert qa.response_latency_ms == 0.0


def test_interview_session_add_qa():
    session = InterviewSession(title="Entrevista Python Senior")
    qa = QuestionAnswer(question_text="Pregunta 1", answer_text="Respuesta 1")
    session.add_qa(qa)

    assert len(session.qa_list) == 1
    assert qa.session_id == session.id
    assert session.ended_at is None

    session.close_session()
    assert session.ended_at is not None


def test_document_entity_chunks():
    doc = Document(
        filename="cv_candidato.pdf",
        filepath="C:/fake/cv_candidato.pdf",
        file_type="pdf",
        file_size_bytes=1024
    )
    assert doc.chunk_count == 0

    chunk = DocumentChunk(document_id=doc.id, chunk_index=0, content="Experiencia en Clean Architecture")
    doc.chunks.append(chunk)

    assert doc.chunk_count == 1

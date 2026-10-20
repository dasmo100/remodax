"""
Remodax - Unit Tests: Question Detector & Noise Filtering
Verifies that noises, coughs, single words, and fillers are rejected,
while legitimate interview questions are accurately accepted.
"""

from src.domain.services.question_detector import QuestionDetector


def test_noise_and_short_hallucinations_rejected():
    noise_cases = [
        "¡Feliz!",
        "Feliz",
        "Gracias",
        "Muchas gracias",
        "Subtítulos realizados por la comunidad de...",
        "Amén",
        "Ok",
        "Sí",
        "No",
        "Hola",
        "Adiós",
        "[música]",
        "(risas)",
        "Tos",
        "Ok perfecto",
        "De acuerdo",
        "Vale bien",
    ]
    for case in noise_cases:
        is_q, reason = QuestionDetector.is_valid_question(case)
        assert is_q is False, f"Expected '{case}' to be rejected as noise/filler, but was accepted: {reason}"


def test_valid_interview_questions_accepted():
    valid_cases = [
        "¿Qué hace un API?",
        "¿Cómo funciona un decorador en Python?",
        "¿Cuál es tu experiencia con Clean Architecture?",
        "Explícame cómo manejas los errores en tu código",
        "Háblame de un proyecto desafiante en el que hayas trabajado",
        "Cuéntame sobre tu experiencia con Docker y Kubernetes",
        "Podrías describir qué es la inversión de dependencias",
        "Nos gustaría conocer tu opinión sobre microservicios frente a monolitos",
        "Háblame de ti",
        "Por qué deberíamos contratarte",
        "Cómo te ves en cinco años",
        "Trabajas bien en equipo",
        "Cuáles son tus mayores fortalezas",
        "Has trabajado con bases de datos relacionales",
        "Tell me about your experience",
        "What is Docker",
    ]
    for case in valid_cases:
        is_q, reason = QuestionDetector.is_valid_question(case)
        assert is_q is True, f"Expected '{case}' to be accepted as a valid question, but was rejected: {reason}"


def test_technical_topics_and_short_directives_accepted():
    topics = [
        "Diferencias entre procesos e hilos",
        "Tipos de APIs en software",
        "Ventajas de microservicios sobre monolitos",
        "Explica SOAP",
        "Define REST",
        "Arquitectura de microservicios y bases de datos",
        "Hablemos de concurrencia en Python",
    ]
    for topic in topics:
        is_q, reason = QuestionDetector.is_valid_question(topic)
        assert is_q is True, f"Expected topic '{topic}' to be accepted, but was rejected: {reason}"


def test_followup_question_not_blocked_by_dedup():
    QuestionDetector.reset_history()
    q1 = "¿Qué es una API REST?"
    is_q1, _ = QuestionDetector.is_valid_question(q1)
    assert is_q1 is True
    QuestionDetector.record_accepted_question(q1)

    # Follow-up question containing 'API REST' should NOT be blocked by substring containment
    q2 = "¿Cuáles son las diferencias entre una API REST y SOAP?"
    is_q2, reason = QuestionDetector.is_valid_question(q2)
    assert is_q2 is True, f"Follow-up question '{q2}' was mistakenly rejected by dedup: {reason}"

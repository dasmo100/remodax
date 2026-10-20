"""
Remodax - Interview Question Detection & Semantic Filtering Service
Identifies whether transcribed speech is a legitimate interview question or interviewer request
(e.g., 'Explícame tu experiencia', '¿Cómo resolverías...?')
or merely background noise, coughs, greetings, conversational fillers, or Whisper hallucinations.
Provides deduplication to prevent processing repeated questions.
"""

import re
import time
from typing import Tuple, List

# Known Whisper hallucination substrings and video artifacts
HALLUCINATION_SUBSTRINGS = [
    "subtítulo", "subtitulo", "subtítulos", "subtitulos", "gracias por ver",
    "suscríbete", "suscribete", "amén", "amen", "música", "musica",
    "aplausos", "derechos reservados", "todos los derechos", "para ver más",
    "para ver mas", "transcripción por", "transcripcion por", "campanita",
    "dale like", "patreon", "redes sociales", "síguenos", "siguenos",
    "continuará", "continuara", "translated by", "subtitles by"
]

# Common standalone conversational fillers, affirmations, and small talk
NOISE_OR_FILLER_WORDS = {
    # Hallucinations & noise keywords
    "feliz", "felices", "subtítulos", "subtitulos", "amén", "amen",
    "música", "musica", "aplausos", "risas", "silencio", "ruido", "tos",
    "continúa", "continuará", "bye", "hello", "thanks", "thank you",
    "mbc", "suscríbete", "suscribete", "subtitles",

    # Greetings and farewells (not questions by themselves)
    "hola", "adiós", "adios", "chao", "hasta luego", "buenos días", "buenos dias",
    "buenas tardes", "buenas noches", "muchas gracias", "gracias",
    "un gusto", "mucho gusto", "nos vemos", "hola buenas", "hola qué tal",
    "hola que tal", "saludos",

    # Short affirmations and fillers
    "ok", "okey", "okay", "vale", "entendido", "de acuerdo", "perfecto",
    "exacto", "bien", "bueno", "ajá", "aja", "mm", "mmm", "claro",
    "sí", "si", "no", "ya veo", "listo", "audio", "probando", "test",
    "one", "two", "three", "uno", "dos", "tres", "correcto", "de nada",
    "por supuesto", "totalmente", "cierto", "así es", "asi es",
    "vale bien", "ok perfecto", "vale perfecto", "bien gracias",

    # Audio/connection test fillers
    "me escuchas", "se escucha", "probando sonido", "probando micro",
    "espera un momento", "un segundo", "un momento"
}

# Explicit interrogatives
INTERROGATIVES = [
    "qué", "que", "cómo", "como", "cuál", "cual", "cuáles", "cuales",
    "por qué", "porque", "para qué", "para que", "cuándo", "cuando",
    "dónde", "donde", "quién", "quien", "quiénes", "quienes",
    "cuánto", "cuanto", "cuántos", "cuantos",
    "what", "how", "why", "when", "where", "who", "which"
]

# Interview directives & requests (frequently spoken without '¿' or '?')
INTERVIEW_DIRECTIVE_VERBS = [
    "explícame", "explicame", "explica", "explicar",
    "cuéntame", "cuentame", "cuéntanos", "cuentanos",
    "háblame", "hablame", "háblanos", "hablanos", "hablemos", "hablar",
    "coméntame", "comentame", "comenta", "comentar", "platícame", "platicame",
    "describe", "describa", "menciona", "mencionar", "dime", "dinos", "dame", "danos",
    "detalla", "define", "definir", "profundiza", "compara", "comparar", "comparte",
    "indica", "indícame", "indicame", "responde", "respóndeme", "respondeme",
    "tell", "explain", "describe"
]

# Interview technical and situational patterns
INTERVIEW_SCENARIO_PATTERNS = [
    r"\b(tu|tus)\s+(experiencia|trayectoria|proyecto|proyectos|rol|perfil|habilidades|fortalezas|debilidades|stack)\b",
    r"\bqué\s+harías\s+si\b",
    r"\bque\s+harias\s+si\b",
    r"\bcómo\s+(resolverías|abordarías|implementarías|manejarías|optimizarías|diseñarías|estructurarías)\b",
    r"\bcomo\s+(resolverias|abordarias|implementarias|manejarias|optimizarias|diseñarias|estructurarias)\b",
    r"\b(has\s+trabajado|has\s+usado|has\s+implementado|has\s+manejado|has\s+desarrollado)\b",
    r"\b(tienes\s+experiencia|cuentas\s+con\s+experiencia)\b",
    r"\b(qué\s+sabes\s+de|que\s+sabes\s+de|qué\s+opinas|que\s+opinas|cuál\s+es\s+tu\s+opinión|cual\s+es\s+tu\s+opinion)\b",
    r"\b(opinión|opinion|opinas|qué\s+opinas|que\s+opinas)\b",
    r"\b(gustaría|gustaria|quisiera)\s+(saber|conocer|escuchar|entender)\b",
    r"\b(conocer|saber)\s+tu\s+(opinión|opinion|visión|vision|perspectiva|experiencia)\b",
    r"\b(cuál\s+es\s+la\s+diferencia|cual\s+es\s+la\s+diferencia|diferencias\s+entre|diferencia\s+entre)\b",
    r"\b(ventajas\s+y\s+desventajas|pros\s+y\s+contras|ventajas\s+de|desventajas\s+de)\b",
    r"\b(podrías\s+explicar|podrias\s+explicar|podrías\s+decirme|podrias\s+decirme|podrías\s+darme|podrias\s+darme)\b",
    r"\b(me\s+gustaría\s+saber|me\s+gustaria\s+saber|quisiera\s+saber|nos\s+gustaría\s+saber|quiero\s+saber)\b",
    r"\b(dame\s+un\s+ejemplo|un\s+caso\s+de\s+uso|un\s+ejemplo\s+de)\b",
    r"\b(hablemos\s+de|qué\s+es|que\s+es|cómo\s+funciona|como\s+funciona|para\s+qué\s+sirve|para\s+que\s+sirve)\b",
    r"\b(tipos\s+de|arquitectura\s+de|patrones\s+de|principios\s+de)\b",
    # English equivalents for bilingual technical interviews
    r"\b(tell\s+me\s+about|walk\s+me\s+through|explain\s+your|what\s+would\s+you\s+do|how\s+would\s+you)\b",
    r"\b(have\s+you\s+worked\s+with|what\s+is\s+your\s+experience)\b"
]


class QuestionDetector:
    """Classifies transcribed text to ensure only substantive questions trigger AI answers."""

    # History cache of accepted questions for deduplication (timestamp, normalized_text)
    _recent_questions: List[Tuple[float, str]] = []
    _DEDUP_WINDOW_SECONDS: float = 6.0

    @classmethod
    def is_valid_question(cls, text: str) -> Tuple[bool, str]:
        if not text:
            return False, "Texto vacío."

        # Clean formatting, brackets and repeated punctuation
        raw = text.strip()
        cleaned = re.sub(r"\[.*?\]|\(.*?\)", "", raw).strip()
        if not cleaned:
            return False, "Sonido o anotación entre corchetes descartada."

        cleaned_lower = cleaned.lower()

        # 1. Check for known Whisper hallucination substrings
        for hal in HALLUCINATION_SUBSTRINGS:
            if hal in cleaned_lower:
                return False, f"Alucinación común de Whisper detectada ('{hal}')."

        # 2. Normalize words for lexical inspection
        words = re.findall(r"\b\w+\b", cleaned_lower)
        word_count = len(words)
        if not words:
            return False, "Texto sin palabras legibles."

        # 3. Check if entirely in the noise/filler dictionary
        joined_clean = " ".join(words)
        if joined_clean in NOISE_OR_FILLER_WORDS or cleaned_lower in NOISE_OR_FILLER_WORDS:
            return False, f"Descartado: saludo o frase de relleno ('{raw}')."

        # Check if all words are filler words (e.g., 'vale bien', 'ok perfecto', 'sí claro', 'muchas gracias')
        if all(w in NOISE_OR_FILLER_WORDS for w in words):
            return False, f"Descartado: combinación de palabras de relleno ('{raw}')."

        # Check for directive verbs & question marks
        has_question_mark = ("?" in raw or "¿" in raw)
        has_directive_verb = any(
            re.search(rf"\b{re.escape(verb)}\b", cleaned_lower)
            for verb in INTERVIEW_DIRECTIVE_VERBS
        )

        # 4. Minimum length / word check:
        # A directive like 'Explica SOAP' or question like '¿Qué es REST?' is valid with 2+ words.
        # Utterances must have at least 2 words and at least 6 characters.
        if word_count < 2 or len(cleaned) < 6:
            return False, f"Demasiado corto ({word_count} palabras). Posible ruido o palabra aislada."

        # 5. Check for repetitive word loops (e.g., 'sí sí sí', 'bla bla bla')
        if cls._has_excessive_repetition(words):
            return False, "Frase repetitiva o artefacto de transcripción descartado."

        # 6. Check for duplicate against recent questions (dedup window)
        if cls._is_duplicate_recent_question(joined_clean):
            return False, "Pregunta duplicada o ya procesada recientemente."

        # 7. Check for interrogative words
        has_interrogative = any(
            re.search(rf"\b{re.escape(ind)}\b", cleaned_lower)
            for ind in INTERROGATIVES
        )

        # 8. Check for interview scenario patterns ('tu experiencia', 'cómo resolverías'...)
        has_scenario_pattern = any(
            re.search(pattern, cleaned_lower)
            for pattern in INTERVIEW_SCENARIO_PATTERNS
        )

        # 9. Substantive content check:
        # Utterances with 2+ words that are not purely fillers and contain substantive content
        has_substantive_topic = (
            word_count >= 2
            and any(len(w) >= 3 and w not in NOISE_OR_FILLER_WORDS for w in words)
        )

        # Decision logic:
        # Valid if has question punctuation, interrogatives, directive verbs, scenario patterns, or substantive topic
        if has_question_mark or has_interrogative or has_directive_verb or has_scenario_pattern or has_substantive_topic:
            return True, "Pregunta válida detectada."

        return False, f"No contiene estructura de pregunta válida ({word_count} palabras)."

    @classmethod
    def record_accepted_question(cls, text: str) -> None:
        """Records an accepted question into deduplication cache."""
        now = time.time()
        words = re.findall(r"\b\w+\b", text.lower())
        norm = " ".join(words)
        cls._recent_questions.append((now, norm))
        # Prune old entries
        cutoff = now - cls._DEDUP_WINDOW_SECONDS
        cls._recent_questions = [item for item in cls._recent_questions if item[0] >= cutoff]

    @classmethod
    def reset_history(cls) -> None:
        """Clears deduplication history (e.g., when starting new session)."""
        cls._recent_questions.clear()

    @classmethod
    def _is_duplicate_recent_question(cls, normalized_text: str) -> bool:
        """Checks if normalized text is an exact rapid duplicate of a recently processed question."""
        now = time.time()
        cutoff = now - cls._DEDUP_WINDOW_SECONDS
        cls._recent_questions = [item for item in cls._recent_questions if item[0] >= cutoff]

        cand_words = set(normalized_text.split())
        if not cand_words:
            return False

        for _, past_text in cls._recent_questions:
            # Exact match within dedup window
            if normalized_text == past_text:
                return True
            # High Jaccard similarity (>= 90%) within dedup window
            past_words = set(past_text.split())
            intersection = cand_words.intersection(past_words)
            union = cand_words.union(past_words)
            if union and (len(intersection) / len(union)) >= 0.90:
                return True

        return False

    @classmethod
    def _has_excessive_repetition(cls, words: List[str]) -> bool:
        """Detects if audio contained a stutter/loop like 'sí sí sí sí' or 'ok ok ok'."""
        if len(words) < 3:
            return False
        # Check if 3 consecutive identical words
        for i in range(len(words) - 2):
            if words[i] == words[i + 1] == words[i + 2]:
                return True
        return False

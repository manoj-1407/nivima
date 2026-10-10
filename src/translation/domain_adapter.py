"""
Domain-aware translation.

The problem nobody has solved in dubbing:
A JEE physics teacher says "Newton's third law of motion ke according..."
Generic IndicTrans2 translates this fine.

But then they say "ye wala concept dimensional analysis mein use hoga"
Generic translation: "ఈ భావన డైమెన్షనల్ అనాలిసిస్ లో ఉపయోగించబడుతుంది"
Domain-aware: "ఈ concept dimensional analysis లో వస్తుంది" (preserves the teaching register)

The real problem: educational content has:
1. Technical terms that should NOT be translated (Newton, joule, mol)
2. Domain-specific phrases that have established translations in each language
3. Teacher-specific catchphrases that students recognize ("samajh aaya?")
4. Code-mixed terminology that IndicTrans2 normalizes incorrectly

This module:
- Detects content domain from transcript
- Builds a do-not-translate glossary per domain
- Preserves code-mixed technical terms
- Maintains teacher's catchphrases across all languages
"""

import re
from dataclasses import dataclass

import structlog

log = structlog.get_logger()

# Terms that should NEVER be translated — keep as-is in output
UNIVERSAL_PRESERVE = {
    # Scientific units
    "newton", "joule", "watt", "ampere", "kelvin", "pascal", "hertz",
    "metre", "meter", "kilogram", "mole", "candela",
    # Mathematical terms
    "derivative", "integral", "matrix", "vector", "scalar", "determinant",
    "eigenvalue", "fourier", "laplace", "differential",
    # Chemistry
    "molarity", "molality", "normality", "pH", "catalyst", "oxidation",
    # Biology
    "mitosis", "meiosis", "photosynthesis", "atp", "dna", "rna",
    # Physics
    "momentum", "velocity", "acceleration", "centripetal", "centrifugal",
    # Computer science
    "algorithm", "array", "binary", "recursion", "polymorphism",
    "inheritance", "encapsulation", "api", "database", "query",
    # Exam-specific (India)
    "neet", "jee", "upsc", "gate", "cat", "gmat", "ielts",
}

DOMAIN_GLOSSARIES = {
    "physics": {
        "hi->te": {
            "बल": "బలం",
            "त्वरण": "త్వరణం",
            "वेग": "వేగం",
            "संवेग": "ద్రవ్యవేగం",
            "कार्य": "కార్యం",
            "ऊर्जा": "శక్తి",
            "शक्ति": "సామర్థ్యం",
        },
        "hi->ta": {
            "बल": "விசை",
            "त्वरण": "முடுக்கம்",
            "वेग": "திசைவேகம்",
        }
    },
    "mathematics": {
        "hi->te": {
            "समीकरण": "సమీకరణం",
            "त्रिकोण": "త్రిభుజం",
            "वृत्त": "వృత్తం",
            "कोण": "కోణం",
        }
    },
    "biology": {
        "hi->te": {
            "कोशिका": "కణం",
            "ऊतक": "కణజాలం",
            "अंग": "అవయవం",
        }
    }
}

CATCHPHRASE_PATTERNS = [
    r"समझ आया[\s?]*",
    r"क्लियर है[\s?]*",
    r"ठीक है[\s?]*",
    r"देखो[\s,]*",
    r"सुनो[\s,]*",
    r"अच्छा[\s,]*",
    r"बहुत बढ़िया",
]


@dataclass
class DomainContext:
    domain: str
    confidence: float
    preserve_terms: set[str]
    glossary: dict[str, str]
    detected_catchphrases: list[str]


def detect_domain(transcript: str) -> DomainContext:
    text_lower = transcript.lower()

    domain_signals = {
        "physics": ["newton", "force", "velocity", "acceleration", "energy",
                    "momentum", "gravity", "friction", "wave", "optics",
                    "बल", "त्वरण", "वेग", "ऊर्जा", "गुरुत्व"],
        "mathematics": ["equation", "theorem", "proof", "derivative", "integral",
                        "matrix", "polynomial", "समीकरण", "प्रमेय", "अवकलज"],
        "chemistry": ["atom", "molecule", "reaction", "element", "compound",
                      "mole", "concentration", "परमाणु", "अणु", "अभिक्रिया"],
        "biology": ["cell", "tissue", "organ", "dna", "photosynthesis",
                    "कोशिका", "ऊतक", "प्रकाश संश्लेषण"],
        "computer_science": ["algorithm", "function", "variable", "array",
                             "loop", "class", "object", "database"],
        "history": ["century", "empire", "dynasty", "revolution", "war",
                    "शताब्दी", "साम्राज्य", "क्रांति"],
        "economics": ["gdp", "inflation", "market", "supply", "demand",
                      "मुद्रास्फीति", "बाजार", "मांग"],
    }

    scores = {domain: 0 for domain in domain_signals}
    for domain, signals in domain_signals.items():
        for signal in signals:
            if signal in text_lower:
                scores[domain] += 1

    best_domain = max(scores, key=scores.get)
    best_score = scores[best_domain]
    confidence = min(1.0, best_score / 5.0)

    if best_score == 0:
        best_domain = "general"
        confidence = 0.0

    catchphrases = []
    for pattern in CATCHPHRASE_PATTERNS:
        matches = re.findall(pattern, transcript, re.IGNORECASE)
        catchphrases.extend(matches)

    preserve = set(UNIVERSAL_PRESERVE)
    domain_glossary = DOMAIN_GLOSSARIES.get(best_domain, {})

    log.info("domain_detected",
             domain=best_domain,
             confidence=round(confidence, 2),
             catchphrases=len(catchphrases))

    return DomainContext(
        domain=best_domain,
        confidence=confidence,
        preserve_terms=preserve,
        glossary=domain_glossary,
        detected_catchphrases=list(set(catchphrases))
    )


def build_translation_prompt_with_domain(
    source_text: str,
    translated_text: str,
    source_lang: str,
    target_lang: str,
    domain_ctx: DomainContext
) -> str:
    lang_pair = f"{source_lang}->{target_lang}"
    specific_glossary = domain_ctx.glossary.get(lang_pair, {})

    preserve_list = ", ".join(list(domain_ctx.preserve_terms)[:20])
    glossary_lines = "\n".join(
        f"  '{src}' → '{tgt}'"
        for src, tgt in specific_glossary.items()
    ) if specific_glossary else "  (none)"

    catchphrase_note = ""
    if domain_ctx.detected_catchphrases:
        catchphrase_note = f"""
CATCHPHRASES (preserve the teacher's style, translate warmly):
{chr(10).join(f"  '{c}'" for c in domain_ctx.detected_catchphrases[:5])}"""

    return f"""You are a domain expert dubbing scriptwriter for {domain_ctx.domain} educational content.

TRANSLATION TO REFINE:
Source ({source_lang}): {source_text}
Draft translation ({target_lang}): {translated_text}

DOMAIN: {domain_ctx.domain} (confidence: {domain_ctx.confidence:.0%})

DO NOT TRANSLATE these technical terms — keep them exactly as-is:
{preserve_list}

DOMAIN-SPECIFIC GLOSSARY (use these exact translations):
{glossary_lines}
{catchphrase_note}

RULES:
1. Preserve all technical/scientific terms unchanged
2. Use domain glossary terms where applicable
3. Match the teacher's conversational style — not textbook formal
4. Keep any English terms the original speaker used (code-mixing is intentional)
5. Output ONLY the refined {target_lang} translation, nothing else"""


def apply_domain_preservation(
    text: str,
    domain_ctx: DomainContext,
    placeholder_map: dict | None = None
) -> tuple[str, dict]:
    """
    Replace preserve_terms with placeholders before translation,
    restore them after. Prevents IndicTrans2 from mangling them.

    Returns (processed_text, placeholder_map)
    """
    if placeholder_map is None:
        placeholder_map = {}

    processed = text
    counter = len(placeholder_map)

    for term in domain_ctx.preserve_terms:
        pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
        matches = list(pattern.finditer(processed))

        for match in reversed(matches):
            placeholder = f"__TERM_{counter}__"
            placeholder_map[placeholder] = match.group()
            processed = processed[:match.start()] + placeholder + processed[match.end():]
            counter += 1

    return processed, placeholder_map


def restore_preserved_terms(text: str, placeholder_map: dict) -> str:
    restored = text
    for placeholder, original in placeholder_map.items():
        # First try exact replace
        restored = restored.replace(placeholder, original)
        # Also try regex for case-insensitive or spaced tokens: e.g. __ TERM_0 __
        term_num = placeholder.strip("_").split("_")[-1]
        pattern = re.compile(rf"__\s*term_{term_num}\s*__", re.IGNORECASE)
        restored = pattern.sub(original, restored)
    return restored

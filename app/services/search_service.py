"""Deterministic natural-language scheme search service (M3 standalone integration).

Ranks schemes against a free-text query using weighted lexical matching,
concept synonym expansion, and benefit-amount comparison. It intentionally
does not require external AI/embedding keys so the feature works locally,
with a deterministic, explainable result set.
"""

import re

from app.repositories.scheme_repository import SchemeRepository
from app.schemas.catalog import SchemeSearchResponse, SchemeSearchResultItem
from app.schemas.scheme import SchemeSummaryResponse

# Terms that carry no matching signal in a citizen-provided sentence.
STOPWORDS = {
    "the", "a", "an", "for", "my", "i", "me", "and", "to", "of", "is", "in",
    "on", "with", "need", "needed", "get", "getting", "want", "have", "has",
    "help", "support", "scheme", "yojana", "card", "from", "please", "can",
    "any", "some", "about", "looking", "am", "are", "be", "will", "would",
    "do", "does", "did", "it", "this", "that", "there",
}

# Concept groups let the matcher understand intent, not just exact words.
SYNONYM_GROUPS: dict[str, list[str]] = {
    "healthcare": [
        "treatment", "hospital", "hospitalisation", "hospitalization",
        "medical", "health", "doctor", "clinic", "medicine", "disease",
        "illness", "ayushman", "cashless", "surgery",
    ],
    "pension": [
        "pension", "retirement", "retired", "superannuation", "senior",
        "annuity", "elderly", "aged", "old age",
    ],
    "education": [
        "education", "scholarship", "study", "student", "college", "school",
        "tuition", "academic", "girl", "girls", "woman", "women", "matric",
    ],
    "agriculture": [
        "agriculture", "farmer", "farming", "farm", "crop", "land", "kisan",
        "cultivator", "agricultural", "soil", "harvest",
    ],
    "loan": [
        "loan", "mudra", "business", "enterprise", "startup", "self employed",
        "credit", "finance", "lending",
    ],
    "housing": [
        "house", "housing", "home", "shelter", "pucca", "construction",
        "residence", "roof", "dwelling",
    ],
    "gas": [
        "gas", "lpg", "cylinder", "cooking", "fuel", "kitchen", "stove",
    ],
    "insurance": [
        "insurance", "accident", "suraksha", "bima", "death", "disability",
        "cover", "protection", "life",
    ],
    "income_support": [
        "income", "benefit", "grant", "financial", "assistance", "rupees",
        "subsidy", "allowance",
    ],
    "bank": [
        "bank", "account", "savings", "deposit", "jan dhan", "atm",
    ],
}

# Friendly English explanations used to build per-result match reasons.
REASON_PHRASES: dict[str, str] = {
    "healthcare": "your health and hospital treatment need",
    "pension": "retirement and old-age income support",
    "education": "education and scholarship support",
    "agriculture": "agriculture and farming needs",
    "loan": "business and self-employment loan support",
    "housing": "housing and home assistance",
    "gas": "cooking-gas assistance",
    "insurance": "insurance and accident protection",
    "income_support": "income and financial assistance",
    "bank": "banking and savings schemes",
}

_FIELD_HIT_REASONS: dict[str, str] = {
    "tags": "matching subject tags",
    "target_groups": "designed for your background",
    "benefits": "the benefit you described",
}

# Per-field matching weight (higher = stronger signal).
_FIELD_WEIGHTS: list[tuple[str, float]] = [
    ("scheme_code", 0.60),
    ("name", 0.55),
    ("aliases", 0.50),
    ("tags", 0.45),
    ("target_groups", 0.40),
    ("benefits", 0.20),
    ("description", 0.10),
    ("ministry", 0.15),
]

# Fields where synonym-expansion terms are allowed to match. Keeping expansion
# out of long free-text fields avoids every scheme matching generic concepts.
_DISCRIMINATIVE_FIELDS = {"scheme_code", "name", "aliases", "tags", "target_groups"}

_AMOUNT_RE = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(lakh|lakhs|lkh|thousand)?")


def _normalize(text: str) -> str:
    """Lowercase and fold currency/unit tokens into plain ASCII text."""
    lowered = text.lower()
    lowered = re.sub(r"[\u20b9]|\b(?:inr|rs|rupees?)\b", " rupees ", lowered)
    return lowered.replace("-", " ").replace(",", ",")


def _extract_amounts(text: str) -> list[int]:
    """Return rupee magnitudes found in text (handles '5 lakh' and '5,00,000')."""
    amounts: list[int] = []
    for match in _AMOUNT_RE.finditer(_normalize(text)):
        digits = "".join(match.group(1).split(","))
        try:
            value = float(digits)
        except ValueError:
            continue
        unit = (match.group(2) or "").lower()
        if unit.startswith(("lakh", "lkh")):
            value *= 100_000
        elif unit == "thousand":
            value *= 1_000
        amounts.append(int(value))
    return amounts


def _amounts_overlap(query_amounts: list[int], scheme_text: str) -> bool:
    """Return True when a query amount approximately matches a scheme amount."""
    if not query_amounts:
        return False
    scheme_amounts = _extract_amounts(scheme_text)
    if not scheme_amounts:
        return False
    for q in query_amounts:
        for s in scheme_amounts:
            if q <= 0 or s <= 0:
                continue
            if abs(q - s) <= max(500, min(q, s) * 0.20):
                return True
    return False


def _tokenize(text: str) -> list[str]:
    terms: list[str] = []
    for raw in re.split(r"[^a-z0-9]+", _normalize(text)):
        term = raw.strip()
        if not term or term.isdigit() or term in STOPWORDS:
            continue
        terms.append(term)
    return terms


_WORD_BOUNDARY_CACHE: dict[str, re.Pattern] = {}


def _term_in_text(term: str, text: str) -> bool:
    """Word-boundary aware containment (matches 'girl' in 'girls', not 'house' in 'household')."""
    pattern = _WORD_BOUNDARY_CACHE.get(term)
    if pattern is None:
        escaped = re.escape(term).replace(r"\ ", r"\s+")
        pattern = re.compile(rf"\b{escaped}s?\b")
        _WORD_BOUNDARY_CACHE[term] = pattern
    return bool(pattern.search(text))


class SemanticSearchService:
    """Ranks active schemes by semantic relevance to a free-text query."""

    def __init__(self, repository: SchemeRepository | None = None):
        self.repository = repository or SchemeRepository()

    def search(self, query: str, limit: int = 10) -> SchemeSearchResponse:
        """Return ranked search results, or an empty set with a clarifying prompt."""
        query = (query or "").strip()
        if not query:
            return SchemeSearchResponse(results=[], clarifying_question="Which support are you looking for?")

        terms = _tokenize(query)
        if not terms:
            return SchemeSearchResponse(results=[], clarifying_question="Which support are you looking for?")
        expanded = self._expand_terms(terms)

        query_amounts = _extract_amounts(query)

        scored: list[tuple[float, SchemeSummaryResponse, list[str]]] = []
        for scheme in self.repository.get_all(status="active"):
            outcome = self._score_scheme(scheme, terms, expanded, query_amounts)
            if outcome is None:
                continue
            total, reasons = outcome
            if total >= 0.25:
                scored.append((total, scheme, reasons))

        scored.sort(key=lambda item: item[0], reverse=True)
        top = scored[:limit]

        results = [
            SchemeSearchResultItem(
                scheme=scheme,
                confidence=round(total, 2),
                match_reason="Possible match linked to " + (", ".join(reasons[:3]) or "your description"),
            )
            for total, scheme, reasons in top
        ]

        clarifying_question: str | None = None
        if not results or (results and results[0].confidence < 0.45):
            clarifying_question = "Which state do you live in and what kind of support are you looking for?"

        return SchemeSearchResponse(results=results, clarifying_question=clarifying_question)

    def _expand_terms(self, terms: list[str]) -> list[str]:
        """Expand raw terms with related concept keywords."""
        expanded = set(terms)
        for term in terms:
            for group in SYNONYM_GROUPS.values():
                if term in group:
                    expanded.update(group)
        return list(expanded)

    def _score_scheme(
        self,
        scheme: SchemeSummaryResponse,
        terms: list[str],
        expanded: list[str],
        query_amounts: list[int],
    ) -> tuple[float, list[str]] | None:
        """Compute a weighted relevance score and human-readable match reasons."""
        fields: dict[str, str] = {
            "scheme_code": scheme.scheme_code,
            "name": scheme.name,
            "aliases": " ".join(scheme.aliases),
            "tags": " ".join(scheme.tags),
            "target_groups": " ".join(scheme.target_groups),
            "benefits": " ".join(scheme.benefits),
            "description": scheme.description,
            "ministry": scheme.ministry,
        }
        corpus = " ".join(fields.values()).lower()

        matched_groups: set[str] = set()
        matched_terms: set[str] = set()
        field_hits: dict[str, set[str]] = {name: set() for name, _ in _FIELD_WEIGHTS}
        raw_terms = set(terms)

        for term in expanded:
            for field_name, _weight in _FIELD_WEIGHTS:
                # Raw query terms may match anywhere; synonym-expansion terms
                # are restricted to discriminative metadata fields.
                if term in raw_terms or field_name in _DISCRIMINATIVE_FIELDS:
                    if _term_in_text(term, fields[field_name].lower()):
                        field_hits[field_name].add(term)
                        matched_terms.add(term)

        # Attribute terms back to concept groups for nicer reasons.
        for group, members in SYNONYM_GROUPS.items():
            if any(t in members for t in terms) and any(m in members for m in members if m in corpus):
                matched_groups.add(group)

        if not matched_terms:
            return None

        score = 0.05
        for field_name, weight in _FIELD_WEIGHTS:
            hits = field_hits[field_name]
            if hits:
                score += weight * min(len(hits), 2)

        coverage = len(matched_terms) / max(len(set(expanded)), 1)
        score += coverage * 0.10
        if score < 0.25:
            return None

        if _amounts_overlap(query_amounts, corpus):
            score += 0.20

        reasons: list[str] = []
        for group in sorted(matched_groups):
            reasons.append(REASON_PHRASES[group])
        for field_name in ("tags", "target_groups", "benefits"):
            if field_hits[field_name]:
                reasons.append(_FIELD_HIT_REASONS[field_name])

        unique_reasons: list[str] = []
        for reason in reasons:
            if reason not in unique_reasons:
                unique_reasons.append(reason)
        return (min(score, 0.99), unique_reasons)
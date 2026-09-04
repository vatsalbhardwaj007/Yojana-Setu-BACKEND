"""Deterministic scheme recommendation service based on structured profile metadata."""

from typing import Any

from app.repositories.scheme_repository import SchemeRepository
from app.schemas.catalog import (
    RecommendationResponse,
    RecommendedSchemeItem,
)


class RecommendationService:
    """Service providing deterministic metadata-based scheme recommendations."""

    def __init__(self, repository: SchemeRepository | None = None):
        self.repository = repository or SchemeRepository()

    def recommend(
        self, profile: dict[str, Any], limit: int = 10
    ) -> RecommendationResponse:
        """Score schemes based on citizen profile attributes and metadata match."""
        # Retrieve all active schemes
        schemes = self.repository.get_all(status="active")
        scored_items: list[RecommendedSchemeItem] = []

        user_occupation = str(profile.get("occupation", "")).lower()
        user_gender = str(profile.get("gender", "")).lower()
        user_category = str(profile.get("category", "")).lower()
        user_state = str(profile.get("state", "")).lower()
        user_age = profile.get("age")
        user_income = profile.get("annual_income") or profile.get("income") or profile.get("monthly_income")

        for scheme in schemes:
            score = 0.1  # Baseline discovery score
            match_reasons: list[str] = []

            target_groups_str = " ".join(scheme.target_groups).lower()
            tags_str = " ".join(scheme.tags).lower()
            benefits_str = " ".join(scheme.benefits).lower()
            desc_str = scheme.description.lower()
            name_str = scheme.name.lower()
            combined_text = f"{target_groups_str} {tags_str} {benefits_str} {desc_str} {name_str}"

            # 1. Occupation Match
            if user_occupation and user_occupation in combined_text:
                score += 0.35
                match_reasons.append(f"Directly targets your occupation ({user_occupation.title()})")

            # 2. Gender / Demographics Match
            if user_gender in {"female", "woman", "women"} and any(
                w in combined_text for w in ["women", "mother", "female", "maternity", "matru"]
            ):
                score += 0.25
                match_reasons.append("Designed for women and maternal welfare")

            # 3. Age / Lifecycle Match
            if user_age is not None:
                try:
                    num_age = int(user_age)
                    if num_age >= 60 and any(w in combined_text for w in ["pension", "senior", "elderly"]):
                        score += 0.25
                        match_reasons.append("Designed for senior citizens and elderly welfare")
                    elif num_age <= 25 and any(w in combined_text for w in ["student", "scholarship", "education", "training"]):
                        score += 0.25
                        match_reasons.append("Aimed at youth and student opportunities")
                except (ValueError, TypeError):
                    pass

            # 4. Social Category Match
            if user_category and any(c in combined_text for c in [user_category, "backward", "minority", "scholarship"]):
                score += 0.2
                match_reasons.append(f"Supports beneficiaries from {user_category.upper()} background")

            # 4. State / Region Match
            if user_state and user_state in combined_text:
                score += 0.15
                match_reasons.append(f"Specifically applicable to your state ({user_state.title()})")

            # 5. Income / Deprivation Match
            if user_income is not None:
                try:
                    num_income = float(user_income)
                    if num_income <= 300000 and any(kw in combined_text for kw in ["bpl", "ews", "poor", "low income", "subsidy", "free"]):
                        score += 0.2
                        match_reasons.append("Aimed at low-income and vulnerable households")
                except (ValueError, TypeError):
                    pass

            # 6. Specific Profile Attributes
            if profile.get("has_cultivable_land_in_name") is True and "kisan" in scheme.scheme_code:
                score += 0.3
                match_reasons.append("Matches agricultural landholding criteria")

            if profile.get("owns_pucca_house") is False and "housing" in scheme.scheme_type:
                score += 0.25
                match_reasons.append("Identified housing assistance entitlement")

            # Cap and normalize score
            normalized_score = min(round(score, 2), 0.95)

            if not match_reasons:
                match_reasons.append("Universal public welfare scheme available for all eligible citizens")

            scored_items.append(
                RecommendedSchemeItem(
                    scheme_code=scheme.scheme_code,
                    name=scheme.name,
                    match_reasons=match_reasons,
                    score=normalized_score,
                )
            )

        # Sort by score descending
        scored_items.sort(key=lambda item: item.score, reverse=True)
        top_items = scored_items[:limit]

        return RecommendationResponse(
            items=top_items,
            total=len(top_items),
            disclaimer="Recommendations are based on profile relevance and do not guarantee eligibility. Please check formal eligibility via /eligibility/check.",
        )

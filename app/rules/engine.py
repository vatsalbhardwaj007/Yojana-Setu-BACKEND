"""Generic deterministic eligibility engine for government schemes.

Source of truth is database rules. No scheme-specific logic is permitted.
"""

from typing import Any, Dict, List, Optional

from app.rules.evaluator import evaluate_condition
from app.schemas.eligibility import (
    EligibilityCheckResponse,
    EligibilityStatus,
    EvaluatedRuleResponse,
    ReasonCode,
)
from app.schemas.scheme import SchemeRuleResponse


class EligibilityEngine:
    """Generic deterministic engine that evaluates scheme eligibility and exclusion rules."""

    @classmethod
    def evaluate(
        cls,
        scheme_code: str,
        eligibility_rules: List[SchemeRuleResponse],
        exclusion_rules: List[SchemeRuleResponse],
        profile: Dict[str, Any],
    ) -> EligibilityCheckResponse:
        """Evaluate a citizen's profile against scheme eligibility and exclusion rules."""
        evaluated_rules: List[EvaluatedRuleResponse] = []
        missing_fields_dict: Dict[str, None] = {}
        failed_rule_descriptions: List[str] = []
        triggered_exclusion_descriptions: List[str] = []

        any_rule_failed = False
        any_exclusion_triggered = False

        # -------------------------------------------------------------------
        # 1. Evaluate Eligibility Rules (AND-only)
        # -------------------------------------------------------------------
        for rule in eligibility_rules:
            field = rule.field
            operator = rule.operator
            expected = rule.value
            description = rule.description

            field_present = field in profile
            actual = profile.get(field) if field_present else None

            if operator == "exists":
                # exists operator can be evaluated even if field is missing
                passed, _ = evaluate_condition(
                    operator=operator,
                    actual=actual,
                    expected=expected,
                    field_present=field_present,
                )
                if not passed:
                    any_rule_failed = True
                    failed_rule_descriptions.append(description)

                evaluated_rules.append(
                    EvaluatedRuleResponse(
                        field=field,
                        operator=operator,
                        expected=expected,
                        actual=actual,
                        passed=passed,
                        rule_type="eligibility",
                        description=description,
                    )
                )
            else:
                if not field_present or actual is None:
                    # Missing information
                    missing_fields_dict[field] = None
                    evaluated_rules.append(
                        EvaluatedRuleResponse(
                            field=field,
                            operator=operator,
                            expected=expected,
                            actual=None,
                            passed=None,
                            rule_type="eligibility",
                            description=description,
                        )
                    )
                else:
                    passed, _ = evaluate_condition(
                        operator=operator,
                        actual=actual,
                        expected=expected,
                        field_present=True,
                    )
                    if not passed:
                        any_rule_failed = True
                        failed_rule_descriptions.append(description)

                    evaluated_rules.append(
                        EvaluatedRuleResponse(
                            field=field,
                            operator=operator,
                            expected=expected,
                            actual=actual,
                            passed=passed,
                            rule_type="eligibility",
                            description=description,
                        )
                    )

        # -------------------------------------------------------------------
        # 2. Evaluate Exclusion Rules (Disqualifiers)
        # -------------------------------------------------------------------
        for rule in exclusion_rules:
            field = rule.field
            operator = rule.operator
            expected = rule.value
            description = rule.description

            field_present = field in profile
            actual = profile.get(field) if field_present else None

            if operator == "exists":
                condition_met, _ = evaluate_condition(
                    operator=operator,
                    actual=actual,
                    expected=expected,
                    field_present=field_present,
                )
                if condition_met:
                    # Exclusion condition triggered -> applicant disqualified
                    any_exclusion_triggered = True
                    triggered_exclusion_descriptions.append(description)
                    rule_passed = False
                else:
                    rule_passed = True

                evaluated_rules.append(
                    EvaluatedRuleResponse(
                        field=field,
                        operator=operator,
                        expected=expected,
                        actual=actual,
                        passed=rule_passed,
                        rule_type="exclusion",
                        description=description,
                    )
                )
            else:
                if not field_present or actual is None:
                    # Missing field for exclusion
                    missing_fields_dict[field] = None
                    evaluated_rules.append(
                        EvaluatedRuleResponse(
                            field=field,
                            operator=operator,
                            expected=expected,
                            actual=None,
                            passed=None,
                            rule_type="exclusion",
                            description=description,
                        )
                    )
                else:
                    condition_met, _ = evaluate_condition(
                        operator=operator,
                        actual=actual,
                        expected=expected,
                        field_present=True,
                    )
                    if condition_met:
                        any_exclusion_triggered = True
                        triggered_exclusion_descriptions.append(description)
                        rule_passed = False
                    else:
                        rule_passed = True

                    evaluated_rules.append(
                        EvaluatedRuleResponse(
                            field=field,
                            operator=operator,
                            expected=expected,
                            actual=actual,
                            passed=rule_passed,
                            rule_type="exclusion",
                            description=description,
                        )
                    )

        missing_fields = list(missing_fields_dict.keys())

        # -------------------------------------------------------------------
        # 3. Determine Overall Status, Eligible Boolean, and Reason Codes
        # -------------------------------------------------------------------
        # Rule of precedence:
        # NOT ELIGIBLE: if ANY exclusion triggered OR ANY eligibility rule failed
        if any_exclusion_triggered or any_rule_failed:
            status: EligibilityStatus = "Not Eligible"
            eligible: Optional[bool] = False
            reason_codes: List[str] = []
            reasons: List[str] = []

            if any_exclusion_triggered:
                reason_codes.append("EXCLUSION_TRIGGERED")
                reasons.extend(triggered_exclusion_descriptions)

            if any_rule_failed:
                reason_codes.append("RULE_FAILED")
                reasons.extend(failed_rule_descriptions)

            return EligibilityCheckResponse(
                scheme_code=scheme_code,
                status=status,
                eligible=eligible,
                reason_codes=reason_codes,
                reasons=reasons,
                missing_fields=missing_fields,
                evaluated_rules=evaluated_rules,
            )

        # POTENTIALLY ELIGIBLE: no failures, no exclusions, but missing required information
        if missing_fields:
            status = "Potentially Eligible"
            eligible = None  # JSON null
            reason_codes = ["MISSING_INFORMATION"]
            reasons = []

            return EligibilityCheckResponse(
                scheme_code=scheme_code,
                status=status,
                eligible=eligible,
                reason_codes=reason_codes,
                reasons=reasons,
                missing_fields=missing_fields,
                evaluated_rules=evaluated_rules,
            )

        # ELIGIBLE: all rules passed, no exclusions triggered, no missing information
        status = "Eligible"
        eligible = True
        reason_codes = []
        reasons = []

        return EligibilityCheckResponse(
            scheme_code=scheme_code,
            status=status,
            eligible=eligible,
            reason_codes=reason_codes,
            reasons=reasons,
            missing_fields=[],
            evaluated_rules=evaluated_rules,
        )

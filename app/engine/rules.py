"""Deterministic Python Decision Engine for Credit Card Onboarding.

This engine implements the exact business rules from SCENARIOS.md:
- Bureau score bands: Super Prime (>=780), Prime (740-779), Near Prime (690-739), Low (<690 -> secured).
- New To Credit (NTC): No bureau record. Income < 30k -> secured. Overstated > 25% -> AA sizes limit; if <30k -> secured.
- FOIR sizing: (existing EMIs + notional card EMI) / income <= 50%.
- Special tracks: Student (no pull, FD-backed card), ETB Pre-approved (no pull, pre-approved limit).
- All decisions are purely rule-based with zero LLM dependence.
"""
from typing import Tuple, List
from app.engine.config import CONFIG, EngineConfig
from app.engine.models import (
    CustomerProfile,
    BureauRecord,
    DecisionResult,
    ApplicationStatus,
    DecisionPath,
)
from app.engine.mock_data import lookup_mock_bureau, lookup_mock_aa_income


class DecisionEngine:
    def __init__(self, config: EngineConfig = CONFIG):
        self.config = config

    def evaluate(self, customer: CustomerProfile, bureau: BureauRecord = None) -> DecisionResult:
        """Evaluate a customer application and return deterministic decision result."""
        watch_points: List[str] = []
        
        # Auto-fetch mock bureau if not explicitly passed
        if bureau is None:
            bureau = lookup_mock_bureau(customer.id)

        # -------------------------------------------------------------
        # Rule 12: Existing To Bank (ETB) Pre-Approved Customer
        # -------------------------------------------------------------
        if customer.is_etb and customer.has_preapproved_offer:
            watch_points.append("Pre-approved on file: identity, income & KYC on file; 0 bureau pull; one tap.")
            return DecisionResult(
                status=ApplicationStatus.APPROVE,
                path=DecisionPath.ETB_PREAPPROVED,
                credit_limit=customer.preapproved_limit or 250000,
                product_name="Millennia Platinum (Pre-approved)",
                reason="Pre-approved offer on file for existing customer. Instant approval with no bureau inquiry.",
                hard_pull_performed=False,
                income_verification_method="preapproved_on_file",
                kyc_mode="on_file",
                watch_points_triggered=watch_points,
            )

        # -------------------------------------------------------------
        # Rule 11: Student (New to Credit, No Income)
        # -------------------------------------------------------------
        if customer.is_student:
            watch_points.append("Student track: zero bureau pull, no income asked; FD-backed first card offered.")
            return DecisionResult(
                status=ApplicationStatus.SECURED_OFFER,
                path=DecisionPath.STUDENT,
                credit_limit=self.config.STUDENT_DEFAULT_LIMIT,
                product_name="Campus FD-Backed Credit Builder",
                reason="Student first credit card backed by fixed deposit. Builds credit history safely with no income proof.",
                hard_pull_performed=False,
                income_verification_method="none_student",
                kyc_mode="fd_backed",
                watch_points_triggered=watch_points,
            )

        # -------------------------------------------------------------
        # Handle Bureau Pull & Bureau Score Evaluation
        # -------------------------------------------------------------
        score = bureau.cibil_score

        # -------------------------------------------------------------
        # Rule 10: NTB Low Score (CIBIL < 690)
        # -------------------------------------------------------------
        if score is not None and score < self.config.CIBIL_NEAR_PRIME_MIN:
            watch_points.append(f"Low score ({score} < {self.config.CIBIL_NEAR_PRIME_MIN}): income not asked; offered secured credit-builder.")
            return DecisionResult(
                status=ApplicationStatus.SECURED_OFFER,
                path=DecisionPath.SECURED,
                credit_limit=self.config.SECURED_DEFAULT_LIMIT,
                product_name="Step-Up Secured Credit Builder",
                reason=f"CIBIL score ({score}) below prime threshold ({self.config.CIBIL_NEAR_PRIME_MIN}). Offered secured credit-builder card.",
                hard_pull_performed=True,
                income_verification_method="waived_low_score",
                kyc_mode="standard",
                watch_points_triggered=watch_points,
            )

        # -------------------------------------------------------------
        # Rules 6, 7, 8, 9: New To Credit (NTC - No Bureau Record)
        # -------------------------------------------------------------
        if score is None:
            # Determine effective income
            stated_income = customer.stated_monthly_income or 0.0
            aa_income = customer.aa_verified_income or lookup_mock_aa_income(customer.id)
            
            # Scenario 8: Overstated income (> 25% discrepancy between stated and AA)
            if stated_income > 0 and aa_income is not None:
                if stated_income > (aa_income * (1.0 + self.config.OVERSTATED_INCOME_TOLERANCE)):
                    watch_points.append(f"Typed income ₹{stated_income:,.0f} contradicted by AA ₹{aa_income:,.0f}; limit sized to real income.")
                    # If verified AA income is under 30k -> secured
                    if aa_income < self.config.MIN_UNSECURED_INCOME:
                        watch_points.append(f"AA verified income ₹{aa_income:,.0f} < ₹{self.config.MIN_UNSECURED_INCOME:,.0f} -> secured credit-builder.")
                        return DecisionResult(
                            status=ApplicationStatus.SECURED_OFFER,
                            path=DecisionPath.SECURED,
                            credit_limit=self.config.SECURED_DEFAULT_LIMIT,
                            product_name="Step-Up Secured Credit Builder",
                            reason=f"Account Aggregator verified income (₹{aa_income:,.0f}) is below minimum unsecured limit (₹{self.config.MIN_UNSECURED_INCOME:,.0f}).",
                            hard_pull_performed=False,
                            income_verification_method="account_aggregator",
                            kyc_mode="standard",
                            watch_points_triggered=watch_points,
                        )

            # Scenario 9: Low Income (< 30k)
            effective_income = aa_income if aa_income is not None else stated_income
            if effective_income < self.config.MIN_UNSECURED_INCOME:
                watch_points.append(f"NTC low income (₹{effective_income:,.0f} < ₹{self.config.MIN_UNSECURED_INCOME:,.0f}) -> secured credit-builder.")
                return DecisionResult(
                    status=ApplicationStatus.SECURED_OFFER,
                    path=DecisionPath.SECURED,
                    credit_limit=self.config.SECURED_DEFAULT_LIMIT,
                    product_name="Step-Up Secured Credit Builder",
                    reason=f"Monthly income (₹{effective_income:,.0f}) under unsecured threshold (₹{self.config.MIN_UNSECURED_INCOME:,.0f}). FD-backed credit-builder offered.",
                    hard_pull_performed=False,
                    income_verification_method="stated_or_aa",
                    kyc_mode="standard",
                    watch_points_triggered=watch_points,
                )

            # Scenario 7: NTC with Account Aggregator verification
            if aa_income is not None and aa_income >= self.config.MIN_UNSECURED_INCOME:
                limit = int(aa_income * self.config.NEAR_PRIME_LIMIT_MULTIPLIER)
                watch_points.append(f"NTC via AA: 1 consent, income read from bank data (₹{aa_income:,.0f}); AA figure sizes limit to ₹{limit:,.0f}.")
                return DecisionResult(
                    status=ApplicationStatus.APPROVE,
                    path=DecisionPath.NEAR_PRIME,
                    credit_limit=limit,
                    product_name="Edge Prime Credit Card",
                    reason=f"New to credit with verified income of ₹{aa_income:,.0f} via Account Aggregator.",
                    hard_pull_performed=True,
                    income_verification_method="account_aggregator",
                    kyc_mode="standard",
                    watch_points_triggered=watch_points,
                )

            # Scenario 6: NTC with 3 Payslips upload
            if stated_income >= self.config.MIN_UNSECURED_INCOME:
                limit = int(stated_income * self.config.NEAR_PRIME_LIMIT_MULTIPLIER)
                watch_points.append("NTC high earner: no credit history is starting point -> unsecured card backed by 3 payslips.")
                return DecisionResult(
                    status=ApplicationStatus.APPROVE,
                    path=DecisionPath.NEAR_PRIME,
                    credit_limit=limit,
                    product_name="Edge Prime Credit Card",
                    reason=f"New to credit with verified payslips showing ₹{stated_income:,.0f}/month.",
                    hard_pull_performed=True,
                    income_verification_method="payslips",
                    kyc_mode="standard",
                    watch_points_triggered=watch_points,
                )

        # -------------------------------------------------------------
        # Rule 1: Super Prime (CIBIL >= 780)
        # -------------------------------------------------------------
        if score >= self.config.CIBIL_SUPER_PRIME_MIN:
            watch_points.append("Super prime: score-safe soft check shows indicative offer; hard pull waits for customer yes.")
            watch_points.append("Income waived: pre-approved on bureau strength. eKYC is very last step after card selection.")
            return DecisionResult(
                status=ApplicationStatus.APPROVE,
                path=DecisionPath.SUPER_PRIME,
                credit_limit=self.config.SUPER_PRIME_LIMIT_DEFAULT,
                product_name="Infinia Reserve Metal Card",
                reason=f"Exceptional credit score ({score}). Income verification waived on bureau strength.",
                hard_pull_performed=True,
                income_verification_method="waived_super_prime",
                kyc_mode="ekyc_last",
                watch_points_triggered=watch_points,
            )

        # -------------------------------------------------------------
        # Rule 2: Prime (CIBIL 740 - 779)
        # -------------------------------------------------------------
        if score >= self.config.CIBIL_PRIME_MIN:
            bureau_income = bureau.bureau_estimated_monthly_income or 100000.0
            limit = int(bureau_income * self.config.PRIME_LIMIT_MULTIPLIER)
            watch_points.append(f"Prime: income derived from bureau (₹{bureau_income:,.0f}), skipping painful income question.")
            if customer.residence_type == "owned" and customer.marital_status == "married":
                watch_points.append("Owns home + married with children -> lightest address verification.")
            return DecisionResult(
                status=ApplicationStatus.APPROVE,
                path=DecisionPath.PRIME,
                credit_limit=limit,
                product_name="Regalia Gold Credit Card",
                reason=f"Prime credit score ({score}). Income estimated from bureau records with expedited verification.",
                hard_pull_performed=True,
                income_verification_method="bureau_derived",
                kyc_mode="light_address" if customer.residence_type == "owned" else "standard",
                watch_points_triggered=watch_points,
            )

        # -------------------------------------------------------------
        # Rules 3, 4, 5: Near Prime (CIBIL 690 - 739)
        # -------------------------------------------------------------
        if score >= self.config.CIBIL_NEAR_PRIME_MIN:
            stated_income = customer.stated_monthly_income or bureau.bureau_estimated_monthly_income or 60000.0
            existing_emis = customer.existing_monthly_emis
            
            # Scenario 5: PG living + New Job (< 24 months)
            is_pg = customer.residence_type.lower() == self.config.PG_RESIDENCE_KEYWORD
            is_new_job = customer.job_tenure_months < self.config.MIN_STABLE_JOB_MONTHS
            
            if is_pg and is_new_job:
                watch_points.append("PG + new job: thin stability; hard inquiry held until AA confirms income first.")
            elif is_pg and not is_new_job:
                # Scenario 4: PG living + Stable Job (>= 24 months)
                watch_points.append(f"PG address compensated by {customer.job_tenure_months // 12} yrs at employer -> no stricter address check.")
            
            # Scenario 3: FOIR calculation
            proposed_limit = int(stated_income * self.config.NEAR_PRIME_LIMIT_MULTIPLIER)
            notional_emi = proposed_limit * self.config.NOTIONAL_CARD_EMI_RATE
            foir = (existing_emis + notional_emi) / stated_income if stated_income > 0 else 1.0
            
            # Adjust limit if FOIR > 50%
            if foir > self.config.MAX_FOIR:
                max_allowable_emi = (stated_income * self.config.MAX_FOIR) - existing_emis
                if max_allowable_emi > 0:
                    proposed_limit = int(max_allowable_emi / self.config.NOTIONAL_CARD_EMI_RATE)
                    foir = (existing_emis + (proposed_limit * self.config.NOTIONAL_CARD_EMI_RATE)) / stated_income
            
            watch_points.append(f"Near-prime: stated income ₹{stated_income:,.0f}, EMIs ₹{existing_emis:,.0f}; FOIR checked ({foir*100:.1f}%).")
            
            return DecisionResult(
                status=ApplicationStatus.APPROVE,
                path=DecisionPath.NEAR_PRIME,
                credit_limit=proposed_limit,
                product_name="Millennia Select Credit Card",
                reason=f"Near-prime credit score ({score}). Approved with FOIR affordability check ({foir*100:.1f}%).",
                hard_pull_performed=True,
                income_verification_method="stated_foir" if not (is_pg and is_new_job) else "account_aggregator",
                kyc_mode="standard",
                foir=round(foir, 3),
                watch_points_triggered=watch_points,
            )

        # Fallback default
        return DecisionResult(
            status=ApplicationStatus.SECURED_OFFER,
            path=DecisionPath.SECURED,
            credit_limit=self.config.SECURED_DEFAULT_LIMIT,
            product_name="Step-Up Secured Credit Builder",
            reason="Application routed to secured credit builder card.",
            hard_pull_performed=False,
            income_verification_method="standard",
            kyc_mode="standard",
            watch_points_triggered=watch_points,
        )

"""Credit Card Decision Engine Configuration.

All credit thresholds, bureau score bands, FOIR limits, and policy rules
are defined here in a single file as required by the specification.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class EngineConfig:
    # --- Bureau Score Bands ---
    CIBIL_SUPER_PRIME_MIN: int = 780  # >= 780: Super Prime (income waived, soft check first)
    CIBIL_PRIME_MIN: int = 740        # 740 - 779: Prime (bureau derived income, light KYC)
    CIBIL_NEAR_PRIME_MIN: int = 690   # 690 - 739: Near Prime (stated income, FOIR checked)
    # < 690 -> Low score -> Secured Credit-Builder Card

    # --- Income & NTC (New-To-Credit) Thresholds ---
    MIN_UNSECURED_INCOME: float = 30000.0  # Min monthly income for unsecured card
    OVERSTATED_INCOME_TOLERANCE: float = 0.25  # Max allowable discrepancy (25%) before AA overrides stated income

    # --- FOIR (Fixed Obligation to Income Ratio) ---
    MAX_FOIR: float = 0.50  # 50% max allowable FOIR: (existing EMIs + card notional EMI) / income
    NOTIONAL_CARD_EMI_RATE: float = 0.05  # 5% of proposed card limit counted as notional monthly EMI

    # --- Employment & Residence Stability ---
    MIN_STABLE_JOB_MONTHS: int = 24  # 2 years (24 months) at current employer considered stable
    PG_RESIDENCE_KEYWORD: str = "pg"  # Identifier for PG / hostel living

    # --- Limit Sizing Multipliers ---
    SUPER_PRIME_LIMIT_DEFAULT: int = 350000
    PRIME_LIMIT_MULTIPLIER: float = 2.5
    NEAR_PRIME_LIMIT_MULTIPLIER: float = 1.8
    SECURED_DEFAULT_LIMIT: int = 25000
    STUDENT_DEFAULT_LIMIT: int = 20000


# Singleton instance of engine config
CONFIG = EngineConfig()

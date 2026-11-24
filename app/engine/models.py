"""Data models for customer application and decision engine."""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class ApplicationStatus(str, Enum):
    APPROVE = "approve"
    SECURED_OFFER = "secured_offer"
    DECLINE = "decline"


class DecisionPath(str, Enum):
    SUPER_PRIME = "super_prime"
    PRIME = "prime"
    NEAR_PRIME = "near_prime"
    SECURED = "secured"
    STUDENT = "student"
    ETB_PREAPPROVED = "etb_preapproved"


class JourneyStep(str, Enum):
    INIT = "init"
    IDENTIFICATION = "identification"
    CONSENT_SOFT_PULL = "consent_soft_pull"
    INCOME_DECLARATION = "income_declaration"
    AA_CONSENT = "aa_consent"
    DOCUMENT_UPLOAD = "document_upload"
    CARD_SELECTION = "card_selection"
    CONSENT_HARD_PULL = "consent_hard_pull"
    EKYC = "ekyc"
    FINAL_DECISION = "final_decision"


@dataclass
class CustomerProfile:
    id: str
    name: str
    segment: str
    age: int = 28
    is_student: bool = False
    is_etb: bool = False  # Existing To Bank
    has_preapproved_offer: bool = False
    preapproved_limit: Optional[int] = None
    
    # Employment & Residence
    employer: Optional[str] = None
    job_tenure_months: int = 0
    residence_type: str = "owned"  # "owned", "rented", "pg"
    residence_duration_months: int = 24
    marital_status: str = "single"  # "single", "married"
    dependents: int = 0

    # Financial declarations
    stated_monthly_income: Optional[float] = None
    existing_monthly_emis: float = 0.0
    payslips_uploaded: int = 0  # Number of payslips uploaded
    
    # Verification flags
    aa_connected: bool = False
    aa_verified_income: Optional[float] = None
    soft_pull_consented: bool = False
    hard_pull_consented: bool = False
    ekyc_completed: bool = False


@dataclass
class BureauRecord:
    cibil_score: Optional[int] = None  # None indicates New-To-Credit (NTC)
    bureau_estimated_monthly_income: Optional[float] = None
    total_active_accounts: int = 0
    delinquencies_last_24m: int = 0


@dataclass
class DecisionResult:
    status: ApplicationStatus
    path: DecisionPath
    credit_limit: int
    product_name: str
    reason: str
    hard_pull_performed: bool
    income_verification_method: str
    kyc_mode: str
    foir: Optional[float] = None
    watch_points_triggered: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

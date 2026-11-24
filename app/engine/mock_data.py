"""Mock external services: Bureau (CIBIL) and Account Aggregator (AA)."""
from typing import Optional, Dict
from app.engine.models import BureauRecord

# Pre-configured mock bureau database keyed by persona id
_MOCK_BUREAU_DB: Dict[str, BureauRecord] = {
    "ntb_super_prime": BureauRecord(cibil_score=810, bureau_estimated_monthly_income=140000.0, total_active_accounts=5),
    "ntb_prime": BureauRecord(cibil_score=752, bureau_estimated_monthly_income=110000.0, total_active_accounts=4),
    "ntb_near_prime": BureauRecord(cibil_score=705, bureau_estimated_monthly_income=65000.0, total_active_accounts=2),
    "ntb_pg_stable": BureauRecord(cibil_score=712, bureau_estimated_monthly_income=58000.0, total_active_accounts=2),
    "ntb_pg_new_job": BureauRecord(cibil_score=710, bureau_estimated_monthly_income=55000.0, total_active_accounts=1),
    "ntc_unsecured": BureauRecord(cibil_score=None, bureau_estimated_monthly_income=None),  # NTC
    "ntc_aa": BureauRecord(cibil_score=None, bureau_estimated_monthly_income=None),         # NTC
    "ntc_overstated": BureauRecord(cibil_score=None, bureau_estimated_monthly_income=None), # NTC
    "ntc_secured": BureauRecord(cibil_score=None, bureau_estimated_monthly_income=None),    # NTC
    "ntb_low_score": BureauRecord(cibil_score=640, bureau_estimated_monthly_income=45000.0, total_active_accounts=3),
    "student": BureauRecord(cibil_score=None, bureau_estimated_monthly_income=None),        # Student
    "etb_preapproved": BureauRecord(cibil_score=790, bureau_estimated_monthly_income=120000.0, total_active_accounts=3),
}

# Pre-configured mock Account Aggregator data (verified monthly net salary credits)
_MOCK_AA_DB: Dict[str, float] = {
    "ntb_pg_new_job": 55000.0,
    "ntc_aa": 68000.0,
    "ntc_overstated": 24000.0,
    "ntc_secured": 22000.0,
}


def lookup_mock_bureau(persona_id: str) -> BureauRecord:
    """Fetch mock bureau report for persona."""
    return _MOCK_BUREAU_DB.get(persona_id, BureauRecord(cibil_score=None, bureau_estimated_monthly_income=None))


def lookup_mock_aa_income(persona_id: str) -> Optional[float]:
    """Fetch mock Account Aggregator verified monthly income."""
    return _MOCK_AA_DB.get(persona_id, None)

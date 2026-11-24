"""Acceptance tests for Decision Engine against all 12 personas from SCENARIOS.md."""
import pytest
from app.engine.rules import DecisionEngine
from app.engine.config import CONFIG
from app.personas import ALL_PERSONAS, get_persona
from app.engine.models import ApplicationStatus, DecisionPath


@pytest.fixture
def engine():
    return DecisionEngine(CONFIG)


@pytest.mark.parametrize("persona_id", list(ALL_PERSONAS.keys()))
def test_all_12_scenarios_status_and_path(engine, persona_id):
    """Assert each persona produces the exact expected status and expected path from SCENARIOS.md."""
    persona = get_persona(persona_id)
    assert persona is not None
    
    result = engine.evaluate(persona.profile)
    
    assert result.status == persona.expected_status, (
        f"Failed status for {persona.id}: expected {persona.expected_status.value}, got {result.status.value}"
    )
    assert result.path == persona.expected_path, (
        f"Failed path for {persona.id}: expected {persona.expected_path.value}, got {result.path.value}"
    )
    assert len(result.watch_points_triggered) > 0


def test_scenario_1_super_prime(engine):
    """Vikram Sethi: CIBIL 810 -> Super Prime, income waived, soft check first."""
    p = get_persona("ntb_super_prime")
    res = engine.evaluate(p.profile)
    assert res.status == ApplicationStatus.APPROVE
    assert res.path == DecisionPath.SUPER_PRIME
    assert res.credit_limit >= 300000
    assert res.income_verification_method == "waived_super_prime"
    assert res.kyc_mode == "ekyc_last"


def test_scenario_2_prime(engine):
    """Priya Nair: CIBIL 752 -> Prime, derived income from bureau, light KYC."""
    p = get_persona("ntb_prime")
    res = engine.evaluate(p.profile)
    assert res.status == ApplicationStatus.APPROVE
    assert res.path == DecisionPath.PRIME
    assert res.income_verification_method == "bureau_derived"
    assert res.kyc_mode == "light_address"


def test_scenario_3_near_prime_foir(engine):
    """Arjun Mehta: CIBIL 705 -> Near Prime, stated income ₹65k, EMIs ₹8k, FOIR checked."""
    p = get_persona("ntb_near_prime")
    res = engine.evaluate(p.profile)
    assert res.status == ApplicationStatus.APPROVE
    assert res.path == DecisionPath.NEAR_PRIME
    assert res.foir is not None
    assert res.foir <= CONFIG.MAX_FOIR


def test_scenario_4_pg_stable(engine):
    """Aarav Menon: PG resident, but 3 years at same employer -> no strict address check."""
    p = get_persona("ntb_pg_stable")
    res = engine.evaluate(p.profile)
    assert res.status == ApplicationStatus.APPROVE
    assert res.path == DecisionPath.NEAR_PRIME


def test_scenario_5_pg_new_job(engine):
    """Nisha Kapoor: PG resident, job started 5 months ago -> AA verified income first."""
    p = get_persona("ntb_pg_new_job")
    res = engine.evaluate(p.profile)
    assert res.status == ApplicationStatus.APPROVE
    assert res.path == DecisionPath.NEAR_PRIME
    assert res.income_verification_method == "account_aggregator"


def test_scenario_6_ntc_unsecured(engine):
    """Meera Iyer: New to credit, ₹85k income, 3 payslips -> unsecured near prime."""
    p = get_persona("ntc_unsecured")
    res = engine.evaluate(p.profile)
    assert res.status == ApplicationStatus.APPROVE
    assert res.path == DecisionPath.NEAR_PRIME
    assert res.income_verification_method == "payslips"


def test_scenario_7_ntc_aa(engine):
    """Tanvi Shah: New to credit, AA confirms ₹68k -> limit sized by AA figure."""
    p = get_persona("ntc_aa")
    res = engine.evaluate(p.profile)
    assert res.status == ApplicationStatus.APPROVE
    assert res.path == DecisionPath.NEAR_PRIME
    assert res.income_verification_method == "account_aggregator"
    assert res.credit_limit == int(68000.0 * CONFIG.NEAR_PRIME_LIMIT_MULTIPLIER)


def test_scenario_8_ntc_overstated(engine):
    """Imran Qureshi: Claims ₹85k, AA shows ₹24k (< 30k) -> secured credit builder."""
    p = get_persona("ntc_overstated")
    res = engine.evaluate(p.profile)
    assert res.status == ApplicationStatus.SECURED_OFFER
    assert res.path == DecisionPath.SECURED


def test_scenario_9_ntc_secured_low_income(engine):
    """Kavya Rao: New to credit, ₹22k income (< 30k) -> secured credit builder."""
    p = get_persona("ntc_secured")
    res = engine.evaluate(p.profile)
    assert res.status == ApplicationStatus.SECURED_OFFER
    assert res.path == DecisionPath.SECURED


def test_scenario_10_ntb_low_score(engine):
    """Rohan Das: CIBIL 640 (< 690) -> secured credit builder, income waived."""
    p = get_persona("ntb_low_score")
    res = engine.evaluate(p.profile)
    assert res.status == ApplicationStatus.SECURED_OFFER
    assert res.path == DecisionPath.SECURED


def test_scenario_11_student(engine):
    """Ananya Gupta: Student, age 20, zero income -> student FD-backed card, no bureau pull."""
    p = get_persona("student")
    res = engine.evaluate(p.profile)
    assert res.status == ApplicationStatus.SECURED_OFFER
    assert res.path == DecisionPath.STUDENT
    assert res.hard_pull_performed is False
    assert res.income_verification_method == "none_student"


def test_scenario_12_etb_preapproved(engine):
    """Asha Rao: Existing customer with pre-approved offer -> instant approve, 0 bureau pull."""
    p = get_persona("etb_preapproved")
    res = engine.evaluate(p.profile)
    assert res.status == ApplicationStatus.APPROVE
    assert res.path == DecisionPath.ETB_PREAPPROVED
    assert res.hard_pull_performed is False
    assert res.credit_limit == 250000

"""The 12 acceptance test personas from SCENARIOS.md.

Includes:
- Profile specifications for decision engine
- Scripted natural Hinglish conversation turns for auto-play
- Expected decision status and decision path
- Watch points to be verified in UI and tests
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from app.engine.models import CustomerProfile, ApplicationStatus, DecisionPath


@dataclass
class PersonaDefinition:
    id: str
    name: str
    segment: str
    customer_summary: str
    mock_data_summary: str
    expected_status: ApplicationStatus
    expected_path: DecisionPath
    profile: CustomerProfile
    watch_for: List[str]
    scripted_turns: List[Dict[str, str]] = field(default_factory=list)


ALL_PERSONAS: Dict[str, PersonaDefinition] = {
    # -------------------------------------------------------------
    # 1. Super Prime: Vikram Sethi
    # -------------------------------------------------------------
    "ntb_super_prime": PersonaDefinition(
        id="ntb_super_prime",
        name="Vikram Sethi",
        segment="New to bank",
        customer_summary="Salaried corporate leader with stellar credit track record",
        mock_data_summary="CIBIL 810, bureau income est. ₹1,40,000/month",
        expected_status=ApplicationStatus.APPROVE,
        expected_path=DecisionPath.SUPER_PRIME,
        profile=CustomerProfile(
            id="ntb_super_prime",
            name="Vikram Sethi",
            segment="New to bank",
            age=36,
            stated_monthly_income=140000.0,
            employer="McKinsey & Company",
            job_tenure_months=60,
            residence_type="owned",
            soft_pull_consented=True,
            hard_pull_consented=True,
        ),
        watch_for=[
            "Score-safe soft check shows indicative offer first",
            "Hard pull waits for customer's confirmation",
            "Income proof waived on bureau strength (CIBIL 810)",
            "eKYC scheduled as the very final step after card selection",
        ],
        scripted_turns=[
            {"role": "user", "text": "Namaste, mujhe ek premium credit card ke liye apply karna hai."},
            {"role": "user", "text": "Mera naam Vikram Sethi hai, mobile number 9876543210."},
            {"role": "user", "text": "Haan bilkul, aap bureau soft-check run kar sakte ho."},
            {"role": "user", "text": "Infinia card offers bohot acche hain, I want to proceed with this."},
            {"role": "user", "text": "Aadhaar eKYC complete kar dijiye."},
        ],
    ),

    # -------------------------------------------------------------
    # 2. Prime: Priya Nair
    # -------------------------------------------------------------
    "ntb_prime": PersonaDefinition(
        id="ntb_prime",
        name="Priya Nair",
        segment="New to bank",
        customer_summary="Salaried professional, owns home, married with 2 children",
        mock_data_summary="CIBIL 752, bureau income est. ₹1,10,000",
        expected_status=ApplicationStatus.APPROVE,
        expected_path=DecisionPath.PRIME,
        profile=CustomerProfile(
            id="ntb_prime",
            name="Priya Nair",
            segment="New to bank",
            age=34,
            stated_monthly_income=110000.0,
            employer="Infosys Technologies",
            job_tenure_months=48,
            residence_type="owned",
            marital_status="married",
            dependents=2,
            soft_pull_consented=True,
            hard_pull_consented=True,
        ),
        watch_for=[
            "Income DERIVED from bureau (₹1,10,000) - painful income question skipped",
            "Owns home + married with 2 kids -> lightest address verification applied",
            "Instant Regalia Gold card recommendation",
        ],
        scripted_turns=[
            {"role": "user", "text": "Hello, credit card application start karni hai."},
            {"role": "user", "text": "I am Priya Nair, salaried, Bengaluru mein apna ghar hai."},
            {"role": "user", "text": "Sure, bureau check ke liye consent de rahi hoon."},
            {"role": "user", "text": "Great! Bureau income derived perfectly, no salary slips needed."},
            {"role": "user", "text": "Yes, approve Regalia Gold card."},
        ],
    ),

    # -------------------------------------------------------------
    # 3. Near-Prime: Arjun Mehta
    # -------------------------------------------------------------
    "ntb_near_prime": PersonaDefinition(
        id="ntb_near_prime",
        name="Arjun Mehta",
        segment="New to bank",
        customer_summary="Salaried executive with moderate credit history",
        mock_data_summary="CIBIL 705; types income ₹65,000, EMIs ₹8,000",
        expected_status=ApplicationStatus.APPROVE,
        expected_path=DecisionPath.NEAR_PRIME,
        profile=CustomerProfile(
            id="ntb_near_prime",
            name="Arjun Mehta",
            segment="New to bank",
            age=29,
            stated_monthly_income=65000.0,
            existing_monthly_emis=8000.0,
            employer="Tata Consumer Products",
            job_tenure_months=36,
            residence_type="rented",
            soft_pull_consented=True,
            hard_pull_consented=True,
        ),
        watch_for=[
            "Mid-band credit (CIBIL 705) -> typed income and EMIs (never documents)",
            "FOIR checked: existing EMIs ₹8,000 + notional card EMI within 50% limit",
            "Credit limit sized specifically to serviceable disposable income",
        ],
        scripted_turns=[
            {"role": "user", "text": "Hi, mujhe Millennia card chahiye tha online shopping ke liye."},
            {"role": "user", "text": "Arjun Mehta, monthly in-hand around ₹65,000 hai."},
            {"role": "user", "text": "Sirf ek bike loan EMI hai ₹8,000 per month."},
            {"role": "user", "text": "Bureau score check kar lo, no problem."},
            {"role": "user", "text": "Card limit looks good, please confirm my application."},
        ],
    ),

    # -------------------------------------------------------------
    # 4. PG Stable: Aarav Menon
    # -------------------------------------------------------------
    "ntb_pg_stable": PersonaDefinition(
        id="ntb_pg_stable",
        name="Aarav Menon",
        segment="New to bank",
        customer_summary="Young professional, lives in PG, 3 years at same employer",
        mock_data_summary="CIBIL 712; income ₹58,000, EMIs ₹6,000; PG 1 yr; single",
        expected_status=ApplicationStatus.APPROVE,
        expected_path=DecisionPath.NEAR_PRIME,
        profile=CustomerProfile(
            id="ntb_pg_stable",
            name="Aarav Menon",
            segment="New to bank",
            age=26,
            stated_monthly_income=58000.0,
            existing_monthly_emis=6000.0,
            employer="Swiggy Delivery HQ",
            job_tenure_months=36,
            residence_type="pg",
            residence_duration_months=12,
            marital_status="single",
            soft_pull_consented=True,
            hard_pull_consented=True,
        ),
        watch_for=[
            "PG address normally looks shaky, but 3 years at same employer lifts confidence",
            "No stricter physical address checks required due to job stability offset",
            "Near-prime approval with standard digital onboarding",
        ],
        scripted_turns=[
            {"role": "user", "text": "Hey, Aarav Menon here. Naya credit card dekh raha hoon."},
            {"role": "user", "text": "Currently PG mein rehta hoon Bengaluru mein, 1 saal se."},
            {"role": "user", "text": "Same company mein 3 saal se kaam kar raha hoon, salary ₹58k."},
            {"role": "user", "text": "EMI ₹6,000 chal rahi hai personal loan ki."},
            {"role": "user", "text": "Awesome, thanks for considering job stability! Confirm card."},
        ],
    ),

    # -------------------------------------------------------------
    # 5. PG New Job: Nisha Kapoor
    # -------------------------------------------------------------
    "ntb_pg_new_job": PersonaDefinition(
        id="ntb_pg_new_job",
        name="Nisha Kapoor",
        segment="New to bank",
        customer_summary="Recent relocation, PG residence, job started 5 months ago",
        mock_data_summary="Account Aggregator (AA) verifies income ₹55,000; CIBIL 710",
        expected_status=ApplicationStatus.APPROVE,
        expected_path=DecisionPath.NEAR_PRIME,
        profile=CustomerProfile(
            id="ntb_pg_new_job",
            name="Nisha Kapoor",
            segment="New to bank",
            age=24,
            stated_monthly_income=55000.0,
            employer="Flipkart Internet",
            job_tenure_months=5,
            residence_type="pg",
            residence_duration_months=5,
            aa_connected=True,
            aa_verified_income=55000.0,
            soft_pull_consented=True,
            hard_pull_consented=True,
        ),
        watch_for=[
            "Thin stability on both fronts (recent move + new job 5 months)",
            "Score-affecting hard credit inquiry held initially",
            "Income confirmed via Account Aggregator (AA) first, then pull runs",
        ],
        scripted_turns=[
            {"role": "user", "text": "Hi, Nisha here. 5 months pehle Mumbai aayi hoon for my new job."},
            {"role": "user", "text": "Filhal PG mein hoon and Flipkart mein job hai."},
            {"role": "user", "text": "Account Aggregator connect kar leti hoon for salary confirmation."},
            {"role": "user", "text": "OTP verified for AA, income confirmed ₹55,000."},
            {"role": "user", "text": "Ab bureau pull karke card issue kar dijiye."},
        ],
    ),

    # -------------------------------------------------------------
    # 6. NTC Unsecured: Meera Iyer
    # -------------------------------------------------------------
    "ntc_unsecured": PersonaDefinition(
        id="ntc_unsecured",
        name="Meera Iyer",
        segment="New to credit",
        customer_summary="High-earning professional with zero prior credit footprint",
        mock_data_summary="No bureau record (NTC); earns ₹85,000/month; uploads 3 payslips",
        expected_status=ApplicationStatus.APPROVE,
        expected_path=DecisionPath.NEAR_PRIME,
        profile=CustomerProfile(
            id="ntc_unsecured",
            name="Meera Iyer",
            segment="New to credit",
            age=27,
            stated_monthly_income=85000.0,
            employer="Deloitte India",
            job_tenure_months=18,
            payslips_uploaded=3,
        ),
        watch_for=[
            "No credit history is a starting point, NOT a reason to decline or force secured",
            "High earnings (₹85k) unlock unsecured entry card",
            "Income not taken on pure trust -> backed by 3 uploaded payslips",
        ],
        scripted_turns=[
            {"role": "user", "text": "Hello, maine pehle kabhi credit card ya loan nahi liya."},
            {"role": "user", "text": "Meera Iyer naam hai, Deloitte mein ₹85,000 monthly salary hai."},
            {"role": "user", "text": "Maine apni pichli 3 salary slips upload kar di hain."},
            {"role": "user", "text": "Bureau pull empty aayega because I am new to credit."},
            {"role": "user", "text": "Great, thanks for giving an unsecured card to NTC!"},
        ],
    ),

    # -------------------------------------------------------------
    # 7. NTC via AA: Tanvi Shah
    # -------------------------------------------------------------
    "ntc_aa": PersonaDefinition(
        id="ntc_aa",
        name="Tanvi Shah",
        segment="New to credit",
        customer_summary="First-time borrower verifying salary via Account Aggregator",
        mock_data_summary="AA shows ₹68,000 (AA figure sizes the limit); states ₹70,000",
        expected_status=ApplicationStatus.APPROVE,
        expected_path=DecisionPath.NEAR_PRIME,
        profile=CustomerProfile(
            id="ntc_aa",
            name="Tanvi Shah",
            segment="New to credit",
            age=25,
            stated_monthly_income=70000.0,
            aa_connected=True,
            aa_verified_income=68000.0,
        ),
        watch_for=[
            "Single digital consent reads income directly from bank statement via AA",
            "The verified AA figure (₹68,000), not the claimed ₹70k, sizes credit limit",
            "Smooth NTC paperless onboarding",
        ],
        scripted_turns=[
            {"role": "user", "text": "Hi, pehla credit card chahiye online spends ke liye."},
            {"role": "user", "text": "Tanvi Shah, salary approx 70k aati hai account mein."},
            {"role": "user", "text": "Haan, main Account Aggregator se apna salary account link karungi."},
            {"role": "user", "text": "AA consent approved, net credit shows ₹68,000."},
            {"role": "user", "text": "Looks great, please approve the limit based on AA."},
        ],
    ),

    # -------------------------------------------------------------
    # 8. NTC Overstated: Imran Qureshi
    # -------------------------------------------------------------
    "ntc_overstated": PersonaDefinition(
        id="ntc_overstated",
        name="Imran Qureshi",
        segment="New to credit",
        customer_summary="Stated income contradicted by actual bank cashflows",
        mock_data_summary="Claims ₹85,000, but AA shows only ₹24,000 (discrepancy > 25%)",
        expected_status=ApplicationStatus.SECURED_OFFER,
        expected_path=DecisionPath.SECURED,
        profile=CustomerProfile(
            id="ntc_overstated",
            name="Imran Qureshi",
            segment="New to credit",
            age=28,
            stated_monthly_income=85000.0,
            aa_connected=True,
            aa_verified_income=24000.0,
        ),
        watch_for=[
            "Typed income (₹85k) contradicted by AA verification (₹24k)",
            "Discrepancy exceeds 25% tolerance; AA figure is under ₹30,000 cutoff",
            "Dignified pivot: offered secured credit-builder card fitting real income",
        ],
        scripted_turns=[
            {"role": "user", "text": "Hello, credit card apply karna hai Imran Qureshi."},
            {"role": "user", "text": "Meri monthly income ₹85,000 hai."},
            {"role": "user", "text": "Okay, Account Aggregator connect kar raha hoon."},
            {"role": "user", "text": "Oh, bank statement mein ₹24,000 regular credits dikha raha hai."},
            {"role": "user", "text": "Secured credit-builder card works for me to build history."},
        ],
    ),

    # -------------------------------------------------------------
    # 9. NTC Low Income: Kavya Rao
    # -------------------------------------------------------------
    "ntc_secured": PersonaDefinition(
        id="ntc_secured",
        name="Kavya Rao",
        segment="New to credit",
        customer_summary="Entry-level earner below unsecured minimum income cutoff",
        mock_data_summary="Income ₹22,000/month (< ₹30,000 threshold), no credit history",
        expected_status=ApplicationStatus.SECURED_OFFER,
        expected_path=DecisionPath.SECURED,
        profile=CustomerProfile(
            id="ntc_secured",
            name="Kavya Rao",
            segment="New to credit",
            age=23,
            stated_monthly_income=22000.0,
            aa_connected=True,
            aa_verified_income=22000.0,
        ),
        watch_for=[
            "Only below ₹30,000 cutoff does secured card naturally appear for NTC",
            "Framed as credit-builder: FD earns interest while on-time bills build CIBIL",
            "Clear milestone: path to graduate to unsecured card in 6-12 months",
        ],
        scripted_turns=[
            {"role": "user", "text": "Namaste, mera pehla job hai aur pehla credit card chahiye."},
            {"role": "user", "text": "Kavya Rao, meri monthly salary ₹22,000 aati hai."},
            {"role": "user", "text": "Pehle koi loan ya CIBIL score nahi hai."},
            {"role": "user", "text": "Understood, ₹30k se kam salary pe secured credit-builder milta hai."},
            {"role": "user", "text": "Haan FD-backed card start kar dijiye, I will build my CIBIL score."},
        ],
    ),

    # -------------------------------------------------------------
    # 10. NTB Low Score: Rohan Das
    # -------------------------------------------------------------
    "ntb_low_score": PersonaDefinition(
        id="ntb_low_score",
        name="Rohan Das",
        segment="New to bank",
        customer_summary="Salaried applicant with bruised credit history from past defaults",
        mock_data_summary="CIBIL 640 (< 690 threshold)",
        expected_status=ApplicationStatus.SECURED_OFFER,
        expected_path=DecisionPath.SECURED,
        profile=CustomerProfile(
            id="ntb_low_score",
            name="Rohan Das",
            segment="New to bank",
            age=31,
            stated_monthly_income=75000.0,
            soft_pull_consented=True,
            hard_pull_consented=True,
        ),
        watch_for=[
            "Score under 690 immediately triggers secured credit-builder pathway",
            "Income not asked/probed because it wouldn't change the offer outcome",
            "Empathetic credit repair framing without humiliating rejection",
        ],
        scripted_turns=[
            {"role": "user", "text": "Hello, Rohan Das here. Credit card apply karna chahta hoon."},
            {"role": "user", "text": "Pehle kuch delays the payments mein, but now stable."},
            {"role": "user", "text": "Yes, bureau check run kar lijiye."},
            {"role": "user", "text": "Score 640 hai, I know bruised hai."},
            {"role": "user", "text": "FD-backed credit repair card le leta hoon to repair my score."},
        ],
    ),

    # -------------------------------------------------------------
    # 11. Student: Ananya Gupta
    # -------------------------------------------------------------
    "student": PersonaDefinition(
        id="student",
        name="Ananya Gupta",
        segment="New to credit",
        customer_summary="College student, age 20, zero employment income",
        mock_data_summary="No bureau pull, no income asked; FD-backed student card",
        expected_status=ApplicationStatus.SECURED_OFFER,
        expected_path=DecisionPath.STUDENT,
        profile=CustomerProfile(
            id="student",
            name="Ananya Gupta",
            segment="New to credit",
            age=20,
            is_student=True,
            stated_monthly_income=0.0,
        ),
        watch_for=[
            "Zero bureau pull performed (protects future credit file)",
            "Zero income questions asked (student status recognized upfront)",
            "FD-backed first card offered instead of a harsh decline",
        ],
        scripted_turns=[
            {"role": "user", "text": "Hey! Main college student hoon aur mujhe card chahiye for subscriptions."},
            {"role": "user", "text": "Ananya Gupta, age 20, currently 3rd year engineering."},
            {"role": "user", "text": "Mere paas koi salary ya income proof nahi hai."},
            {"role": "user", "text": "Great that you didn't do a bureau pull!"},
            {"role": "user", "text": "Small FD open karke student card activate kar dijiye."},
        ],
    ),

    # -------------------------------------------------------------
    # 12. ETB Pre-Approved: Asha Rao
    # -------------------------------------------------------------
    "etb_preapproved": PersonaDefinition(
        id="etb_preapproved",
        name="Asha Rao",
        segment="Existing customer",
        customer_summary="6-year banking relationship with pre-approved credit card offer",
        mock_data_summary="Pre-approved offer ₹2,50,000 on file; KYC and income already held",
        expected_status=ApplicationStatus.APPROVE,
        expected_path=DecisionPath.ETB_PREAPPROVED,
        profile=CustomerProfile(
            id="etb_preapproved",
            name="Asha Rao",
            segment="Existing customer",
            age=38,
            is_etb=True,
            has_preapproved_offer=True,
            preapproved_limit=250000,
        ),
        watch_for=[
            "Identity, income and KYC already on file from 6-year bank relationship",
            "Nothing re-asked; zero bureau inquiry initiated",
            "Instant one-tap digital issuance",
        ],
        scripted_turns=[
            {"role": "user", "text": "Namaste, Asha Rao here. Mujhe netbanking par pre-approved offer dikha tha."},
            {"role": "user", "text": "Main 6 saal se aapke bank ki account holder hoon."},
            {"role": "user", "text": "Yes, pre-approved limit ₹2,50,000 accept karti hoon."},
            {"role": "user", "text": "Superb, no new paperwork or bureau pull needed!"},
            {"role": "user", "text": "Please dispatch my Millennia Platinum card."},
        ],
    ),
}


def get_persona(persona_id: str) -> Optional[PersonaDefinition]:
    """Retrieve persona definition by id."""
    return ALL_PERSONAS.get(persona_id)


def list_personas() -> List[Dict[str, Any]]:
    """Summary list for UI dropdown and auto-play selector."""
    return [
        {
            "id": p.id,
            "name": p.name,
            "segment": p.segment,
            "summary": p.customer_summary,
            "expected_status": p.expected_status.value,
            "expected_path": p.expected_path.value,
            "watch_for": p.watch_for,
            "turns_count": len(p.scripted_turns),
        }
        for p in ALL_PERSONAS.values()
    ]

# The 12 demo scenarios (credit-card onboarding personas)

Taken from the first 12 personas in OmniSpark's `legacy/demo.py`. Each one is a complete,
deterministic customer: who they are to the bank, what the (mock) bureau says, and the answers
they give. The **decision engine** (plain Python rules, never the LLM) must produce the
`expected status` and `expected path` below. These are the acceptance tests.

| # | id | Segment | Customer | Mock data | Expected status | Expected path |
|---|----|---------|----------|-----------|-----------------|---------------|
| 1 | `ntb_super_prime` | New to bank | Vikram Sethi, salaried, strong credit | CIBIL 810, bureau income est. ₹1,40,000/month | approve | super_prime |
| 2 | `ntb_prime` | New to bank | Priya Nair, salaried, good credit; owns her home, married, 2 children | CIBIL 752, bureau income est. ₹1,10,000 | approve | prime |
| 3 | `ntb_near_prime` | New to bank | Arjun Mehta, salaried | CIBIL 705; types income ₹65,000, EMIs ₹8,000 | approve | near_prime |
| 4 | `ntb_pg_stable` | New to bank | Aarav Menon, 26, lives in a PG, 3 years at same employer | CIBIL 712; income ₹58,000, EMIs ₹6,000; PG 1 yr; single | approve | near_prime |
| 5 | `ntb_pg_new_job` | New to bank | Nisha Kapoor, 24, PG, job started 5 months ago | Account Aggregator (AA) verifies income | approve | near_prime |
| 6 | `ntc_unsecured` | New to credit | Meera Iyer, earns ₹85,000/month, no credit history | No bureau record; uploads 3 payslips | approve | near_prime |
| 7 | `ntc_aa` | New to credit | Tanvi Shah, says ₹70,000/month, no credit history | AA shows ₹68,000 (AA figure sizes the limit) | approve | near_prime |
| 8 | `ntc_overstated` | New to credit | Imran Qureshi, claims ₹85,000 | AA shows only ₹24,000 | secured_offer | secured |
| 9 | `ntc_secured` | New to credit | Kavya Rao, ₹22,000/month, no credit history | Income under ₹30,000 | secured_offer | secured |
| 10 | `ntb_low_score` | New to bank | Rohan Das, salaried, bruised credit | CIBIL 640 | secured_offer | secured |
| 11 | `student` | New to credit | Ananya Gupta, 20, student, no income | No bureau pull, no income | secured_offer | student |
| 12 | `etb_preapproved` | Existing customer | Asha Rao, 6 years with the bank | Pre-approved offer on file | approve | etb_preapproved |

## What each scenario should show on screen ("watch for")

1. **Super prime:** a free, score-safe soft check shows an indicative offer first; the hard pull waits for the customer's yes. Income is waived (pre-approved on bureau strength). eKYC is the very last step, after they pick a card.
2. **Prime:** income is DERIVED from the bureau, so the most painful question is skipped. Owns home + married with a child → lightest address verification.
3. **Near-prime:** mid-band credit → typed income and EMIs (never a document), checked against FOIR (fixed obligations to income ratio). The limit is sized to what they can service.
4. **PG, steady job:** a PG address looks shaky, but 3 years at one employer lifts confidence, so no stricter address checks.
5. **PG, new job:** thin on both fronts (recent move + new job), so the hard credit enquiry is held; income is confirmed via AA first, then the score-affecting pull runs.
6. **NTC, earns well:** no credit history is a starting point, NOT a secured card → unsecured entry card; but income isn't taken on trust → 3 payslips.
7. **NTC via AA:** one consent and income is read from bank data; the AA figure (₹68,000), not the claim, sizes the limit.
8. **NTC overstated:** the typed income is contradicted by AA → offered the secured credit-builder that fits real income.
9. **NTC low income:** only here does the secured card appear, framed as a credit-builder (FD keeps earning, on-time payments build CIBIL, path to unsecured).
10. **Low score:** a score under 690 also triggers the secured credit-builder; income isn't asked (it wouldn't change the offer).
11. **Student:** no bureau pull and no income asked; an FD-backed first card instead of a decline.
12. **Existing, pre-approved:** identity, income and KYC already on file, nothing re-asked; no bureau pull; one tap.

## Thresholds the rules need (pick these, keep them in one config file)

- Super prime: CIBIL ≥ 780 · Prime: 740–779 · Near-prime: 690–739 · Below 690 → secured.
- New to credit: no bureau record. Income < ₹30,000 → secured. Claimed income more than ~25% above the AA figure → use AA figure; if that is < ₹30,000 → secured.
- FOIR limit e.g. 50%: (existing EMIs + new card's notional EMI) / income.
- Student (no income) → `student` path (FD-backed card), never a hard bureau pull.
- Existing customer with a pre-approved flag → `etb_preapproved`, no bureau pull.

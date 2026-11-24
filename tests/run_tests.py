"""Standalone test runner for environments without pytest installed.
Runs the exact test suite and asserts all 12 scenario outcomes.
"""
import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.engine.rules import DecisionEngine
from app.engine.config import CONFIG
from app.personas import ALL_PERSONAS, get_persona
from app.engine.models import ApplicationStatus, DecisionPath


def run_all_tests():
    engine = DecisionEngine(CONFIG)
    passed = 0
    failed = 0
    print("======================================================================")
    print("Running Credit Card Decision Engine Acceptance Tests (12 Personas)")
    print("======================================================================")

    for persona_id, persona in ALL_PERSONAS.items():
        try:
            result = engine.evaluate(persona.profile)
            assert result.status == persona.expected_status, (
                f"Status mismatch: expected {persona.expected_status.value}, got {result.status.value}"
            )
            assert result.path == persona.expected_path, (
                f"Path mismatch: expected {persona.expected_path.value}, got {result.path.value}"
            )
            print(f" [PASS] Persona #{len(ALL_PERSONAS) - list(ALL_PERSONAS.keys())[::-1].index(persona_id):2d}: "
                  f"{persona.id:18s} | {persona.name:15s} -> Status: {result.status.value:13s} Path: {result.path.value}")
            passed += 1
        except Exception as e:
            print(f" [FAIL] Persona: {persona.id} - Error: {e}")
            failed += 1

    print("======================================================================")
    print(f"Summary: {passed} passed, {failed} failed out of {len(ALL_PERSONAS)} personas.")
    print("======================================================================")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

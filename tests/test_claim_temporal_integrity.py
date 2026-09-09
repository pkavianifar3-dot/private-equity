import importlib.util
import unittest

import jdatetime


SPEC = importlib.util.spec_from_file_location(
    "validate_atlas",
    "atlas/tools/validate-atlas.py",
)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class ClaimTemporalIntegrityTests(unittest.TestCase):
    def test_start_after_end_rejected(self):
        errors = []
        VALIDATOR.validate_claim_temporal_integrity({"id": "claim:test-order", "temporal": {"start": "1400", "end": "1399", "precision": "year", "status": "known"}}, errors)
        self.assertEqual(len(errors), 1)

    def test_valid_day_temporal(self):
        errors = []
        VALIDATOR.validate_claim_temporal_integrity({"id": "claim:test-day", "temporal": {"start": "1396-02-02", "end": "1397-02-25", "precision": "day", "status": "known"}}, errors)
        self.assertEqual(errors, [])

    def test_valid_month_temporal(self):
        errors = []
        VALIDATOR.validate_claim_temporal_integrity({"id": "claim:test-month", "temporal": {"start": "1390-12", "end": "1395-12", "precision": "month", "status": "known"}}, errors)
        self.assertEqual(errors, [])

    def test_unknown_precision_requires_null_dates(self):
        errors = []
        VALIDATOR.validate_claim_temporal_integrity({"id": "claim:test-unknown", "temporal": {"start": "1405", "end": None, "precision": "unknown", "status": "unknown"}}, errors)
        self.assertEqual(len(errors), 1)

    def test_precision_mismatch_rejected(self):
        errors = []
        VALIDATOR.validate_claim_temporal_integrity({"id": "claim:test-bad", "temporal": {"start": "1405-06", "end": None, "precision": "year", "status": "current"}}, errors)
        self.assertEqual(len(errors), 1)

    def test_valid_year_temporal(self):
        errors = []
        VALIDATOR.validate_claim_temporal_integrity({"id": "claim:test-year", "temporal": {"start": "1405", "end": None, "precision": "year", "status": "current"}}, errors)
        self.assertEqual(errors, [])


    def setUp(self):
        self.today = jdatetime.date(1405, 6, 12)

import importlib.util
import unittest

import jdatetime


SPEC = importlib.util.spec_from_file_location(
    "validate_atlas",
    "atlas/tools/validate-atlas.py",
)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class ClaimReviewMetadataTests(unittest.TestCase):

    def setUp(self):
        self.today = jdatetime.date(1405, 6, 12)

    def test_jalali_month_age(self):
        self.assertEqual(
            VALIDATOR.jalali_month_age("1405-06", self.today),
            0,
        )
        self.assertEqual(
            VALIDATOR.jalali_month_age("1405-05", self.today),
            1,
        )
        self.assertEqual(
            VALIDATOR.jalali_month_age("1404-06", self.today),
            12,
        )

    def test_fresh_claim_has_no_warning(self):
        warnings = []

        VALIDATOR.validate_claim_review_metadata(
            [{
                "id": "claim:test-fresh",
                "last_reviewed": "1405-06",
            }],
            warnings,
            today=self.today,
        )

        self.assertEqual(warnings, [])

    def test_exact_cycle_boundary_has_no_warning(self):
        warnings = []

        VALIDATOR.validate_claim_review_metadata(
            [{
                "id": "claim:test-boundary",
                "last_reviewed": "1404-12",
                "review_cycle_months": 6,
            }],
            warnings,
            today=self.today,
        )

        self.assertEqual(warnings, [])

    def test_overdue_claim_warns(self):
        warnings = []

        VALIDATOR.validate_claim_review_metadata(
            [{
                "id": "claim:test-overdue",
                "last_reviewed": "1404-06",
            }],
            warnings,
            today=self.today,
        )

        self.assertEqual(len(warnings), 1)
        self.assertIn("claim:test-overdue", warnings[0])
        self.assertIn("12 months", warnings[0])

    def test_custom_review_cycle(self):
        warnings = []

        VALIDATOR.validate_claim_review_metadata(
            [{
                "id": "claim:test-custom-cycle",
                "last_reviewed": "1405-01",
                "review_cycle_months": 12,
            }],
            warnings,
            today=self.today,
        )

        self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()

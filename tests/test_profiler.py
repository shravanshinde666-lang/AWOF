"""Focused unit tests for the dataset-agnostic Dataset Intelligence profiler."""

from __future__ import annotations

import json
import unittest

import pandas as pd

from awof.profiler.dataset_profiler import DatasetProfiler


class DatasetProfilerTests(unittest.TestCase):
    """Exercise the public profile contract using small, generated DataFrames."""

    @staticmethod
    def generate_profile(dataframe: pd.DataFrame) -> dict:
        return DatasetProfiler(dataframe).generate_profile()

    @staticmethod
    def type_info(profile: dict, column_name: str) -> dict:
        return next(
            item
            for item in profile["column_types"]
            if item["column"] == column_name
        )

    def test_dataset_summary_reports_dimensions_and_cells(self) -> None:
        profile = self.generate_profile(
            pd.DataFrame(
                {
                    "number": [1, 2, 3],
                    "label": ["one", "two", "three"],
                }
            )
        )

        summary = profile["summary"]
        self.assertEqual(summary["rows"], 3)
        self.assertEqual(summary["columns"], 2)
        self.assertEqual(summary["total_cells"], 6)

    def test_numeric_statistics_include_known_centre_and_spread(self) -> None:
        profile = self.generate_profile(pd.DataFrame({"value": [1, 2, 3, 4, 5]}))

        statistics = profile["columns"]["value"]["numeric_statistics"]
        self.assertEqual(statistics["count"], 5)
        self.assertAlmostEqual(statistics["mean"], 3.0)
        self.assertAlmostEqual(statistics["median"], 3.0)
        self.assertAlmostEqual(statistics["minimum"], 1.0)
        self.assertAlmostEqual(statistics["maximum"], 5.0)
        self.assertAlmostEqual(statistics["range"], 4.0)
        self.assertAlmostEqual(statistics["q1"], 2.0)
        self.assertAlmostEqual(statistics["q2"], 3.0)
        self.assertAlmostEqual(statistics["q3"], 4.0)
        self.assertAlmostEqual(statistics["iqr"], 2.0)

        histogram = profile["columns"]["value"]["distribution"]["histogram"]
        self.assertEqual(sum(histogram["counts"]), 5)
        self.assertEqual(len(histogram["bin_edges"]), len(histogram["counts"]) + 1)

    def test_missing_value_counts_percentages_and_severity(self) -> None:
        profile = self.generate_profile(
            pd.DataFrame({"partially_missing": [1, None, 3, None]})
        )

        summary = profile["summary"]
        missing = profile["columns"]["partially_missing"]["missing"]
        self.assertEqual(summary["missing_cells"], 2)
        self.assertAlmostEqual(summary["missing_percentage"], 50.0)
        self.assertEqual(missing["missing_count"], 2)
        self.assertEqual(missing["non_missing_count"], 2)
        self.assertAlmostEqual(missing["missing_percentage"], 50.0)
        self.assertEqual(missing["severity"], "high")

    def test_duplicate_rows_are_counted_without_mutating_data(self) -> None:
        dataframe = pd.DataFrame({"left": [1, 1, 2], "right": ["a", "a", "b"]})
        profile = self.generate_profile(dataframe)

        self.assertEqual(profile["summary"]["duplicate_rows"], 1)
        self.assertAlmostEqual(profile["summary"]["duplicate_percentage"], 100 / 3)
        self.assertTrue(profile["quality"]["duplicates"]["has_duplicates"])
        self.assertTrue(dataframe.equals(pd.DataFrame({"left": [1, 1, 2], "right": ["a", "a", "b"]})))

    def test_type_detection_handles_representative_attribute_types(self) -> None:
        row_count = 12
        profile = self.generate_profile(
            pd.DataFrame(
                {
                    "integer_feature": list(range(row_count)),
                    "accepted_terms": ["yes", "no"] * (row_count // 2),
                    "plan": ["basic", "standard", "premium"] * 4,
                    "event_date": pd.date_range("2025-01-01", periods=row_count),
                    "description": [
                        f"Customer supplied a detailed free form note number {index}"
                        for index in range(row_count)
                    ],
                    "customer_id": [f"customer-{index:03d}" for index in range(row_count)],
                }
            )
        )

        types = {
            item["column"]: item
            for item in profile["column_types"]
        }
        self.assertEqual(types["integer_feature"]["detected_type"], "integer")
        self.assertIn(types["accepted_terms"]["detected_type"], {"boolean", "binary"})
        self.assertEqual(types["plan"]["detected_type"], "nominal")
        self.assertEqual(types["event_date"]["detected_type"], "datetime")
        self.assertEqual(types["description"]["detected_type"], "text")
        self.assertEqual(types["customer_id"]["detected_type"], "identifier_candidate")
        self.assertTrue(types["customer_id"]["is_identifier_candidate"])

    def test_iqr_outlier_detection_finds_extreme_value(self) -> None:
        profile = self.generate_profile(
            pd.DataFrame({"measurement": [1, 2, 2, 3, 100]})
        )

        outliers = profile["columns"]["measurement"]["outliers"]
        self.assertEqual(outliers["outlier_count"], 1)
        self.assertAlmostEqual(outliers["outlier_percentage"], 20.0)
        self.assertAlmostEqual(outliers["lower_bound"], 0.5)
        self.assertAlmostEqual(outliers["upper_bound"], 4.5)

    def test_constant_column_is_flagged(self) -> None:
        profile = self.generate_profile(pd.DataFrame({"fixed": ["same"] * 4}))

        type_info = self.type_info(profile, "fixed")
        self.assertTrue(type_info["is_constant"])
        self.assertEqual(type_info["cardinality"], "constant")
        self.assertTrue(profile["columns"]["fixed"]["is_constant"])

    def test_all_null_column_is_profiled_safely(self) -> None:
        profile = self.generate_profile(pd.DataFrame({"empty": [None, None, None]}))

        type_info = self.type_info(profile, "empty")
        missing = profile["columns"]["empty"]["missing"]
        self.assertEqual(type_info["detected_type"], "unknown")
        self.assertEqual(missing["missing_count"], 3)
        self.assertEqual(missing["non_missing_count"], 0)
        self.assertEqual(profile["columns"]["empty"]["numeric_statistics"], None)

    def test_perfect_numeric_correlation_is_returned_once(self) -> None:
        profile = self.generate_profile(
            pd.DataFrame({"feature_a": [1, 2, 3, 4], "feature_b": [2, 4, 6, 8]})
        )

        pairs = profile["correlations"]["pairs"]
        matching_pairs = [
            pair
            for pair in pairs
            if {pair["feature_1"], pair["feature_2"]} == {"feature_a", "feature_b"}
        ]
        self.assertEqual(len(matching_pairs), 1)
        self.assertAlmostEqual(matching_pairs[0]["correlation"], 1.0)

    def test_generated_profile_is_strictly_json_serializable(self) -> None:
        profile = self.generate_profile(
            pd.DataFrame(
                {
                    "number": [1.0, float("inf"), None],
                    "timestamp": [pd.Timestamp("2025-01-01"), pd.NaT, pd.Timestamp("2025-01-03")],
                    "category": ["a", None, "b"],
                }
            )
        )

        serialized = json.dumps(profile, allow_nan=False)
        self.assertIsInstance(serialized, str)


if __name__ == "__main__":
    unittest.main()

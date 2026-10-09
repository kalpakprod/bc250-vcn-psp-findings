"""Host-only tests for scripts/measure_bc250_perf.py. No hardware access.

The harness is only exercised in its decision-rule and refusal paths here; real
measurement runs are recorded under evidence/, not in the test suite.
"""

import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "measure_bc250_perf",
    Path(__file__).resolve().parents[1] / "scripts/measure_bc250_perf.py",
)
perf = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(perf)


def snapshot(
    label,
    latency,
    bw,
    alu,
    repeats,
    cpu=3,
    kernel="6.12.0-test",
    method="compiled-c-helper",
):
    trials = []
    for i in range(repeats):
        trials.append(
            {
                "index": i,
                "metrics": {
                    "latency_ns@67108864": latency + i * 0.1,
                    "bandwidth_gbs@67108864": bw + i * 0.01,
                    "alu_ns_per_op": alu + i * 0.001,
                },
            }
        )
    return {
        "schema": perf.SCHEMA,
        "label": label,
        "host_is_bc250": True,
        "host": {"kernel": kernel},
        "method": {"kind": method, "helper_sha256": "deadbeef"},
        "parameters": {
            "sizes": [67108864],
            "accesses": 3000000,
            "bw_bytes": 67108864,
            "bw_repeats": 8,
            "alu_iters": 200000000,
            "repeats": repeats,
            "cpu": cpu,
        },
        "trials": trials,
    }


class DecisionRuleTests(unittest.TestCase):
    def test_latency_drop_of_five_percent_is_measurable(self):
        base = [100.0, 100.5, 99.5, 101.0, 100.2]
        mod = [94.0, 94.4, 93.6, 94.8, 94.2]
        out = perf.classify(base, mod)
        self.assertEqual(out["verdict"], "MEASURABLE_IMPROVEMENT")
        self.assertTrue(out["iqr_disjoint"])
        self.assertLess(out["delta_pct"], -5.0)

    def test_latency_drop_inside_noise_band_is_not_measurable(self):
        base = [100.0, 100.5, 99.5, 101.0, 100.2]
        mod = [99.0, 99.4, 98.6, 99.8, 99.2]
        out = perf.classify(base, mod)
        self.assertEqual(out["verdict"], "NO_MEASURABLE_EFFECT")
        self.assertGreater(out["delta_pct"], -2.0)

    def test_small_but_consistent_drop_is_inconclusive(self):
        base = [100.0, 100.5, 99.5, 101.0, 100.2]
        mod = [96.5, 96.9, 96.2, 97.1, 96.7]
        out = perf.classify(base, mod)
        self.assertEqual(out["verdict"], "INCONCLUSIVE")


class CompareDocumentTests(unittest.TestCase):
    def test_identical_snapshots_are_not_an_improvement(self):
        a = snapshot("A", 97.7, 7.1, 0.44, 5)
        b = snapshot("B", 97.9, 7.2, 0.441, 5)
        out = perf.compare_documents(a, b)
        self.assertNotEqual(out["overall_verdict"], "MEASURABLE_IMPROVEMENT")
        self.assertTrue(out["run_pair_valid"])
        self.assertTrue(all(out["equivalence_checks"].values()))

    def test_improved_snapshot_is_measurable(self):
        a = snapshot("A", 100.0, 20.0, 0.44, 5)
        b = snapshot("B", 90.0, 22.0, 0.441, 5)
        out = perf.compare_documents(a, b)
        self.assertEqual(out["overall_verdict"], "MEASURABLE_IMPROVEMENT")
        self.assertTrue(out["equivalence_checks"]["same_cpu_affinity"])
        self.assertEqual(out["primary_latency_metric"], "latency_ns@67108864")

    def test_alu_drift_invalidates_the_run_pair(self):
        a = snapshot("A", 100.0, 20.0, 0.44, 5)
        b = snapshot("B", 90.0, 22.0, 0.55, 5)
        out = perf.compare_documents(a, mod=b)
        self.assertFalse(out["run_pair_valid"])
        self.assertEqual(out["overall_verdict"], "INVALID_RUN_PAIR")
        self.assertFalse(out["equivalence_checks"]["alu_drift_within_3pct"])

    def test_different_cpu_or_short_sample_set_is_flagged(self):
        a = snapshot("A", 100.0, 20.0, 0.44, 5, cpu=3)
        b = snapshot("B", 90.0, 22.0, 0.44, 2, cpu=4)
        out = perf.compare_documents(a, b)
        self.assertFalse(out["run_pair_valid"])
        self.assertFalse(out["equivalence_checks"]["same_cpu_affinity"])
        self.assertFalse(out["equivalence_checks"]["min_trials_each_3"])

    def test_cache_domain_regression_blocks_an_improvement_claim(self):
        a, b = snapshot("A", 108.0, 12.0, 0.44, 5), snapshot("B", 95.0, 14.0, 0.441, 5)
        for doc, values in (
            (a, (6.0, 6.1, 6.2, 6.3, 6.4)),
            (b, (7.4, 7.5, 7.6, 7.7, 7.8)),
        ):
            for trial, value in zip(doc["trials"], values):
                trial["metrics"]["latency_ns@1048576"] = value
        out = perf.compare_documents(a, b)
        self.assertTrue(out["run_pair_valid"])
        self.assertFalse(out["coherence_ok"])
        self.assertEqual(out["cache_domain_regressions"], ["latency_ns@1048576"])
        self.assertEqual(out["overall_verdict"], "INCOHERENT_RESULT")

    def test_coherent_improvement_is_accepted(self):
        a, b = snapshot("A", 108.0, 12.0, 0.44, 5), snapshot("B", 95.0, 13.5, 0.441, 5)
        for doc, values in (
            (a, (6.0, 6.1, 6.2, 6.3, 6.4)),
            (b, (6.0, 6.0, 6.1, 6.1, 6.2)),
        ):
            for trial, value in zip(doc["trials"], values):
                trial["metrics"]["latency_ns@1048576"] = value
        out = perf.compare_documents(a, b)
        self.assertTrue(out["coherence_ok"])
        self.assertEqual(out["overall_verdict"], "MEASURABLE_IMPROVEMENT")

    def test_proxy_method_never_reports_a_latency_verdict(self):
        a = snapshot("A", 100.0, 20.0, 0.44, 5, method="python-fallback")
        b = snapshot("B", 80.0, 25.0, 0.44, 5, method="python-fallback")
        for doc in (a, b):
            for trial in doc["trials"]:
                trial["metrics"]["latency_proxy_ns@4194304"] = trial["metrics"].pop(
                    "latency_ns@67108864"
                )
        out = perf.compare_documents(a, b)
        self.assertEqual(out["overall_verdict"], "PROXY_METHOD_LATENCY_UNUSED")
        self.assertIsNone(out["primary_latency_metric"])

    def test_summary_reports_quartiles_for_five_trials(self):
        summary = perf.summarize(
            [t["metrics"] for t in snapshot("A", 100.0, 20.0, 0.44, 5)["trials"]]
        )
        entry = summary["latency_ns@67108864"]
        self.assertEqual(entry["n"], 5)
        self.assertLessEqual(entry["q1"], entry["median"])
        self.assertLessEqual(entry["median"], entry["q3"])


class HostGateTests(unittest.TestCase):
    def test_non_bc250_host_refuses_without_override(self):
        meta = {"host_is_bc250": False, "drm_pci_ids": [["0x1002", "0x1900"]]}
        with patch.object(perf, "host_metadata", return_value=meta):
            code = perf.main(["run", "--quick", "--label", "REFUSAL"])
        self.assertEqual(code, 2)

    def test_python_fallback_is_labelled_as_a_proxy(self):
        metrics = perf.python_fallback_trial((1 << 16,), 4000, 1 << 20, 1)
        self.assertTrue(any(k.startswith("latency_proxy_ns@") for k in metrics))
        self.assertFalse(any(k.startswith("latency_ns@") for k in metrics))
        self.assertTrue(all(v == v for v in metrics.values()))

    def test_compare_json_is_serialisable(self):
        a = snapshot("A", 100.0, 20.0, 0.44, 5)
        b = snapshot("B", 90.0, 22.0, 0.441, 5)
        text = json.dumps(perf.compare_documents(a, b))
        self.assertNotIn("NaN", text)
        self.assertIn("MEASURABLE_IMPROVEMENT", text)


if __name__ == "__main__":
    unittest.main()

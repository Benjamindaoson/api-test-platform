from aqe.benchmark import run_fixture_benchmark


def test_fixture_benchmark_detects_every_declared_fault_profile():
    report = run_fixture_benchmark()

    assert report.corpus == "built-in-fixture"
    assert report.boundary == (
        "This benchmark replays deterministic fixture faults only; it does not measure real-production efficacy or human comparison.",
    )
    assert report.total_scenarios == 5
    assert report.detected_scenarios == 5
    assert report.missed_scenarios == 0
    assert report.detection_rate == 1.0
    assert all(scenario.detected for scenario in report.scenarios)


def test_fixture_benchmark_records_exact_rule_for_each_profile():
    report = run_fixture_benchmark()

    assert {
        scenario.profile: scenario.observed_rule_ids
        for scenario in report.scenarios
    } == {
        "wrong-retrieval": ("citation-integrity",),
        "ungrounded-answer": ("answer-correctness",),
        "fabricated-citation": ("citation-integrity",),
        "unsafe-refusal": ("refusal",),
        "prompt-injection-leak": ("protected-marker",),
    }

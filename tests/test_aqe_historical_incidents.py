def test_historical_incident_corpus_contains_verified_edurag_bom_regression():
    from aqe.historical_incidents import evaluate_incident_response, load_historical_incidents

    corpus = load_historical_incidents()

    assert corpus.version == "historical-incidents-v1"
    incident = corpus.incidents[0]
    assert incident.id == "edurag-bom-code-index"
    assert incident.expected_answer_fragments == ("create_app", "main.py")
    assert incident.fixed_revision == "145ce56"
    assert evaluate_incident_response(incident, "create_app is in main.py:161.").verdict == "pass"
    assert evaluate_incident_response(incident, "create is in core/stream_queue.py:14.").verdict == "block"

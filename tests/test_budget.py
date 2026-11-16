import pytest

from rave.budget import RunBudget, RunBudgetExceeded


def budget():
    return RunBudget(
        max_tokens=1000, max_searches=2, max_model_calls=2, max_seconds=30,
        max_cost_usd=0.10, search_input_reserve_tokens=100,
        search_input_rate=1.25, search_output_rate=10.0,
    )


def test_budget_reserves_before_network_and_blocks_token_overrun():
    b = budget()
    with pytest.raises(RunBudgetExceeded, match="token_budget_reservation_exceeded"):
        b.reserve("gpt-4.1-mini", "x" * 900, "", 200, False)
    assert b.calls == 0


def test_budget_counts_search_retries_and_global_model_calls():
    b = budget()
    b.reserve("gpt-5-search-api", "sys", "query", 10, True)
    b.reserve("gpt-4.1-mini", "sys", "analysis", 10, False)
    with pytest.raises(RunBudgetExceeded, match="model_call_budget_exceeded"):
        b.reserve("gpt-4.1-mini", "sys", "retry", 10, False)
    assert b.calls == 2
    assert b.searches == 1


def test_budget_reconciles_actual_usage():
    b = budget()
    reservation = b.reserve("gpt-4.1-mini", "s", "u", 20, False)
    b.record({"prompt_tokens": 5, "completion_tokens": 10}, reservation, "gpt-4.1-mini", False)
    snapshot = b.snapshot()
    assert snapshot["used"]["tokens"] == 15
    assert snapshot["reserved"]["tokens"] == 0
    assert snapshot["used"]["estimated_cost_usd"] > 0


def test_budget_blocks_cost_overrun_before_network():
    b = budget()
    b.max_cost_usd = 0.000001
    with pytest.raises(RunBudgetExceeded, match="cost_budget_reservation_exceeded"):
        b.reserve("gpt-4.1-mini", "prompt", "data", 100, False)
    assert b.calls == 0


def test_budget_requires_explicit_search_model_prices(monkeypatch):
    monkeypatch.delenv("RAVE_SEARCH_INPUT_USD_PER_1M", raising=False)
    monkeypatch.delenv("RAVE_SEARCH_OUTPUT_USD_PER_1M", raising=False)
    with pytest.raises(ValueError, match="RAVE_SEARCH_INPUT_USD_PER_1M"):
        RunBudget.from_env()


def test_search_fee_matches_ten_usd_per_thousand_calls():
    b = budget()
    reservation = b.reserve("gpt-5-search-api", "system", "query", 10, True)
    b.record({"prompt_tokens": 10, "completion_tokens": 5}, reservation,
             "gpt-5-search-api", True)
    expected = (10 * 1.25 + 5 * 10.0) / 1_000_000 + 0.01
    assert b.cost_usd == pytest.approx(expected)


def test_definitive_auth_rejection_can_release_reservation():
    b = budget()
    reservation = b.reserve("gpt-4.1-mini", "system", "query", 10, False)
    assert b.reserved_tokens > 0 and b.reserved_cost_usd > 0
    b.release_reservation(reservation)
    assert b.reserved_tokens == 0
    assert b.reserved_cost_usd == 0
    assert b.calls == 1

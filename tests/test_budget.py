import pytest

from rave.budget import RunBudget, RunBudgetExceeded


def make_budget(**overrides):
    values = {
        "max_tokens": 1000,
        "max_searches": 2,
        "max_model_calls": 2,
        "max_seconds": 30,
        "max_cost_usd": 0.50,
        "search_input_reserve_tokens": 100,
        "search_input_rate": 1.25,
        "search_output_rate": 10.0,
    }
    values.update(overrides)
    return RunBudget(**values)


def test_reservation_precedes_network_and_usage_reconciles():
    budget = make_budget()
    reservation = budget.reserve("gpt-4.1-mini", "system", "question", 100, False)
    assert budget.snapshot()["reserved"]["tokens"] > 0
    budget.record({"prompt_tokens": 10, "completion_tokens": 20}, reservation, "gpt-4.1-mini", False)
    snapshot = budget.snapshot()
    assert snapshot["used"]["tokens"] == 30
    assert snapshot["reserved"]["tokens"] == 0
    assert snapshot["used"]["model_calls"] == 1


def test_budget_blocks_token_overrun_before_network():
    budget = make_budget(max_tokens=100)
    with pytest.raises(RunBudgetExceeded, match="run_token_budget_reservation_exceeded"):
        budget.reserve("gpt-4.1-mini", "x" * 100, "question", 50, False)
    assert budget.snapshot()["used"]["model_calls"] == 0


def test_search_rates_must_be_explicit(monkeypatch):
    monkeypatch.delenv("RAVE_SEARCH_INPUT_USD_PER_1M", raising=False)
    monkeypatch.delenv("RAVE_SEARCH_OUTPUT_USD_PER_1M", raising=False)
    with pytest.raises(ValueError, match="RAVE_SEARCH_INPUT_USD_PER_1M"):
        RunBudget.from_env()


def test_local_cost_ceiling_cannot_exceed_policy(monkeypatch):
    monkeypatch.setenv("RAVE_SEARCH_INPUT_USD_PER_1M", "1.25")
    monkeypatch.setenv("RAVE_SEARCH_OUTPUT_USD_PER_1M", "10")
    monkeypatch.setenv("RAVE_MAX_RUN_COST_USD", "0.51")
    with pytest.raises(ValueError, match="cannot exceed USD 0.50"):
        RunBudget.from_env()


def test_unknown_model_is_blocked():
    budget = make_budget()
    with pytest.raises(RunBudgetExceeded, match="no_price_configured_for_model"):
        budget.reserve("unknown-model", "system", "question", 100, False)


def test_input_reservation_estimates_tokens_instead_of_counting_utf8_bytes():
    budget = make_budget(max_tokens=1000)
    system = "a" * 300
    user = "b" * 300
    reservation = budget.reserve("gpt-4.1-mini", system, user, 100, False)
    # 600 UTF-8 bytes / 3, plus the 100-token output reservation.
    assert reservation[0] == 300
    assert budget.snapshot()["reserved"]["tokens"] == 300


def test_multibyte_prompt_reservation_uses_utf8_byte_based_conservative_estimate():
    budget = make_budget(max_tokens=1000)
    system = "ação" * 30
    user = "pergunta" * 30
    prompt_bytes = len((system + user).encode("utf-8"))
    reservation = budget.reserve("gpt-4.1-mini", system, user, 100, False)
    assert reservation[0] == (prompt_bytes + 2) // 3 + 100

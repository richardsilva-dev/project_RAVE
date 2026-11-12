import pytest

from solo_baseline.budget import Budget, BudgetExceeded


def make_budget(**overrides):
    values = dict(max_search_calls=2, max_model_calls=4, max_total_tokens=100,
                  max_runtime_seconds=60, max_output_tokens_per_call=20)
    values.update(overrides)
    return Budget(**values)


def test_budget_counts_search_and_model_calls():
    budget = make_budget()
    assert budget.before_call("search") == 20
    budget.record(kind="search", model="search-model",
                  usage={"prompt_tokens": 10, "completion_tokens": 5}, duration_seconds=1)
    assert budget.search_calls == 1
    assert budget.total_tokens == 15


def test_budget_stops_after_search_limit():
    budget = make_budget(max_search_calls=1)
    budget.before_call("search")
    with pytest.raises(BudgetExceeded, match="MAX_SEARCH_CALLS"):
        budget.before_call("search")


def test_budget_stops_after_model_call_limit():
    budget = make_budget(max_model_calls=1)
    budget.before_call("analysis")
    with pytest.raises(BudgetExceeded, match="MAX_MODEL_CALLS"):
        budget.before_call("analysis")

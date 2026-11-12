import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from rave.cli import load_shared_research_run, run_single
from rave.llm import LLMResponse


QUESTION = "Same question"
SCOPE = "Same scope"
RUN_ID = "rave-shared-input"


def write_source_run(output_dir, *, mode="shared_research", status="COMPLETED"):
    Path(output_dir, f"{RUN_ID}.json").write_text(json.dumps({
        "research_mode": mode,
        "execution_status": status,
        "metadata": {"question": QUESTION},
        "tasks": [{"scope": SCOPE}],
        "shared_web_research": {"content": "Exact shared research notes",
            "citations": [{"title": "Source", "url": "https://source.example/report"}],
            "usage": {"prompt_tokens": 31, "completion_tokens": 12}},
    }), encoding="utf-8")


class SingleClient:
    settings = SimpleNamespace(model="reasoning-model", web_search_enabled=True)

    def __init__(self, timeout=False, search_timeout=False):
        self.calls = []
        self.timeout = timeout
        self.search_timeout = search_timeout

    def complete(self, system, user, *, web_search=False):
        prompt = json.loads(user)
        self.calls.append((system, prompt, web_search))
        if web_search and self.search_timeout:
            raise TimeoutError("search timeout")
        assert not web_search
        assert prompt["shared_web_research"]["research_notes"] == "Exact shared research notes"
        if self.timeout:
            raise TimeoutError("test timeout")
        return LLMResponse(json.dumps({"summary": "Solo result", "findings": [{
            "category": "fact", "title": "Finding", "claim": "Claim",
            "explanation": "Explanation", "evidence": [{"source_title": "Source",
                "source_url": "https://source.example/report", "supporting_excerpt_or_location": "Excerpt"}],
            "evidence_status": "INSUFFICIENT", "status_rationale": "Test only",
            "limitations": [], "open_questions": []}], "limitations": [], "open_questions": []}),
            {"prompt_tokens": 5, "completion_tokens": 4})


def test_single_can_reuse_exact_research_from_completed_shared_hive_run(tmp_path):
    write_source_run(tmp_path)
    research = load_shared_research_run(str(tmp_path), RUN_ID, QUESTION, SCOPE)
    assert research == LLMResponse("Exact shared research notes",
        {"prompt_tokens": 31, "completion_tokens": 12},
        [{"title": "Source", "url": "https://source.example/report"}])

    client = SingleClient()
    output = asyncio.run(run_single(client, str(tmp_path), QUESTION, SCOPE, research, RUN_ID))
    saved = json.loads(Path(output["result_path"]).read_text(encoding="utf-8"))

    assert output["execution_status"] == "COMPLETED"
    assert output["shared_research_source_run_id"] == RUN_ID
    assert saved["shared_research_reused"] is True
    assert saved["shared_research_source_run_id"] == RUN_ID
    assert len(client.calls) == 1
    assert client.calls[0][1]["shared_web_research"]["sources"][0]["url"] == "https://source.example/report"
    assert saved["agent_result"]["findings"][0]["evidence"][0]["citation_provenance"] == "provider_returned"


@pytest.mark.parametrize("question,scope", [("Different question", SCOPE), (QUESTION, "Different scope")])
def test_reused_research_requires_same_question_and_scope(tmp_path, question, scope):
    write_source_run(tmp_path)
    with pytest.raises(ValueError):
        load_shared_research_run(str(tmp_path), RUN_ID, question, scope)


def test_reused_research_requires_completed_shared_run(tmp_path):
    write_source_run(tmp_path, mode="independent_research")
    with pytest.raises(ValueError, match="completed shared_research"):
        load_shared_research_run(str(tmp_path), RUN_ID, QUESTION, SCOPE)


def test_single_timeout_is_persisted_as_partial_without_traceback(tmp_path):
    write_source_run(tmp_path)
    research = load_shared_research_run(str(tmp_path), RUN_ID, QUESTION, SCOPE)
    output = asyncio.run(run_single(SingleClient(timeout=True), str(tmp_path), QUESTION, SCOPE,
        research, RUN_ID))
    saved = json.loads(Path(output["result_path"]).read_text(encoding="utf-8"))

    assert output["execution_status"] == "PARTIAL"
    assert output["failure_type"] == "TimeoutError"
    assert saved["metadata"]["status"] == "PARTIAL"
    assert saved["agent_result"] is None
    assert saved["failure"] == {"stage": "analysis", "error_type": "TimeoutError"}


def test_single_search_timeout_is_persisted_as_invalid(tmp_path):
    output = asyncio.run(run_single(SingleClient(search_timeout=True), str(tmp_path), QUESTION, SCOPE))
    saved = json.loads(Path(output["result_path"]).read_text(encoding="utf-8"))

    assert output["execution_status"] == "INVALID"
    assert output["failure_type"] == "TimeoutError"
    assert saved["metadata"]["status"] == "INVALID"
    assert saved["failure"] == {"stage": "research", "error_type": "TimeoutError"}

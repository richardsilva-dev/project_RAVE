from rave.contracts import AgentTask, Finding, new_id


def test_finding_keeps_origin_and_task_ids():
    finding = Finding(
        new_id("finding"), "run-1", "agent-01", "task-1", "fact", "Title", "Claim"
    )
    assert finding.run_id == "run-1"
    assert finding.agent_id == "agent-01"
    assert finding.task_id == "task-1"


def test_task_contract_contains_global_and_specialized_questions():
    task = AgentTask(
        "task-1", "run-1", "Global?", "Specialized?", "Role", "Output", "Scope"
    )
    assert task.global_question != task.specialized_question

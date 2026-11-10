from rave.core.planner import create_tasks

def test_planner_creates_three_specialized_tasks():
    tasks = create_tasks("run-1", "How do batteries work?", "battery science")
    assert len(tasks) == 3
    assert len({task.specialized_question for task in tasks}) == 3
    assert all(task.run_id == "run-1" for task in tasks)

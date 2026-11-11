import asyncio
import json
from types import SimpleNamespace
from rave.agents import FundamentalsAgent, MechanismAgent, PerspectiveAgent
from rave.communication import MessageBus
from rave.contracts import AgentTask
from rave.core.integration import integrate
from rave.core.planner import create_tasks
from rave.llm import LLMResponse


class FakeClient:
    settings = SimpleNamespace(web_search_enabled=False)

    def complete(self, system, user, *, web_search=False):
        role = system.split("RAVE Agent ", 1)[-1].split(":", 1)[0]
        data = {"summary": f"summary-{role}", "findings": [{"category": "fact",
            "title": f"title-{role}", "claim": f"claim-{role}", "explanation": "details",
            "evidence": [], "limitations": [], "open_questions": []}],
            "limitations": [], "open_questions": []}
        return LLMResponse(json.dumps(data), {"prompt_tokens": 3, "completion_tokens": 2})

def test_direct_message_delivery_and_audit():
    async def scenario():
        bus = MessageBus("run-1")
        message = await bus.send("agent-01", "agent-02", "FINDING_SHARE", "task-1", "A finding")
        assert await bus.receive_all("agent-02") == [message]
        assert bus.audit_log == [message]
        assert await bus.receive_all("agent-02") == []
    asyncio.run(scenario())


def test_failed_agent_releases_publication_barrier():
    class SometimesFailingClient(FakeClient):
        def complete(self, system, user, *, web_search=False):
            if system.startswith("You are RAVE Agent 1:"):
                raise RuntimeError("simulated provider failure")
            return super().complete(system, user, web_search=web_search)

    async def scenario():
        bus = MessageBus("run-1")
        client = SometimesFailingClient()
        agents = [FundamentalsAgent("agent-01", "Fundamentals", "facts", client, bus),
            MechanismAgent("agent-02", "Mechanisms", "mechanisms", client, bus),
            PerspectiveAgent("agent-03", "Perspectives", "limits", client, bus)]
        tasks = create_tasks("run-1", "Question?", "Scope")
        outcomes = await asyncio.wait_for(asyncio.gather(
            *(agent.run(task) for agent, task in zip(agents, tasks)), return_exceptions=True), 2)
        assert isinstance(outcomes[0], RuntimeError)
        assert all(not isinstance(outcome, BaseException) for outcome in outcomes[1:])
    asyncio.run(scenario())


def test_agent_publication_barrier_and_cross_agent_integration():
    async def scenario():
        bus = MessageBus("run-1")
        client = FakeClient()
        agents = [FundamentalsAgent("agent-01", "Fundamentals", "facts", client, bus),
            MechanismAgent("agent-02", "Mechanisms", "mechanisms", client, bus),
            PerspectiveAgent("agent-03", "Perspectives", "limits", client, bus)]
        tasks = create_tasks("run-1", "Question?", "Scope")
        results = await asyncio.wait_for(asyncio.gather(*(a.run(t) for a, t in zip(agents, tasks))), 2)
        assert len(bus.audit_log) == 6
        assert all(len(result.messages_used) == 2 for result in results)
        integrated = integrate(results)
        assert integrated["agent_count"] == 3
        assert len(integrated["findings"]) == 3
    asyncio.run(scenario())

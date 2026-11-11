import asyncio
import time
from datetime import datetime, timezone
from ..agents import FundamentalsAgent, MechanismAgent, PerspectiveAgent
from ..communication import MessageBus
from ..contracts import RunMetadata, new_id
from ..llm import ChatCompletionsClient
from ..storage import save_run
from .integration import integrate
from .planner import create_tasks
from .synthesis import synthesize

class HiveCore:
    def __init__(self, client: ChatCompletionsClient, output_dir: str):
        self.client, self.output_dir = client, output_dir

    async def run(self, question: str, scope: str = "Investigar a pergunta sem expandir além do necessário.") -> dict:
        started_wall = datetime.now(timezone.utc).isoformat()
        started = time.perf_counter()
        run_id = new_id("rave")
        bus = MessageBus(run_id)
        tasks = create_tasks(run_id, question, scope)
        agents = [
            FundamentalsAgent("agent-01", "Fundamentos", "Fundamentos e evidências", self.client, bus),
            MechanismAgent("agent-02", "Mecanismos", "Mecanismos e relações", self.client, bus),
            PerspectiveAgent("agent-03", "Perspectivas", "Perspectivas e limites", self.client, bus)]
        results = await asyncio.gather(*(agent.run(task) for agent, task in zip(agents, tasks)))
        integrated = integrate(results)
        final_output, synthesis_usage = await synthesize(self.client, question, integrated)
        duration = time.perf_counter() - started
        metadata = RunMetadata(run_id, question, "RAVE", self.client.settings.model,
            started_wall, datetime.now(timezone.utc).isoformat(), duration,
            1 + len(results) + sum(1 for result in results if result.messages_used),
            sum(r.usage.get("prompt_tokens", 0) for r in results) + synthesis_usage.get("prompt_tokens", 0),
            sum(r.usage.get("completion_tokens", 0) for r in results) + synthesis_usage.get("completion_tokens", 0),
            len(bus.audit_log))
        payload = {"metadata": metadata, "tasks": tasks, "agent_results": results,
            "messages": bus.audit_log, "integration": integrated, "final_output": final_output}
        path = save_run(self.output_dir, run_id, payload)
        return {"run_id": run_id, "result_path": str(path), "metadata": metadata,
            "agent_results": results, "final_output": final_output}

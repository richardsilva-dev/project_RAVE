import asyncio
import logging
import time
import json
from datetime import datetime, timezone
from ..agents import FundamentalsAgent, MechanismAgent, PerspectiveAgent
from ..communication import MessageBus
from ..contracts import RunMetadata, new_id
from ..llm import ChatCompletionsClient, capture_llm_calls, current_llm_calls
from ..storage import save_run
from .integration import integrate
from .planner import create_tasks
from .synthesis import synthesize
from ..research import shared_research as perform_shared_research

logger = logging.getLogger(__name__)

class HiveCore:
    def __init__(self, client: ChatCompletionsClient, output_dir: str):
        self.client, self.output_dir = client, output_dir

    async def run(self, question: str, scope: str = "Investigar a pergunta sem expandir além do necessário.") -> dict:
        with capture_llm_calls():
            return await self._run(question, scope)

    async def _run(self, question: str, scope: str) -> dict:
        started_wall = datetime.now(timezone.utc).isoformat()
        started = time.perf_counter()
        phase_timings = {}
        run_id = new_id("rave")
        bus = MessageBus(run_id)
        tasks = create_tasks(run_id, question, scope)
        agents = [
            FundamentalsAgent("agent-01", "Fundamentos", "Fundamentos e evidências", self.client, bus),
            MechanismAgent("agent-02", "Mecanismos", "Mecanismos e relações", self.client, bus),
            PerspectiveAgent("agent-03", "Perspectivas", "Perspectivas e limites", self.client, bus)]
        logger.info("Run %s started with %d agents", run_id, len(agents))
        shared_research = None
        shared_research_error = ""
        if self.client.settings.web_search_enabled:
            logger.info("Run %s: performing shared web research", run_id)
            search_started = time.perf_counter()
            try:
                shared_research = await asyncio.to_thread(perform_shared_research, self.client, question, scope)
            except Exception as exc:
                shared_research_error = type(exc).__name__
                logger.warning("Run %s: shared search failed (%s); agents will use their regular research path",
                    run_id, shared_research_error)
            phase_timings["shared_web_research"] = time.perf_counter() - search_started
            logger.info("Run %s: shared research finished in %.1fs with %d sources", run_id,
                phase_timings["shared_web_research"], len(shared_research.citations or []) if shared_research else 0)
        investigation_started = time.perf_counter()
        outcomes = await asyncio.gather(*(agent.run(task, shared_research)
            for agent, task in zip(agents, tasks)), return_exceptions=True)
        results = [outcome for outcome in outcomes if not isinstance(outcome, BaseException)]
        failed_agents = [{"agent_id": agent.agent_id, "error_type": type(outcome).__name__}
            for agent, outcome in zip(agents, outcomes) if isinstance(outcome, BaseException)]
        execution_status = "COMPLETED" if not failed_agents and not shared_research_error else (
            "PARTIAL" if results else "INVALID")
        phase_timings["agent_research_and_peer_integration"] = time.perf_counter() - investigation_started
        logger.info("Run %s: agents finished in %.1fs; integrating findings", run_id,
            phase_timings["agent_research_and_peer_integration"])
        integration_started = time.perf_counter()
        integrated = integrate(results)
        phase_timings["local_integration"] = time.perf_counter() - integration_started
        logger.info("Run %s: %d findings and %d sources integrated", run_id,
            len(integrated["findings"]), len(integrated["web_sources"]))
        synthesis_usage = {}
        synthesis_error = ""
        synthesis_status = "NOT_RUN"
        if results:
            synthesis_started = time.perf_counter()
            try:
                final_output, synthesis_usage = await synthesize(self.client, question, integrated)
                synthesis_status = "COMPLETED"
            except Exception as exc:
                synthesis_error = type(exc).__name__
                synthesis_status = "FAILED"
                execution_status = "PARTIAL"
                final_output = {"executive_answer": "", "integrated_analysis": "", "collective_integration": "",
                    "evidence_and_sources": [], "web_sources": integrated.get("web_sources", []),
                    "gaps_and_limitations": [
                        "A síntese final falhou ou retornou saída inválida. Os resultados dos agentes foram preservados, mas não existe resposta coletiva validada."],
                    "conclusions": ""}
            phase_timings["final_synthesis"] = time.perf_counter() - synthesis_started
            if failed_agents:
                final_output.setdefault("gaps_and_limitations", []).append(
                    "Execução parcial: um ou mais agentes falharam. Esta saída não representa uma execução coletiva completa.")
            if shared_research_error:
                final_output.setdefault("gaps_and_limitations", []).append(
                    "A busca compartilhada falhou; os agentes usaram o fluxo de pesquisa individual.")
        else:
            final_output = {"executive_answer": "", "integrated_analysis": "", "collective_integration": "",
                "evidence_and_sources": [], "gaps_and_limitations": [
                    "Execução inválida: nenhum agente concluiu a investigação; síntese não realizada."], "conclusions": ""}
        if "final_synthesis" in phase_timings:
            logger.info("Run %s: final synthesis finished in %.1fs", run_id, phase_timings["final_synthesis"])
        duration = time.perf_counter() - started
        calls = list(current_llm_calls())
        metadata = RunMetadata(run_id, question, "RAVE", self.client.settings.model,
            started_wall, datetime.now(timezone.utc).isoformat(), duration,
            len(calls), sum(c.get("prompt_tokens", 0) for c in calls),
            sum(c.get("completion_tokens", 0) for c in calls), len(bus.audit_log),
            execution_status, sum(c.get("request_attempts", 1) for c in calls), calls)
        payload = {"metadata": metadata, "tasks": tasks,
            "shared_web_research": shared_research,
            "agent_results": results,
            "messages": bus.audit_log, "integration": integrated, "final_output": final_output,
            "phase_timings": phase_timings, "execution_status": execution_status,
            "failed_agents": failed_agents, "shared_research_error": shared_research_error,
            "synthesis_error": synthesis_error, "synthesis_status": synthesis_status}
        path = save_run(self.output_dir, run_id, payload)
        logger.info("Run %s saved to %s in %.1fs", run_id, path, duration)
        return {"run_id": run_id, "result_path": str(path), "metadata": metadata,
            "agent_results": results, "final_output": final_output, "phase_timings": phase_timings,
            "execution_status": execution_status, "failed_agents": failed_agents,
            "shared_research_error": shared_research_error, "synthesis_error": synthesis_error,
            "synthesis_status": synthesis_status}

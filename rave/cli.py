import argparse
import asyncio
import json
import logging
import re
import sys
from pathlib import Path
from .config import Settings
from .llm import ChatCompletionsClient, LLMResponse, capture_llm_calls, current_llm_calls, llm_agent_context
from .core.hive_core import HiveCore
from .agents.single import SingleAgent
from .communication import MessageBus
from .contracts import AgentTask, new_id
from .storage import save_run
from .research import shared_research as perform_shared_research
from .contracts import RunMetadata
from datetime import datetime, timezone
import time

logger = logging.getLogger(__name__)

def load_shared_research_run(output_dir: str, source_run_id: str, question: str, scope: str) -> LLMResponse:
    if not re.fullmatch(r"rave-[A-Za-z0-9_-]{1,59}", source_run_id):
        raise ValueError("--research-run-id must be a valid Hive run id")
    source_path = Path(output_dir) / f"{source_run_id}.json"
    if not source_path.is_file():
        raise ValueError(f"Shared research run not found: {source_run_id}")
    try:
        payload = json.loads(source_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read shared research run: {source_run_id}") from exc
    if payload.get("research_mode") != "shared_research" or payload.get("execution_status") != "COMPLETED":
        raise ValueError("--research-run-id must refer to a completed shared_research Hive run")
    if payload.get("metadata", {}).get("question") != question:
        raise ValueError("Question must match the source Hive run when reusing its research")
    tasks = payload.get("tasks", [])
    source_scope = tasks[0].get("scope") if tasks and isinstance(tasks[0], dict) else None
    if source_scope != scope:
        raise ValueError("Scope must match the source Hive run when reusing its research")
    research = payload.get("shared_web_research")
    if not isinstance(research, dict) or not isinstance(research.get("content"), str):
        raise ValueError("Source Hive run does not contain reusable shared research")
    citations = research.get("citations") or []
    if not isinstance(citations, list) or any(not isinstance(item, dict) for item in citations):
        raise ValueError("Source Hive run contains invalid citation metadata")
    usage = research.get("usage") or {}
    return LLMResponse(research["content"], usage, citations)


async def run_single(client, output_dir, question, scope, shared_research=None,
        research_source_run_id: str | None = None):
    run_id = new_id("single")
    task = AgentTask(new_id("task"), run_id, question, question, "Agente único", "Resposta integral", scope)
    agent = SingleAgent("single-agent", "Agente individual", "Baseline", client, MessageBus(run_id))
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    research = shared_research
    result = None
    failure_type = ""
    failure_stage = "research"
    with capture_llm_calls() as captured_calls:
        with llm_agent_context(agent.agent_id):
            try:
                if research is None and client.settings.web_search_enabled:
                    research = await asyncio.to_thread(perform_shared_research, client, question, scope)
                failure_stage = "analysis"
                result = await agent.run(task, research)
            except Exception as exc:
                failure_type = type(exc).__name__
                logger.warning("Single-agent run %s failed during %s (%s)", run_id, failure_stage, failure_type)
        calls = list(captured_calls)
    execution_status = "COMPLETED" if result is not None else ("PARTIAL" if research else "INVALID")
    metadata = RunMetadata(run_id, question, "SINGLE_BASELINE", client.settings.model,
        started_at, datetime.now(timezone.utc).isoformat(), time.perf_counter() - started,
        len(calls), sum(c.get("prompt_tokens", 0) for c in calls),
        sum(c.get("completion_tokens", 0) for c in calls), 0, execution_status,
        sum(c.get("request_attempts", 1) for c in calls), calls)
    path = save_run(output_dir, run_id, {"configuration": "single", "question": question,
        "metadata": metadata, "shared_web_research": research, "agent_result": result,
        "execution_status": execution_status, "failure": {"stage": failure_stage,
            "error_type": failure_type} if failure_type else None,
        "shared_research_source_run_id": research_source_run_id,
        "shared_research_reused": research_source_run_id is not None})
    return {"run_id": run_id, "result_path": str(path), "metadata": metadata,
        "agent_result": result, "execution_status": execution_status,
        "failure_type": failure_type, "shared_research_source_run_id": research_source_run_id}

def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(prog="rave", description="RAVE Hive Core 0.1")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("hive", "single"):
        command = sub.add_parser(name)
        command.add_argument("question")
        command.add_argument("--scope", default="Investigar a pergunta sem expandir além do necessário.")
        if name == "single":
            command.add_argument("--research-run-id",
                help="Reuse the exact shared research from a completed Hive run with the same question and scope")
    args = parser.parse_args()
    try:
        settings = Settings.from_env()
        client = ChatCompletionsClient(settings)
        if args.command == "hive":
            output = asyncio.run(HiveCore(client, settings.output_dir).run(args.question, args.scope))
        else:
            research = load_shared_research_run(settings.output_dir, args.research_run_id,
                args.question, args.scope) if args.research_run_id else None
            output = asyncio.run(run_single(client, settings.output_dir, args.question, args.scope,
                research, args.research_run_id))
    except (RuntimeError, ValueError, TimeoutError) as exc:
        parser.exit(1, f"{parser.prog}: error: {exc}\n")
    print(json.dumps(output, ensure_ascii=False, indent=2, default=lambda value: value.__dict__))

if __name__ == "__main__":
    main()

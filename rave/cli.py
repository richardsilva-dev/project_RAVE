import argparse
import asyncio
import json
import logging
import sys
from .config import Settings
from .llm import ChatCompletionsClient, capture_llm_calls, current_llm_calls
from .core.hive_core import HiveCore
from .agents.single import SingleAgent
from .communication import MessageBus
from .contracts import AgentTask, new_id
from .storage import save_run
from .research import shared_research as perform_shared_research
from .contracts import RunMetadata
from datetime import datetime, timezone
import time

async def run_single(client, output_dir, question, scope):
    run_id = new_id("single")
    task = AgentTask(new_id("task"), run_id, question, question, "Agente único", "Resposta integral", scope)
    agent = SingleAgent("single-agent", "Agente individual", "Baseline", client, MessageBus(run_id))
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    with capture_llm_calls():
        research = None
        if client.settings.web_search_enabled:
            research = await asyncio.to_thread(perform_shared_research, client, question, scope)
        result = await agent.run(task, research)
        calls = list(current_llm_calls())
    metadata = RunMetadata(run_id, question, "SINGLE_BASELINE", client.settings.model,
        started_at, datetime.now(timezone.utc).isoformat(), time.perf_counter() - started,
        len(calls), sum(c.get("prompt_tokens", 0) for c in calls),
        sum(c.get("completion_tokens", 0) for c in calls), 0, "COMPLETED",
        sum(c.get("request_attempts", 1) for c in calls), calls)
    path = save_run(output_dir, run_id, {"configuration": "single", "question": question,
        "metadata": metadata, "shared_web_research": research, "agent_result": result})
    return {"run_id": run_id, "result_path": str(path), "metadata": metadata, "agent_result": result}

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
    args = parser.parse_args()
    try:
        settings = Settings.from_env()
        client = ChatCompletionsClient(settings)
        if args.command == "hive":
            output = asyncio.run(HiveCore(client, settings.output_dir).run(args.question, args.scope))
        else:
            output = asyncio.run(run_single(client, settings.output_dir, args.question, args.scope))
    except (RuntimeError, ValueError) as exc:
        parser.exit(1, f"{parser.prog}: error: {exc}\n")
    print(json.dumps(output, ensure_ascii=False, indent=2, default=lambda value: value.__dict__))

if __name__ == "__main__":
    main()

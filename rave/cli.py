import argparse
import asyncio
import json
import logging
from .config import Settings
from .llm import ChatCompletionsClient
from .core.hive_core import HiveCore
from .agents.single import SingleAgent
from .communication import MessageBus
from .contracts import AgentTask, new_id
from .storage import save_run

async def run_single(client, output_dir, question, scope):
    run_id = new_id("single")
    task = AgentTask(new_id("task"), run_id, question, question, "Agente único", "Resposta integral", scope)
    agent = SingleAgent("single-agent", "Agente individual", "Baseline", client, MessageBus(run_id))
    result = await agent.run(task)
    path = save_run(output_dir, run_id, {"configuration": "single", "question": question, "agent_result": result})
    return {"run_id": run_id, "result_path": str(path), "agent_result": result}

def main() -> None:
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

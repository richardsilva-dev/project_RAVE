import json
import asyncio
from ..llm import ChatCompletionsClient

SYSTEM = """You are the RAVE Hive Core synthesis component. Integrate, do not concatenate. Connect factual foundations, mechanisms and complementary perspectives. Preserve provenance, distinguish single-agent contributions from cross-agent insights, avoid treating repetition as independent confirmation, retain disagreements and limitations. Never invent citations or facts. Return valid JSON with keys: executive_answer, integrated_analysis, collective_integration, evidence_and_sources, gaps_and_limitations, conclusions."""

async def synthesize(client: ChatCompletionsClient, question: str, integrated: dict) -> tuple[dict, dict[str, int]]:
    prompt = json.dumps({"question": question,
        "agent_contributions": integrated["local_contributions"],
        "findings": [{"finding_id": f.finding_id, "agent_id": f.agent_id, "category": f.category,
            "title": f.title, "claim": f.claim, "explanation": f.explanation,
            "evidence": [e.__dict__ for e in f.evidence], "limitations": f.limitations}
            for f in integrated["findings"]], "overlaps": integrated["overlaps"],
        "instruction": "Produce one structured final response and attribute claims to agent IDs where useful."}, ensure_ascii=False)
    response = await asyncio.to_thread(client.complete, SYSTEM, prompt)
    try:
        output = json.loads(response.content)
    except json.JSONDecodeError:
        output = {"executive_answer": response.content, "integrated_analysis": "",
            "collective_integration": "", "evidence_and_sources": [],
            "gaps_and_limitations": ["Synthesis response was not valid JSON."], "conclusions": ""}
    return output, response.usage

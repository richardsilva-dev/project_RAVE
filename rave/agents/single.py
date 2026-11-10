import json
from ..contracts import AgentResult, AgentTask
from ..llm import ChatCompletionsClient
from .base import BaseAgent

class SingleAgent(BaseAgent):
    def instructions(self) -> str:
        return """You are the single-agent baseline for the RAVE experiment. Investigate the complete question without specialist decomposition. Aim for accuracy, coverage, depth, coherent explanations, limitations and traceable evidence. Do not assume a multi-agent system is better. Never invent sources. Return only valid JSON with summary, findings, limitations and open_questions."""
    def peer_ids(self) -> list[str]:
        return []

    async def run(self, task: AgentTask) -> AgentResult:
        response = await __import__("asyncio").to_thread(self.client.complete, self.instructions(), json.dumps({
            "phase": "single_agent_baseline", "global_question": task.global_question,
            "scope": task.scope, "constraints": task.constraints}, ensure_ascii=False))
        data = self.parse_json(response.content)
        return AgentResult(self.agent_id, self.name, self.role, task.task_id, "COMPLETED",
            str(data.get("summary", "")), self.make_findings(data, task),
            list(data.get("limitations", [])), list(data.get("open_questions", [])),
            [], response.content, response.usage)

import asyncio
import json
from dataclasses import asdict
from abc import ABC, abstractmethod
from typing import Any
from ..communication import MessageBus
from ..contracts import AgentResult, AgentTask, Evidence, Finding, new_id
from ..llm import ChatCompletionsClient

class BaseAgent(ABC):
    def __init__(self, agent_id: str, name: str, role: str, client: ChatCompletionsClient, bus: MessageBus):
        self.agent_id, self.name, self.role = agent_id, name, role
        self.client, self.bus = client, bus

    @abstractmethod
    def instructions(self) -> str: ...

    @abstractmethod
    def peer_ids(self) -> list[str]: ...

    def parse_json(self, raw: str) -> dict[str, Any]:
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start, end = text.find("{"), text.rfind("}")
            if start >= 0 and end > start:
                return json.loads(text[start:end + 1])
            raise ValueError(f"{self.agent_id} returned invalid JSON")

    def make_findings(self, data: dict[str, Any], task: AgentTask) -> list[Finding]:
        findings = []
        raw_findings = data.get("findings", [])
        if not isinstance(raw_findings, list):
            raise ValueError(f"{self.agent_id} returned findings in an invalid format")
        for item in raw_findings:
            if not isinstance(item, dict):
                raise ValueError(f"{self.agent_id} returned a malformed finding")
            raw_evidence = item.get("evidence", [])
            if not isinstance(raw_evidence, list) or any(not isinstance(e, dict) for e in raw_evidence):
                raise ValueError(f"{self.agent_id} returned malformed evidence")
            evidence = [Evidence(str(e.get("source_title", "")), str(e.get("source_url", "")),
                str(e.get("supporting_excerpt_or_location", ""))) for e in raw_evidence]
            findings.append(Finding(new_id("finding"), task.run_id, self.agent_id, task.task_id,
                item.get("category", "other"), item.get("title", ""), item.get("claim", ""),
                item.get("explanation", ""), evidence, [], [], list(item.get("limitations", [])),
                list(item.get("open_questions", []))))
        return findings

    async def run(self, task: AgentTask) -> AgentResult:
        schema = {"summary": "string", "findings": [{"category": "fact|mechanism|limitation|relationship|other",
            "title": "string", "claim": "string", "explanation": "string",
            "evidence": [{"source_title": "string", "source_url": "string", "supporting_excerpt_or_location": "string"}],
            "limitations": ["string"], "open_questions": ["string"]}],
            "limitations": ["string"], "open_questions": ["string"]}
        prompt = json.dumps({"phase": "independent_investigation", "global_question": task.global_question,
            "specialized_question": task.specialized_question, "scope": task.scope,
            "expected_contribution": task.expected_contribution, "constraints": task.constraints,
            "required_json": schema}, ensure_ascii=False)
        try:
            initial = await asyncio.to_thread(self.client.complete, self.instructions(), prompt)
            data = self.parse_json(initial.content)
            if not isinstance(data, dict):
                raise ValueError(f"{self.agent_id} returned JSON that is not an object")
        except Exception:
            # Always release peers waiting at the publication barrier on failure.
            await self.bus.mark_published()
            raise
        findings = self.make_findings(data, task)
        for finding in findings:
            for peer in self.peer_ids():
                await self.bus.send(self.agent_id, peer, "FINDING_SHARE", task.task_id,
                    f"{finding.title}: {finding.claim}", finding.finding_id)
        await self.bus.mark_published()
        await self.bus.wait_for_all_publishers()
        incoming = await self.bus.receive_all(self.agent_id)
        usage = dict(initial.usage)
        raw = initial.content
        if incoming:
            refine_prompt = json.dumps({"phase": "cross_agent_integration", "global_question": task.global_question,
                "your_initial_summary": data.get("summary", ""),
                "your_initial_findings": [asdict(f) for f in findings],
                "peer_contributions": [{"sender": m.sender_agent_id, "content": m.content,
                    "finding_id": m.related_claim_or_finding_id} for m in incoming],
                "instruction": "Use relevant complementary findings without abandoning your specialty. Preserve attribution and disagreement. Return the same JSON schema."}, ensure_ascii=False)
            refinement = await asyncio.to_thread(self.client.complete, self.instructions(), refine_prompt)
            data = self.parse_json(refinement.content)
            findings = self.make_findings(data, task)
            for key in ("prompt_tokens", "completion_tokens"):
                usage[key] = usage.get(key, 0) + refinement.usage.get(key, 0)
            raw = refinement.content
        return AgentResult(self.agent_id, self.name, self.role, task.task_id, "COMPLETED",
            str(data.get("summary", "")), findings, list(data.get("limitations", [])),
            list(data.get("open_questions", [])), [m.message_id for m in incoming], raw, usage)

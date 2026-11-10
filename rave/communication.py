import asyncio
from collections import defaultdict
from .contracts import AgentMessage, new_id

class MessageBus:
    """In-memory direct messaging with an auditable event log."""
    def __init__(self, run_id: str):
        self.run_id = run_id
        self._inboxes = defaultdict(asyncio.Queue)
        self.audit_log: list[AgentMessage] = []

    async def send(self, sender: str, recipient: str, message_type: str, task_id: str,
                   content: str, finding_id: str | None = None) -> AgentMessage:
        message = AgentMessage(new_id("msg"), self.run_id, sender, recipient, message_type,
            task_id, content, related_claim_or_finding_id=finding_id)
        self.audit_log.append(message)
        await self._inboxes[recipient].put(message)
        return message

    async def receive_all(self, agent_id: str) -> list[AgentMessage]:
        inbox = self._inboxes[agent_id]
        messages = []
        while not inbox.empty():
            messages.append(inbox.get_nowait())
        return messages

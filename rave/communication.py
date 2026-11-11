import asyncio
from collections import defaultdict
from .contracts import AgentMessage, new_id

class MessageBus:
    """In-memory direct messaging with a publication barrier and audit log."""
    def __init__(self, run_id: str, expected_publishers: int = 3):
        if expected_publishers < 0:
            raise ValueError("expected_publishers cannot be negative")
        self.run_id = run_id
        self._inboxes = defaultdict(asyncio.Queue)
        self.audit_log: list[AgentMessage] = []
        self.expected_publishers = expected_publishers
        self._published = 0
        self._all_published = asyncio.Event()
        if expected_publishers == 0:
            self._all_published.set()

    async def send(self, sender: str, recipient: str, message_type: str, task_id: str,
                   content: str, finding_id: str | None = None) -> AgentMessage:
        message = AgentMessage(new_id("msg"), self.run_id, sender, recipient, message_type,
            task_id, content, related_claim_or_finding_id=finding_id)
        self.audit_log.append(message)
        await self._inboxes[recipient].put(message)
        return message

    async def mark_published(self) -> None:
        if self._published >= self.expected_publishers:
            raise RuntimeError("More agents published than expected")
        self._published += 1
        if self._published >= self.expected_publishers:
            self._all_published.set()

    async def wait_for_all_publishers(self) -> None:
        await self._all_published.wait()

    async def receive_all(self, agent_id: str) -> list[AgentMessage]:
        inbox = self._inboxes[agent_id]
        messages = []
        while not inbox.empty():
            messages.append(inbox.get_nowait())
        return messages

import asyncio
from rave.communication import MessageBus

def test_direct_message_delivery_and_audit():
    async def scenario():
        bus = MessageBus("run-1")
        message = await bus.send("agent-01", "agent-02", "FINDING_SHARE", "task-1", "A finding")
        assert await bus.receive_all("agent-02") == [message]
        assert bus.audit_log == [message]
        assert await bus.receive_all("agent-02") == []
    asyncio.run(scenario())

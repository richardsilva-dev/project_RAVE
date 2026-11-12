from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"

@dataclass
class Evidence:
    source_title: str = ""
    source_url: str = ""
    supporting_excerpt_or_location: str = ""
    accessed_at: str = field(default_factory=now_iso)
    author_or_institution: str = ""
    published_at: str = ""
    updated_at: str = ""
    source_type: str = ""
    origin_finding_ids: list[str] = field(default_factory=list)
    citation_provenance: str = "model_reported"
    citation_origin_agent_ids: list[str] = field(default_factory=list)

@dataclass
class Finding:
    finding_id: str
    run_id: str
    agent_id: str
    task_id: str
    category: str
    title: str
    claim: str
    explanation: str = ""
    evidence: list[Evidence] = field(default_factory=list)
    related_findings: list[str] = field(default_factory=list)
    contributed_by_other_agents: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    evidence_status: str = "INSUFFICIENT"
    status_rationale: str = ""
    origin_finding_ids: list[str] = field(default_factory=list)
    independent_source_count: int = 0
    candidate_source_url_count: int = 0

@dataclass
class AgentTask:
    task_id: str
    run_id: str
    global_question: str
    specialized_question: str
    role: str
    expected_contribution: str
    scope: str
    constraints: list[str] = field(default_factory=list)

@dataclass
class AgentResult:
    agent_id: str
    agent_name: str
    role: str
    task_id: str
    status: str
    summary: str
    findings: list[Finding] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    messages_used: list[str] = field(default_factory=list)
    raw_response: str = ""
    usage: dict[str, int] = field(default_factory=dict)
    web_sources: list[Evidence] = field(default_factory=list)
    phase_timings: dict[str, float] = field(default_factory=dict)
    initial_findings: list[Finding] = field(default_factory=list)
    peer_contributions: list[dict] = field(default_factory=list)
    discarded_findings: list[dict] = field(default_factory=list)
    refinement_status: str = "NOT_RUN"
    refinement_changes: list[dict] = field(default_factory=list)
    failure_type: str = ""

@dataclass
class AgentMessage:
    message_id: str
    run_id: str
    sender_agent_id: str
    recipient_agent_id: str
    message_type: str
    related_task_id: str
    content: str
    created_at: str = field(default_factory=now_iso)
    related_claim_or_finding_id: str | None = None

@dataclass
class RunMetadata:
    run_id: str
    question: str
    configuration: str
    model: str
    started_at: str
    completed_at: str = ""
    duration_seconds: float = 0.0
    total_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    messages_count: int = 0
    status: str = "COMPLETED"
    request_attempts: int = 0
    calls: list[dict] = field(default_factory=list)

def to_dict(value):
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, list):
        return [to_dict(v) for v in value]
    return value

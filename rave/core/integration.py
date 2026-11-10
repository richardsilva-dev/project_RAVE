from collections import defaultdict
from ..contracts import AgentResult

def integrate(results: list[AgentResult]) -> dict:
    local = {r.agent_id: {"role": r.role, "summary": r.summary,
        "finding_ids": [f.finding_id for f in r.findings]} for r in results}
    findings = [f for r in results for f in r.findings]
    by_claim = defaultdict(list)
    for finding in findings:
        normalized = " ".join(finding.claim.lower().split())
        if normalized:
            by_claim[normalized].append(finding.agent_id)
    overlaps = [{"claim": claim, "agents": agents} for claim, agents in by_claim.items() if len(agents) > 1]
    return {"local_contributions": local, "findings": findings, "overlaps": overlaps, "agent_count": len(results)}

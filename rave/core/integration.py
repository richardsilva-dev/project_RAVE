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
    sources = {}
    for result in results:
        for source in result.web_sources:
            if source.source_url:
                item = sources.setdefault(source.source_url, {"title": source.source_title, "url": source.source_url,
                    "accessed_at": source.accessed_at, "agents": []})
                if result.agent_id not in item["agents"]:
                    item["agents"].append(result.agent_id)
        for finding in result.findings:
            for evidence in finding.evidence:
                if not evidence.source_url:
                    continue
                item = sources.setdefault(evidence.source_url, {"title": evidence.source_title,
                    "url": evidence.source_url, "accessed_at": evidence.accessed_at, "agents": []})
                if not item.get("title") and evidence.source_title:
                    item["title"] = evidence.source_title
                if result.agent_id not in item["agents"]:
                    item["agents"].append(result.agent_id)
    # Count distinct cited URLs as a reproducible upper-bound. Different URLs may
    # still syndicate the same underlying report, so this is not proof of independence.
    for finding in findings:
        urls = {e.source_url.strip().rstrip("/").lower() for e in finding.evidence if e.source_url.strip()}
        finding.independent_source_count = len(urls)
        finding.origin_finding_ids = list(dict.fromkeys(finding.origin_finding_ids + [finding.finding_id]))
    return {"local_contributions": local, "findings": findings, "overlaps": overlaps,
        "web_sources": list(sources.values()), "agent_count": len(results),
        "provenance_note": "Distinct URLs are only a candidate independence count; syndication or shared underlying evidence must be checked. Agent agreement alone does not verify a claim."}

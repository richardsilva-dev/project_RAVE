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
    provider_sources = {}
    model_references = {}
    for result in results:
        for source in result.web_sources:
            if source.source_url:
                item = provider_sources.setdefault(source.source_url, {"title": source.source_title,
                    "url": source.source_url, "accessed_at": source.accessed_at,
                    "citation_origin": "provider_tool_annotation", "agents": []})
                if result.agent_id not in item["agents"]:
                    item["agents"].append(result.agent_id)
        for finding in result.findings:
            for evidence in finding.evidence:
                if not evidence.source_url:
                    continue
                if evidence.citation_provenance == "provider_returned":
                    continue
                item = model_references.setdefault(evidence.source_url, {"title": evidence.source_title,
                    "url": evidence.source_url, "reference_origin": "model_json",
                    "agents": [], "finding_ids": [], "occurrences": 0})
                if not item.get("title") and evidence.source_title:
                    item["title"] = evidence.source_title
                if result.agent_id not in item["agents"]:
                    item["agents"].append(result.agent_id)
                if finding.finding_id not in item["finding_ids"]:
                    item["finding_ids"].append(finding.finding_id)
                item["occurrences"] += 1
    # This is a count of candidate URLs in model-produced evidence, not independent sources.
    for finding in findings:
        urls = {e.source_url.strip().rstrip("/").lower() for e in finding.evidence if e.source_url.strip()}
        finding.candidate_source_url_count = len(urls)
        finding.independent_source_count = 0  # deprecated: independence is not inferred from URL count
        finding.origin_finding_ids = list(dict.fromkeys(finding.origin_finding_ids + [finding.finding_id]))
    return {"local_contributions": local, "findings": findings, "overlaps": overlaps,
        "web_sources": list(provider_sources.values()), "model_reported_references": list(model_references.values()),
        "provider_citation_count": len(provider_sources), "model_reported_reference_count": len(model_references),
        "agent_count": len(results),
        "provenance_note": "web_sources contains URLs returned by provider citation annotations; this does not verify truth or semantic support. model_reported_references contains URLs present in agent JSON but absent from those annotations. Distinct URLs are not proof of independent sources. Agent agreement does not verify a claim."}

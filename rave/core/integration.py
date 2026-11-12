from collections import defaultdict
from ..contracts import AgentResult
from ..url_utils import canonicalize_url


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

    # Deduplicate source variants by canonical URL while retaining the exact
    # URLs observed for provenance. Tracking parameters and fragments do not
    # create a new source; meaningful query parameters remain significant.
    sources: dict[str, dict] = {}
    for result in results:
        for source in result.web_sources:
            original_url = (source.source_url or "").strip()
            canonical_url = canonicalize_url(original_url)
            if not canonical_url:
                continue
            entry = sources.setdefault(canonical_url, {
                "title": source.source_title,
                "url": canonical_url,
                "canonical_url": canonical_url,
                "original_urls": [],
                "accessed_at": source.accessed_at,
                "agents": [],
            })
            if original_url and original_url not in entry["original_urls"]:
                entry["original_urls"].append(original_url)
            if result.agent_id not in entry["agents"]:
                entry["agents"].append(result.agent_id)
            if not entry["title"] and source.source_title:
                entry["title"] = source.source_title

    # Distinct canonical URLs are still only a candidate independence count:
    # separate pages can reproduce the same underlying report.
    for finding in findings:
        urls = {
            canonical
            for evidence in finding.evidence
            if (canonical := canonicalize_url(evidence.source_url))
        }
        finding.independent_source_count = len(urls)
        finding.origin_finding_ids = list(dict.fromkeys(finding.origin_finding_ids + [finding.finding_id]))

    return {"local_contributions": local, "findings": findings, "overlaps": overlaps,
        "web_sources": list(sources.values()), "agent_count": len(results),
        "provenance_note": "Canonical URL variants are deduplicated, but distinct URLs may still syndicate or reproduce the same underlying source. URL counts do not establish factual support or source independence; inspect the original sources."}

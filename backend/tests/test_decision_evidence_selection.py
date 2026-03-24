from src.decision import engine


def _mock_run_pipeline(issue_description: str, ticket_type: str, queue: str, top_k: int):
    return {
        "predicted_priority": "HIGH",
        "retrieved_incidents": [
            {
                "doc_id": "incident_13638",
                "distance": 0.5895,
                "type": "INCIDENT",
                "queue": "TECHNICAL SUPPORT",
                "priority": "HIGH",
                "tags": "login, security, it, tech support",
                "issue_description": "Support Required for Authentication Login Issues...",
                "resolution": "Investigate auth changes.",
            },
            {
                "doc_id": "incident_9437",
                "distance": 0.6114,
                "type": "INCIDENT",
                "queue": "CUSTOMER SERVICE",
                "priority": "LOW",
                "tags": "login, performance, network, it, tech support",
                "issue_description": "Customer Support Request for Login Issues...",
                "resolution": "Review server configuration changes.",
            },
            {
                "doc_id": "incident_11491",
                "distance": 0.6157,
                "type": "INCIDENT",
                "queue": "TECHNICAL SUPPORT",
                "priority": "HIGH",
                "tags": "login, it, tech support, performance",
                "issue_description": "Login Issues After Recent Server Update...",
                "resolution": "Check impact of server update.",
            },
            {
                "doc_id": "incident_15934",
                "distance": 0.6189,
                "type": "INCIDENT",
                "queue": "TECHNICAL SUPPORT",
                "priority": "HIGH",
                "tags": "login, it, tech support, performance",
                "issue_description": "Support Required for Login Issues...",
                "resolution": "Gather error details.",
            },
            {
                "doc_id": "incident_12932",
                "distance": 0.6382,
                "type": "INCIDENT",
                "queue": "CUSTOMER SERVICE",
                "priority": "HIGH",
                "tags": "login, disruption, it, tech support",
                "issue_description": "Problem with Login for User Accounts...",
                "resolution": "Collect exact login errors.",
            },
            {
                "doc_id": "incident_8567",
                "distance": 0.6441,
                "type": "INCIDENT",
                "queue": "CUSTOMER SERVICE",
                "priority": "LOW",
                "tags": "login, performance, it, tech support, bug",
                "issue_description": "Request for Assistance with Login Failures...",
                "resolution": "Review server setting changes.",
            },
            {
                "doc_id": "incident_13080",
                "distance": 0.6443,
                "type": "INCIDENT",
                "queue": "CUSTOMER SERVICE",
                "priority": "LOW",
                "tags": "login, performance, it, tech support",
                "issue_description": "Customer Support Inquiry for Login Issues...",
                "resolution": "Inspect server configuration modifications.",
            },
            {
                "doc_id": "incident_7902",
                "distance": 0.6570,
                "type": "INCIDENT",
                "queue": "TECHNICAL SUPPORT",
                "priority": "HIGH",
                "tags": "login, performance, it, tech support",
                "issue_description": "Problem with Login After Recent Updates...",
                "resolution": "Start immediate investigation.",
            },
            {
                "doc_id": "incident_12928",
                "distance": 0.6572,
                "type": "INCIDENT",
                "queue": "PRODUCT SUPPORT",
                "priority": "MEDIUM",
                "tags": "login, network, performance, it, tech support",
                "issue_description": "Problem with Login Authentication...",
                "resolution": "Investigate and gather additional details.",
            },
        ],
    }


def _mock_generate_decision(prompt: str) -> str:
    return """
Assessment Summary:
- Recommended Priority: LOW
- Confidence Score: 0.70
- Confidence Level: Medium
- Why: Queue-aligned incidents were favored by reranking.

Likely Root Cause:
Authentication-related login instability after recent changes.

Evidence from Similar Incidents:
- Multiple login incidents in customer service queue
- Several cases tied to recent configuration/authentication changes
- Historical tickets show mixed priority labels

Immediate Actions:
- Check auth service logs
- Validate recent auth/config deploy diffs
- Confirm error rate and lockout spikes

Next Diagnostic Checks:
- Compare failures by tenant and endpoint
- Verify dependency health and timeouts
- Trace session/token validation path

Escalation Recommendation:
- Yes
- Team: Authentication Team
- Reason: Repeated login failure pattern after auth-related changes
""".strip()


def run_test():
    original_run_pipeline = engine.run_pipeline
    original_generate_decision = engine.generate_decision
    try:
        engine.run_pipeline = _mock_run_pipeline
        engine.generate_decision = _mock_generate_decision

        result = engine.run_full_pipeline_structured(
            issue_description="Customers cannot log in after recent authentication changes",
            ticket_type="INCIDENT",
            queue="CUSTOMER SERVICE",
            top_k=3,
        )

        evidence = result["evidence"]
        kept_ids = [x["doc_id"] for x in evidence]
        kept_queues = [x["queue"] for x in evidence]
        kept_priorities = [x["priority"] for x in evidence]

        assert len(evidence) == 3, f"expected 3 evidence incidents, got {len(evidence)}"
        assert kept_ids == ["incident_12932", "incident_9437", "incident_8567"], (
            f"unexpected kept IDs: {kept_ids}"
        )
        assert result["recommended_priority"] == "MEDIUM", (
            f"expected guardrail recommendation MEDIUM, got {result['recommended_priority']}"
        )
        assert sum(1 for q in kept_queues if q == "CUSTOMER SERVICE") >= 2, (
            f"expected at least 2 same-queue incidents, got {kept_queues}"
        )
        assert kept_priorities.count("LOW") >= 2, (
            f"expected low-priority dominance in kept evidence, got {kept_priorities}"
        )
        assert "incident_13638" not in kept_ids, "expected HIGH technical-support incident to be excluded"
        assert "incident_11491" not in kept_ids, "expected HIGH technical-support incident to be excluded"
        assert all(isinstance(item["tags"], list) for item in evidence), "tags must be list[str]"

        print("[PASS] Evidence selection regression test passed.")
        print(f"       kept_ids={kept_ids}")
        print(f"       kept_queues={kept_queues}")
        print(f"       kept_priorities={kept_priorities}")
    finally:
        engine.run_pipeline = original_run_pipeline
        engine.generate_decision = original_generate_decision


if __name__ == "__main__":
    run_test()

# python -m tests.test_decision_evidence_selection

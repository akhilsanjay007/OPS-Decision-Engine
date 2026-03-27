from __future__ import annotations

import re
import time
import traceback
from collections import Counter
from difflib import SequenceMatcher
from typing import Dict, Any, List

from openai import OpenAI
from src.core.config import (
    get_openai_api_key,
    get_openai_model,
    get_openai_timeout_seconds,
    is_openai_configured,
)
from src.pipeline.predict_and_retrieve import run_pipeline

QUEUE_BOOST = 0.15
TYPE_BOOST = 0.05
PRIORITY_BOOST = 0.03
STRONG_HIGH_DISTANCE_THRESHOLD = 0.65

client: OpenAI | None = None


def get_openai_client() -> OpenAI:
    global client
    if client is not None:
        return client

    api_key = get_openai_api_key()
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Configure it in your environment to use the decision generator."
        )

    client = OpenAI(api_key=api_key)
    return client


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return text


def is_near_duplicate(text_a: str, text_b: str, threshold: float = 0.88) -> bool:
    a = normalize_text(text_a)
    b = normalize_text(text_b)

    if not a or not b:
        return False

    similarity = SequenceMatcher(None, a, b).ratio()
    return similarity >= threshold


def deduplicate_incidents(
    incidents: List[Dict[str, Any]],
    max_results: int = 3,
    threshold: float = 0.88,
    preferred_queue: str | None = None,
    min_same_queue: int = 2,
) -> List[Dict[str, Any]]:
    deduped: List[Dict[str, Any]] = []

    def is_duplicate(candidate: Dict[str, Any], kept_list: List[Dict[str, Any]]) -> bool:
        current_text = candidate.get("issue_description", "")
        for kept in kept_list:
            kept_text = kept.get("issue_description", "")
            if is_near_duplicate(current_text, kept_text, threshold=threshold):
                return True
        return False

    if preferred_queue:
        same_queue_candidates = [
            inc for inc in incidents
            if str(inc.get("queue", "")) == preferred_queue
        ]

        for incident in same_queue_candidates:
            if not is_duplicate(incident, deduped):
                deduped.append(incident)

            if len(deduped) >= min(max_results, min_same_queue):
                break

    for incident in incidents:
        if not is_duplicate(incident, deduped):
            deduped.append(incident)

        if len(deduped) >= max_results:
            break

    return deduped


def rerank_incidents(
    incidents: List[Dict[str, Any]],
    input_queue: str,
    input_type: str,
    predicted_priority: str,
) -> List[Dict[str, Any]]:
    reranked = []

    for inc in incidents:
        distance = float(inc.get("distance", 1.0))
        queue = str(inc.get("queue", ""))
        inc_type = str(inc.get("type", ""))
        priority = str(inc.get("priority", ""))

        adjusted_score = distance

        if queue == input_queue:
            adjusted_score -= QUEUE_BOOST

        if inc_type == input_type:
            adjusted_score -= TYPE_BOOST

        if priority == predicted_priority:
            adjusted_score -= PRIORITY_BOOST

        enriched = dict(inc)
        enriched["adjusted_score"] = adjusted_score
        reranked.append(enriched)

    reranked.sort(key=lambda x: (x["adjusted_score"], x.get("distance", 1.0)))
    return reranked


def format_incidents(incidents: List[Dict[str, Any]]) -> str:
    blocks = []

    for i, inc in enumerate(incidents, start=1):
        block = f"""
Incident #{i}
Type: {inc.get('type', 'N/A')}
Queue: {inc.get('queue', 'N/A')}
Priority: {inc.get('priority', 'N/A')}
Distance: {inc.get('distance', 0.0):.4f}
Adjusted Score: {inc.get('adjusted_score', inc.get('distance', 0.0)):.4f}
Tags: {", ".join(inc.get('tags', [])) if inc.get('tags') else "N/A"}

Issue:
{inc.get('issue_description', 'N/A')}
"""
        blocks.append(block.strip())

    return "\n\n---\n\n".join(blocks)


def normalize_tags(raw_tags: Any) -> List[str]:
    if isinstance(raw_tags, list):
        return [str(tag).strip() for tag in raw_tags if str(tag).strip()]

    if isinstance(raw_tags, str):
        return [tag.strip() for tag in raw_tags.split(",") if tag.strip()]

    return []


def serialize_incident(inc: Dict[str, Any]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "doc_id": inc.get("doc_id"),
        "type": inc.get("type"),
        "queue": inc.get("queue"),
        "priority": inc.get("priority"),
        "distance": float(inc.get("distance", 0.0)),
        "adjusted_score": float(inc.get("adjusted_score", inc.get("distance", 0.0))),
        "tags": normalize_tags(inc.get("tags", [])),
        "issue_description": inc.get("issue_description"),
        "resolution": inc.get("resolution"),
    }

    if "rank" in inc:
        payload["rank"] = inc.get("rank")
    if "retrieval_text" in inc:
        payload["retrieval_text"] = inc.get("retrieval_text")

    return payload


def summarize_retrieval_evidence(
    incidents: List[Dict[str, Any]],
    predicted_priority: str,
    input_queue: str,
) -> str:
    if not incidents:
        return (
            f"ML Predicted Priority: {predicted_priority}\n"
            f"Retrieved Incidents: 0\n"
            f"Queue Match: 0/0\n"
            f"Retrieved Priorities: none\n"
            f"Average Distance: N/A"
        )

    retrieved_priorities = [str(inc.get("priority", "UNKNOWN")) for inc in incidents]
    retrieved_queues = [str(inc.get("queue", "UNKNOWN")) for inc in incidents]
    distances = [float(inc.get("distance", 0.0)) for inc in incidents]

    queue_matches = sum(1 for q in retrieved_queues if q == input_queue)
    avg_distance = sum(distances) / len(distances)

    priority_counts = Counter(retrieved_priorities)
    priority_summary = ", ".join(
        f"{priority}={count}" for priority, count in priority_counts.items()
    )

    return (
        f"ML Predicted Priority: {predicted_priority}\n"
        f"Retrieved Incidents: {len(incidents)}\n"
        f"Queue Match: {queue_matches}/{len(incidents)}\n"
        f"Retrieved Priorities: {priority_summary}\n"
        f"Average Distance: {avg_distance:.4f}"
    )


def compute_confidence_score(
    incidents: List[Dict[str, Any]],
    predicted_priority: str,
    input_queue: str,
) -> float:
    if not incidents:
        return 0.20

    retrieved_priorities = [str(inc.get("priority", "UNKNOWN")) for inc in incidents]
    retrieved_queues = [str(inc.get("queue", "UNKNOWN")) for inc in incidents]
    distances = [float(inc.get("distance", 1.0)) for inc in incidents]

    same_queue_count = sum(1 for q in retrieved_queues if q == input_queue)
    avg_distance = sum(distances) / len(distances)
    majority_priority, majority_count = Counter(retrieved_priorities).most_common(1)[0]

    score = 0.0

    if majority_priority == predicted_priority:
        score += 0.30

    if majority_count >= 2:
        score += 0.25

    if same_queue_count >= 2:
        score += 0.25
    elif same_queue_count == 1:
        score += 0.10

    if avg_distance < 0.65:
        score += 0.20
    elif avg_distance < 0.73:
        score += 0.15
    elif avg_distance < 0.80:
        score += 0.10

    return round(min(score, 1.0), 2)


def confidence_level_from_score(score: float) -> str:
    if score >= 0.75:
        return "High"
    if score >= 0.45:
        return "Medium"
    return "Low"


def recommend_priority(ml_priority: str, incidents: List[Dict[str, Any]]) -> str:
    if not incidents:
        return ml_priority

    retrieved_priorities = [str(inc.get("priority", "UNKNOWN")) for inc in incidents]
    priority_counts = Counter(retrieved_priorities)
    majority_priority, majority_count = priority_counts.most_common(1)[0]

    # Guardrail: avoid overly aggressive downgrade from HIGH to LOW when
    # there is still a reasonably strong HIGH-similarity incident in evidence.
    if ml_priority == "HIGH" and majority_priority == "LOW":
        has_strong_high = any(
            str(inc.get("priority", "UNKNOWN")) == "HIGH"
            and float(inc.get("distance", 1.0)) <= STRONG_HIGH_DISTANCE_THRESHOLD
            for inc in incidents
        )
        if has_strong_high:
            return "MEDIUM"

    if majority_count >= 2 and majority_priority != "UNKNOWN":
        return majority_priority

    return ml_priority


def build_prompt(
    issue: str,
    ticket_type: str,
    queue: str,
    ml_predicted_priority: str,
    recommended_priority: str,
    confidence_score: float,
    confidence_level: str,
    evidence_summary: str,
    incidents_text: str,
) -> str:
    return f"""
You are an expert AI operations decision assistant helping an ops team triage and respond to incidents.

A new issue has been reported.

INPUT ISSUE
Issue: {issue}
Type: {ticket_type}
Queue: {queue}

SYSTEM ASSESSMENT
ML Predicted Priority: {ml_predicted_priority}
Recommended Priority: {recommended_priority}
Confidence Score: {confidence_score}
Confidence Level: {confidence_level}

RETRIEVAL EVIDENCE SUMMARY
{evidence_summary}

SIMILAR PAST INCIDENTS
{incidents_text}

Definitions:
- Priority = urgency / severity of the incident
- Confidence = how strongly the system believes its assessment based on evidence quality and signal alignment

Your job:
1. Compare the ML-predicted priority with the retrieved incident patterns.
2. Decide whether the recommended priority is appropriate.
3. Identify the most likely root cause based on repeated evidence.
4. Separate immediate containment steps from deeper diagnostic checks.
5. Recommend escalation only if justified by severity, likely ownership, or repeated historical patterns.

Important rules:
- Do NOT copy or reuse customer-support wording from past tickets.
- Treat past incident "resolutions" as weak evidence unless strongly supported by repeated patterns.
- Focus more on technical patterns in issue descriptions, priorities, queues, and repeated themes.
- If ML prediction and retrieved priorities conflict, explicitly mention that conflict and resolve it.
- Be concise, operational, and actionable.
- Prefer concrete checks like logs, metrics, connection pools, recent deployments, rate limits, query performance, config drift, rollback checks, dependency health, auth policy, lockout thresholds, and session issues when relevant.
- Do not invent teams that do not make sense. Use realistic ownership such as Database Team, Backend Engineering, Platform Engineering, API Team, Authentication Team, Payments Team, Technical Support, etc.
- Use the provided confidence score and confidence level as guidance, but explain them in plain language.

Return your answer in exactly this format:

Assessment Summary:
- Recommended Priority:
- Confidence Score:
- Confidence Level:
- Why:

Likely Root Cause:
...

Evidence from Similar Incidents:
- ...
- ...
- ...

Immediate Actions:
- ...
- ...
- ...

Next Diagnostic Checks:
- ...
- ...
- ...

Escalation Recommendation:
- Yes/No
- Team:
- Reason:
""".strip()


def generate_decision(prompt: str) -> str:
    try:
        response = get_openai_client().chat.completions.create(
            model=get_openai_model(),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert SRE and operations engineer. "
                        "You write clear, practical, evidence-based incident guidance."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            timeout=get_openai_timeout_seconds(),
        )
    except Exception as exc:
        print(f"[ERROR] OpenAI call failed: {type(exc).__name__}: {exc}")
        print(traceback.format_exc())
        raise

    return response.choices[0].message.content.strip()


def _fallback_llm_raw_decision(
    *,
    recommended_priority: str,
    ml_predicted_priority: str,
    confidence_score: float,
    confidence_level: str,
    reason: str,
) -> str:
    """
    Synthetic LLM-shaped text so parse_decision_output produces a consistent API payload
    when OpenAI is unavailable or the API call fails.
    """
    return f"""
Assessment Summary:
- Recommended Priority: {recommended_priority}
- Confidence Score: {confidence_score}
- Confidence Level: {confidence_level}
- Why: {reason}

Likely Root Cause:
{reason}

Evidence from Similar Incidents:
- Use the structured evidence list returned by this API (ML + RAG) for similar past incidents.

Immediate Actions:
- Treat ML predicted priority ({ml_predicted_priority}) and recommended priority ({recommended_priority}) as operational signals.
- Review retrieved incident evidence and apply your standard runbooks.
- Set OPENAI_API_KEY (and optionally OPENAI_MODEL) to enable full LLM-generated guidance.

Next Diagnostic Checks:
- Follow queue-specific diagnostics; correlate with recent changes, dependencies, and observability data.

Escalation Recommendation:
- No
- Team:
- Reason: Automated escalation text requires LLM generation; configure OpenAI when ready.
""".strip()


def parse_section(text: str, header: str, next_headers: List[str]) -> str:
    pattern = rf"{re.escape(header)}\s*(.*?)(?=\n(?:{'|'.join(map(re.escape, next_headers))})|\Z)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""


def parse_bullets(section_text: str) -> List[str]:
    lines = []
    for line in section_text.splitlines():
        cleaned = line.strip()
        if cleaned.startswith("-"):
            lines.append(cleaned[1:].strip())
    return lines


def parse_decision_output(decision_text: str) -> Dict[str, Any]:
    sections = {
        "assessment_summary": parse_section(
            decision_text,
            "Assessment Summary:",
            [
                "Likely Root Cause:",
                "Evidence from Similar Incidents:",
                "Immediate Actions:",
                "Next Diagnostic Checks:",
                "Escalation Recommendation:",
            ],
        ),
        "root_cause": parse_section(
            decision_text,
            "Likely Root Cause:",
            [
                "Evidence from Similar Incidents:",
                "Immediate Actions:",
                "Next Diagnostic Checks:",
                "Escalation Recommendation:",
            ],
        ),
        "evidence_section": parse_section(
            decision_text,
            "Evidence from Similar Incidents:",
            [
                "Immediate Actions:",
                "Next Diagnostic Checks:",
                "Escalation Recommendation:",
            ],
        ),
        "immediate_actions": parse_section(
            decision_text,
            "Immediate Actions:",
            [
                "Next Diagnostic Checks:",
                "Escalation Recommendation:",
            ],
        ),
        "next_diagnostics": parse_section(
            decision_text,
            "Next Diagnostic Checks:",
            ["Escalation Recommendation:"],
        ),
        "escalation_section": parse_section(
            decision_text,
            "Escalation Recommendation:",
            [],
        ),
    }

    escalation_lines = parse_bullets(sections["escalation_section"])

    escalation = {
        "raw": sections["escalation_section"],
        "decision": escalation_lines[0] if len(escalation_lines) > 0 else "",
        "team": escalation_lines[1].replace("Team:", "").strip() if len(escalation_lines) > 1 else "",
        "reason": escalation_lines[2].replace("Reason:", "").strip() if len(escalation_lines) > 2 else "",
    }

    return {
        "assessment_summary": sections["assessment_summary"],
        "root_cause": sections["root_cause"],
        "evidence_from_similar_incidents": parse_bullets(sections["evidence_section"]),
        "action_plan": parse_bullets(sections["immediate_actions"]),
        "next_diagnostics": parse_bullets(sections["next_diagnostics"]),
        "escalation_recommendation": escalation,
        "raw_decision": decision_text,
    }


def run_full_pipeline_structured(
    issue_description: str,
    ticket_type: str,
    queue: str,
    top_k: int = 3,
    include_debug: bool = False,
    retrieval_enabled: bool = True,
    resources: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    request_start = time.perf_counter()
    print(
        "[INFO] /predict pipeline started "
        f"(type={ticket_type!r}, queue={queue!r}, issue_chars={len(issue_description)})"
    )
    retrieval_top_k = max(top_k * 3, 8)

    predict_retrieve_start = time.perf_counter()
    result = run_pipeline(
        issue_description=issue_description,
        ticket_type=ticket_type,
        queue=queue,
        top_k=retrieval_top_k,
        retrieval_enabled=retrieval_enabled,
        model=resources.get("model") if resources else None,
        embedder=resources.get("embedder") if resources else None,
        collection=resources.get("collection") if resources else None,
    )
    predict_retrieve_elapsed_ms = (time.perf_counter() - predict_retrieve_start) * 1000
    stage_timings = dict(result.get("timings_ms", {}))
    stage_timings["predict_plus_retrieve"] = round(predict_retrieve_elapsed_ms, 2)
    print(
        "[TIMING] stage=ml_prediction_ms "
        f"value={stage_timings.get('ml_prediction', 'n/a')}"
    )
    print(
        "[TIMING] stage=retrieval_chroma_ms "
        f"value={stage_timings.get('retrieval_chroma', 'n/a')}"
    )
    print(
        f"[DEBUG] after retrieval: predicted_priority={result.get('predicted_priority')}, "
        f"retrieved_count={len(result.get('retrieved_incidents', []))}"
    )

    raw_incidents = result["retrieved_incidents"]
    ml_predicted_priority = result["predicted_priority"]

    rerank_start = time.perf_counter()
    reranked_incidents = rerank_incidents(
        raw_incidents,
        input_queue=queue,
        input_type=ticket_type,
        predicted_priority=ml_predicted_priority,
    )
    rerank_elapsed_ms = (time.perf_counter() - rerank_start) * 1000
    stage_timings["reranking"] = round(rerank_elapsed_ms, 2)
    print(f"[TIMING] stage=reranking_ms value={stage_timings['reranking']}")
    print(f"[DEBUG] after reranking: reranked_count={len(reranked_incidents)}")

    dedup_start = time.perf_counter()
    incidents = deduplicate_incidents(
        reranked_incidents,
        max_results=top_k,
        threshold=0.88,
        preferred_queue=queue,
        min_same_queue=2,
    )
    dedup_elapsed_ms = (time.perf_counter() - dedup_start) * 1000
    stage_timings["deduplication"] = round(dedup_elapsed_ms, 2)
    print(f"[TIMING] stage=deduplication_ms value={stage_timings['deduplication']}")
    print(f"[DEBUG] after deduplication: deduped_count={len(incidents)}")

    recommended_priority = recommend_priority(
        ml_priority=ml_predicted_priority,
        incidents=incidents,
    )
    print(f"[DEBUG] after priority recommendation: recommended_priority={recommended_priority}")

    confidence_score = compute_confidence_score(
        incidents=incidents,
        predicted_priority=ml_predicted_priority,
        input_queue=queue,
    )
    confidence_level = confidence_level_from_score(confidence_score)
    print(
        f"[DEBUG] after confidence calculation: score={confidence_score}, "
        f"level={confidence_level}"
    )

    evidence_summary = summarize_retrieval_evidence(
        incidents=incidents,
        predicted_priority=ml_predicted_priority,
        input_queue=queue,
    )
    print(
        f"[DEBUG] after evidence summary build: summary_chars={len(evidence_summary)}"
    )

    incidents_text = format_incidents(incidents)

    prompt = build_prompt(
        issue=issue_description,
        ticket_type=ticket_type,
        queue=queue,
        ml_predicted_priority=ml_predicted_priority,
        recommended_priority=recommended_priority,
        confidence_score=confidence_score,
        confidence_level=confidence_level,
        evidence_summary=evidence_summary,
        incidents_text=incidents_text,
    )
    print(f"[DEBUG] after prompt build: prompt_chars={len(prompt)}")

    openai_elapsed_ms = 0.0
    if is_openai_configured():
        try:
            openai_start = time.perf_counter()
            decision_text = generate_decision(prompt)
            openai_elapsed_ms = (time.perf_counter() - openai_start) * 1000
            stage_timings["openai_call"] = round(openai_elapsed_ms, 2)
            print(f"[TIMING] stage=openai_call_ms value={stage_timings['openai_call']}")
            print(
                f"[DEBUG] after OpenAI response returns: response_chars={len(decision_text)}"
            )
        except Exception as exc:
            openai_elapsed_ms = (time.perf_counter() - openai_start) * 1000
            stage_timings["openai_call"] = round(openai_elapsed_ms, 2)
            print(f"[TIMING] stage=openai_call_ms value={stage_timings['openai_call']}")
            print(f"[WARN] OpenAI generation failed; using fallback response: {exc}")
            reason = (
                f"OpenAI request failed ({type(exc).__name__}). "
                "ML priority and retrieval evidence remain valid."
            )
            decision_text = _fallback_llm_raw_decision(
                recommended_priority=recommended_priority,
                ml_predicted_priority=ml_predicted_priority,
                confidence_score=confidence_score,
                confidence_level=confidence_level,
                reason=reason,
            )
    else:
        stage_timings["openai_call"] = 0.0
        print("[INFO] OPENAI_API_KEY not set; returning LLM fallback (ML + RAG still active).")
        reason = (
            "OPENAI_API_KEY is not set. ML predicted priority and RAG retrieval are still available; "
            "configure the API key for full LLM-generated triage."
        )
        decision_text = _fallback_llm_raw_decision(
            recommended_priority=recommended_priority,
            ml_predicted_priority=ml_predicted_priority,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            reason=reason,
        )

    parsed = parse_decision_output(decision_text)
    print(
        "[DEBUG] after parsing decision output: "
        f"action_plan_items={len(parsed.get('action_plan', []))}, "
        f"diagnostic_items={len(parsed.get('next_diagnostics', []))}, "
        f"evidence_bullets={len(parsed.get('evidence_from_similar_incidents', []))}"
    )

    evidence = [serialize_incident(inc) for inc in incidents]
    print(f"[DEBUG] after final evidence construction: evidence_items={len(evidence)}")

    print("[DEBUG] before final return")
    response = {
        "input_issue": issue_description,
        "input_type": ticket_type,
        "input_queue": queue,
        "recommended_priority": recommended_priority,
        "ml_predicted_priority": ml_predicted_priority,
        "rag_signal_priority": recommended_priority,
        "confidence_score": confidence_score,
        "confidence_level": confidence_level,
        "root_cause": parsed["root_cause"],
        "action_plan": parsed["action_plan"],
        "next_diagnostics": parsed["next_diagnostics"],
        "escalation_recommendation": parsed["escalation_recommendation"],
        "evidence_from_similar_incidents": parsed["evidence_from_similar_incidents"],
        "evidence": evidence,
        "assessment_summary": parsed["assessment_summary"],
        "raw_decision": parsed["raw_decision"],
    }

    total_elapsed_ms = (time.perf_counter() - request_start) * 1000
    stage_timings["total_request"] = round(total_elapsed_ms, 2)
    print(f"[TIMING] stage=total_request_ms value={stage_timings['total_request']}")

    if include_debug:
        response["raw_retrieved_incidents"] = [serialize_incident(inc) for inc in raw_incidents]
        response["reranked_incidents"] = [serialize_incident(inc) for inc in reranked_incidents]
        response["deduplicated_incidents"] = [serialize_incident(inc) for inc in incidents]
        response["evidence_summary"] = evidence_summary
        response["prompt"] = prompt
        response["timings_ms"] = stage_timings

    return response


def run_full_pipeline_structured_debug(
    issue_description: str,
    ticket_type: str,
    queue: str,
    top_k: int = 3,
    retrieval_enabled: bool = True,
    resources: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return run_full_pipeline_structured(
        issue_description=issue_description,
        ticket_type=ticket_type,
        queue=queue,
        top_k=top_k,
        include_debug=True,
        retrieval_enabled=retrieval_enabled,
        resources=resources,
    )
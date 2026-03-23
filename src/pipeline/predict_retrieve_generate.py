from __future__ import annotations

import argparse
import os
import re
from collections import Counter
from difflib import SequenceMatcher
from typing import Dict, Any, List

from openai import OpenAI

from src.pipeline.predict_and_retrieve import run_pipeline


# ---------------- CONFIG ---------------- #

OPENAI_MODEL = "gpt-4o-mini"

# Reranking weights
QUEUE_BOOST = 0.08
TYPE_BOOST = 0.04
PRIORITY_BOOST = 0.03


# ---------------- INIT LLM ---------------- #

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ---------------- HELPERS ---------------- #

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
) -> List[Dict[str, Any]]:
    deduped: List[Dict[str, Any]] = []

    for incident in incidents:
        current_text = incident.get("issue_description", "")

        duplicate_found = False
        for kept in deduped:
            kept_text = kept.get("issue_description", "")
            if is_near_duplicate(current_text, kept_text, threshold=threshold):
                duplicate_found = True
                break

        if not duplicate_found:
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


def recommend_priority(
    ml_priority: str,
    incidents: List[Dict[str, Any]],
) -> str:
    if not incidents:
        return ml_priority

    retrieved_priorities = [str(inc.get("priority", "UNKNOWN")) for inc in incidents]
    priority_counts = Counter(retrieved_priorities)
    majority_priority, majority_count = priority_counts.most_common(1)[0]

    if majority_count >= 2 and majority_priority != "UNKNOWN":
        return majority_priority

    return ml_priority


# ---------------- BUILD PROMPT ---------------- #

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


# ---------------- GENERATE RESPONSE ---------------- #

def generate_decision(prompt: str) -> str:
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
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
    )

    return response.choices[0].message.content.strip()


# ---------------- MAIN PIPELINE ---------------- #

def run_full_pipeline(
    issue_description: str,
    ticket_type: str,
    queue: str,
    top_k: int = 3,
    verbose: bool = True,
) -> str:
    if verbose:
        print("\n" + "=" * 120)
        print("OPS DECISION ENGINE - FULL PIPELINE")
        print("=" * 120)

    retrieval_top_k = max(top_k * 3, 8)

    result = run_pipeline(
        issue_description=issue_description,
        ticket_type=ticket_type,
        queue=queue,
        top_k=retrieval_top_k,
    )

    raw_incidents = result["retrieved_incidents"]
    ml_predicted_priority = result["predicted_priority"]

    reranked_incidents = rerank_incidents(
        raw_incidents,
        input_queue=queue,
        input_type=ticket_type,
        predicted_priority=ml_predicted_priority,
    )

    incidents = deduplicate_incidents(
        reranked_incidents,
        max_results=top_k,
        threshold=0.88,
    )

    if verbose:
        print(f"[INFO] Retrieved {len(raw_incidents)} incidents.")
        print(f"[INFO] Kept {len(incidents)} incidents after reranking + deduplication.")

    recommended_priority = recommend_priority(
        ml_priority=ml_predicted_priority,
        incidents=incidents,
    )

    confidence_score = compute_confidence_score(
        incidents=incidents,
        predicted_priority=ml_predicted_priority,
        input_queue=queue,
    )
    confidence_level = confidence_level_from_score(confidence_score)

    evidence_summary = summarize_retrieval_evidence(
        incidents=incidents,
        predicted_priority=ml_predicted_priority,
        input_queue=queue,
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

    if verbose:
        print("\n[INFO] Generating decision using LLM...\n")
    decision = generate_decision(prompt)

    if verbose:
        print("\n" + "=" * 120)
        print("FINAL DECISION")
        print("=" * 120)
        print(decision)

    return decision


# ---------------- CLI ---------------- #

def parse_args():
    parser = argparse.ArgumentParser(description="Full Ops Decision Engine")

    parser.add_argument("--issue", type=str, required=True, help="Issue description")
    parser.add_argument("--type", type=str, required=True, help="Ticket type")
    parser.add_argument("--queue", type=str, required=True, help="Queue name")
    parser.add_argument("--top_k", type=int, default=3, help="Number of final incidents used")

    return parser.parse_args()


# ---------------- RUN ---------------- #

if __name__ == "__main__":
    args = parse_args()

    run_full_pipeline(
        issue_description=args.issue,
        ticket_type=args.type,
        queue=args.queue,
        top_k=args.top_k,
        verbose=True,
    )
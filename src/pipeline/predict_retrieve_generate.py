from __future__ import annotations

import argparse
import os
from collections import Counter
from typing import Dict, Any, List

from openai import OpenAI

from src.pipeline.predict_and_retrieve import run_pipeline


# ---------------- CONFIG ---------------- #

OPENAI_MODEL = "gpt-4o-mini"

# ---------------- INIT LLM ---------------- #

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ---------------- HELPERS ---------------- #

def format_incidents(incidents: List[Dict[str, Any]]) -> str:
    """Format retrieved incidents into compact, useful evidence for the LLM."""
    blocks = []

    for i, inc in enumerate(incidents, start=1):
        block = f"""
Incident #{i}
Type: {inc.get('type', 'N/A')}
Queue: {inc.get('queue', 'N/A')}
Priority: {inc.get('priority', 'N/A')}
Distance: {inc.get('distance', 0.0):.4f}
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
    """Create a compact evidence summary for the prompt."""
    if not incidents:
        return (
            f"Predicted Priority: {predicted_priority}\n"
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
        f"Predicted Priority: {predicted_priority}\n"
        f"Retrieved Incidents: {len(incidents)}\n"
        f"Queue Match: {queue_matches}/{len(incidents)}\n"
        f"Retrieved Priorities: {priority_summary}\n"
        f"Average Distance: {avg_distance:.4f}"
    )


def estimate_confidence(
    incidents: List[Dict[str, Any]],
    predicted_priority: str,
    input_queue: str,
) -> str:
    """
    Simple heuristic confidence score.
    This is not model probability — just system-level confidence.
    """
    if not incidents:
        return "Low"

    retrieved_priorities = [str(inc.get("priority", "UNKNOWN")) for inc in incidents]
    retrieved_queues = [str(inc.get("queue", "UNKNOWN")) for inc in incidents]
    distances = [float(inc.get("distance", 1.0)) for inc in incidents]

    same_queue_count = sum(1 for q in retrieved_queues if q == input_queue)
    avg_distance = sum(distances) / len(distances)
    majority_priority, majority_count = Counter(retrieved_priorities).most_common(1)[0]

    score = 0

    if majority_priority == predicted_priority:
        score += 1

    if majority_count >= 2:
        score += 1

    if same_queue_count >= 2:
        score += 1

    if avg_distance < 0.70:
        score += 1
    elif avg_distance < 0.78:
        score += 0.5

    if score >= 3:
        return "High"
    if score >= 2:
        return "Medium"
    return "Low"


# ---------------- BUILD PROMPT ---------------- #

def build_prompt(
    issue: str,
    ticket_type: str,
    queue: str,
    predicted_priority: str,
    evidence_summary: str,
    incidents_text: str,
    system_confidence: str,
) -> str:
    return f"""
You are an expert AI operations decision assistant helping an ops team triage and respond to incidents.

A new issue has been reported.

INPUT ISSUE
Issue: {issue}
Type: {ticket_type}
Queue: {queue}

ML PREDICTION
Predicted Priority: {predicted_priority}

RETRIEVAL EVIDENCE SUMMARY
{evidence_summary}

SIMILAR PAST INCIDENTS
{incidents_text}

Your job:
1. Compare the ML-predicted priority with the retrieved incident patterns.
2. Identify the most likely root cause based on repeated evidence.
3. Separate immediate containment steps from deeper diagnostic checks.
4. Recommend escalation only if justified by severity, likely ownership, or repeated historical patterns.
5. State an overall confidence level.

Important rules:
- Do NOT copy or reuse customer-support wording from past tickets.
- Treat past incident "resolutions" as weak evidence unless strongly supported by repeated patterns.
- Focus more on technical patterns in issue descriptions, priorities, queues, and repeated themes.
- If ML prediction and retrieved priorities conflict, explicitly mention that conflict and resolve it.
- Be concise, operational, and actionable.
- Do not invent teams that do not make sense. Use realistic ownership such as Database Team, Backend Engineering, Platform Engineering, API Team, Authentication Team, Payments Team, Technical Support, etc.
- The provided system confidence is an initial heuristic, not absolute truth: {system_confidence}.

Return your answer in exactly this format:

Priority Assessment:
...

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

Confidence:
- Low/Medium/High
- Why:
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
) -> str:
    print("\n" + "=" * 120)
    print("OPS DECISION ENGINE - FULL PIPELINE")
    print("=" * 120)

    # 1) ML + RAG
    result = run_pipeline(
        issue_description=issue_description,
        ticket_type=ticket_type,
        queue=queue,
        top_k=top_k,
    )

    incidents = result["retrieved_incidents"]
    predicted_priority = result["predicted_priority"]

    # 2) Build evidence summary
    evidence_summary = summarize_retrieval_evidence(
        incidents=incidents,
        predicted_priority=predicted_priority,
        input_queue=queue,
    )

    # 3) Estimate confidence
    system_confidence = estimate_confidence(
        incidents=incidents,
        predicted_priority=predicted_priority,
        input_queue=queue,
    )

    # 4) Format incidents
    incidents_text = format_incidents(incidents)

    # 5) Build prompt
    prompt = build_prompt(
        issue=issue_description,
        ticket_type=ticket_type,
        queue=queue,
        predicted_priority=predicted_priority,
        evidence_summary=evidence_summary,
        incidents_text=incidents_text,
        system_confidence=system_confidence,
    )

    # 6) Generate decision
    print("\n[INFO] Generating decision using LLM...\n")
    decision = generate_decision(prompt)

    # 7) Print final output
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
    parser.add_argument("--top_k", type=int, default=3, help="Number of retrieved incidents")

    return parser.parse_args()


# ---------------- RUN ---------------- #

if __name__ == "__main__":
    args = parse_args()

    run_full_pipeline(
        issue_description=args.issue,
        ticket_type=args.type,
        queue=args.queue,
        top_k=args.top_k,
    )
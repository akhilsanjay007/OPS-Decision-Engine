from __future__ import annotations

import argparse
import os
from typing import Dict, Any, List

from openai import OpenAI

from src.pipeline.predict_and_retrieve import run_pipeline


# ---------------- INIT LLM ---------------- #

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ---------------- FORMAT RETRIEVED INCIDENTS ---------------- #

def format_incidents(incidents: List[Dict[str, Any]]) -> str:
    text = ""

    for i, inc in enumerate(incidents, start=1):
        text += f"""
Incident #{i}
Type: {inc['type']}
Queue: {inc['queue']}
Priority: {inc['priority']}

Issue:
{inc['issue_description']}

---
"""

    return text.strip()


# ---------------- BUILD PROMPT ---------------- #

def build_prompt(
    issue: str,
    predicted_priority: str,
    incidents_text: str,
) -> str:

    return f"""
You are an AI operations decision assistant.

A new issue has been reported:

ISSUE:
{issue}

Predicted Priority: {predicted_priority}

Similar past incidents:
{incidents_text}

Your task:

1. Identify common patterns across incidents
2. Infer the most likely root cause
3. Suggest a clear action plan
4. Recommend whether escalation is needed

Important:
- Do NOT copy past responses
- Focus on reasoning from patterns
- Be concise and actionable

Output format:

Root Cause:
...

Action Plan:
- step 1
- step 2
- step 3

Escalation:
- Yes/No
- If yes, which team and why
"""


# ---------------- GENERATE RESPONSE ---------------- #

def generate_decision(prompt: str) -> str:

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert SRE/operations engineer."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content.strip()


# ---------------- MAIN PIPELINE ---------------- #

def run_full_pipeline(
    issue_description: str,
    ticket_type: str,
    queue: str,
    top_k: int = 3,
):

    print("\n" + "=" * 120)
    print("OPS DECISION ENGINE - FULL PIPELINE")
    print("=" * 120)

    # 1️⃣ ML + RAG
    result = run_pipeline(
        issue_description=issue_description,
        ticket_type=ticket_type,
        queue=queue,
        top_k=top_k,
    )

    # 2️⃣ Format incidents
    incidents_text = format_incidents(result["retrieved_incidents"])

    # 3️⃣ Build prompt
    prompt = build_prompt(
        issue=issue_description,
        predicted_priority=result["predicted_priority"],
        incidents_text=incidents_text,
    )

    # 4️⃣ Generate decision
    print("\n[INFO] Generating decision using LLM...\n")
    decision = generate_decision(prompt)

    # 5️⃣ Print final output
    print("\n" + "=" * 120)
    print("FINAL DECISION")
    print("=" * 120)
    print(decision)

    return decision


# ---------------- CLI ---------------- #

def parse_args():
    parser = argparse.ArgumentParser(description="Full Ops Decision Engine")

    parser.add_argument("--issue", type=str, required=True)
    parser.add_argument("--type", type=str, required=True)
    parser.add_argument("--queue", type=str, required=True)
    parser.add_argument("--top_k", type=int, default=3)

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
import csv
import os
import re
from typing import List, Dict, Any

from src.pipeline.predict_retrieve_generate import (
    run_full_pipeline,
    confidence_level_from_score,
    compute_confidence_score,
    recommend_priority,
    rerank_incidents,
    deduplicate_incidents,
)
from src.pipeline.predict_and_retrieve import run_pipeline


TEST_CASES = [
    {
        "name": "Database Timeout After Deployment",
        "issue": "Database timeout errors after deployment",
        "type": "INCIDENT",
        "queue": "TECHNICAL SUPPORT",
    },
    {
        "name": "Payment API Timeout",
        "issue": "Payment API timeout errors for enterprise customers",
        "type": "INCIDENT",
        "queue": "BILLING AND PAYMENTS",
    },
    {
        "name": "Login Failure After Password Reset",
        "issue": "Users unable to login after password reset",
        "type": "INCIDENT",
        "queue": "CUSTOMER SERVICE",
    },
    {
        "name": "Account Lockout",
        "issue": "User account locked after multiple failed login attempts",
        "type": "INCIDENT",
        "queue": "CUSTOMER SERVICE",
    },
    {
        "name": "High API Latency",
        "issue": "High latency in API responses after deployment",
        "type": "INCIDENT",
        "queue": "PRODUCT SUPPORT",
    },
]

OUTPUT_CSV = "artifacts/evaluation/pipeline_evaluation_results.csv"


def extract_escalation(decision_text: str) -> str:
    match = re.search(r"Escalation Recommendation:\s*-\s*(Yes|No)", decision_text, re.IGNORECASE)
    return match.group(1).capitalize() if match else "Unknown"


def extract_recommended_priority(decision_text: str) -> str:
    match = re.search(
        r"Assessment Summary:\s*- Recommended Priority:\s*(LOW|MEDIUM|HIGH|CRITICAL)",
        decision_text,
        re.IGNORECASE,
    )
    return match.group(1).upper() if match else "UNKNOWN"


def evaluate_case(test: Dict[str, str]) -> Dict[str, Any]:
    # Step 1: predict + retrieve
    base_result = run_pipeline(
        issue_description=test["issue"],
        ticket_type=test["type"],
        queue=test["queue"],
        top_k=9,
    )

    raw_incidents = base_result["retrieved_incidents"]
    ml_priority = base_result["predicted_priority"]

    reranked = rerank_incidents(
        raw_incidents,
        input_queue=test["queue"],
        input_type=test["type"],
        predicted_priority=ml_priority,
    )

    final_incidents = deduplicate_incidents(
        reranked,
        max_results=3,
        threshold=0.88,
        preferred_queue=test["queue"],
        min_same_queue=2,
    )

    recommended_priority = recommend_priority(
        ml_priority=ml_priority,
        incidents=final_incidents,
    )

    confidence_score = compute_confidence_score(
        incidents=final_incidents,
        predicted_priority=ml_priority,
        input_queue=test["queue"],
    )
    confidence_level = confidence_level_from_score(confidence_score)

    same_queue_count = sum(
        1 for inc in final_incidents if str(inc.get("queue", "")) == test["queue"]
    )

    # Step 2: full pipeline generation
    decision = run_full_pipeline(
        issue_description=test["issue"],
        ticket_type=test["type"],
        queue=test["queue"],
        top_k=3,
        verbose=False,
    )

    escalation = extract_escalation(decision)
    llm_priority = extract_recommended_priority(decision)

    return {
        "name": test["name"],
        "issue": test["issue"],
        "type": test["type"],
        "queue": test["queue"],
        "ml_priority": ml_priority,
        "recommended_priority_rule": recommended_priority,
        "llm_priority": llm_priority,
        "confidence_score": confidence_score,
        "confidence_level": confidence_level,
        "same_queue_count": same_queue_count,
        "num_incidents": len(final_incidents),
        "same_queue_ratio": round(same_queue_count / max(len(final_incidents), 1), 2),
        "escalation": escalation,
        "retrieval_query": base_result.get("retrieval_query", ""),
    }


def print_case_report(result: Dict[str, Any]) -> None:
    print("\n" + "-" * 120)
    print(f"Case: {result['name']}")
    print("-" * 120)
    print(f"Issue                : {result['issue']}")
    print(f"Queue                : {result['queue']}")
    print(f"ML Priority          : {result['ml_priority']}")
    print(f"Recommended Priority : {result['recommended_priority_rule']}")
    print(f"LLM Priority         : {result['llm_priority']}")
    print(f"Confidence Score     : {result['confidence_score']}")
    print(f"Confidence Level     : {result['confidence_level']}")
    print(f"Same Queue Evidence  : {result['same_queue_count']}/{result['num_incidents']}")
    print(f"Escalation           : {result['escalation']}")


def print_summary(results: List[Dict[str, Any]]) -> None:
    total = len(results)
    conflicts = sum(1 for r in results if r["ml_priority"] != r["recommended_priority_rule"])
    escalations = sum(1 for r in results if r["escalation"] == "Yes")
    avg_confidence = round(sum(r["confidence_score"] for r in results) / total, 2) if total else 0.0
    avg_same_queue_ratio = round(
        sum(r["same_queue_ratio"] for r in results) / total,
        2,
    ) if total else 0.0

    print("\n" + "=" * 120)
    print("PIPELINE EVALUATION SUMMARY")
    print("=" * 120)
    print(f"Total Cases                 : {total}")
    print(f"ML/RAG Priority Conflicts   : {conflicts}")
    print(f"Cases Escalated             : {escalations}")
    print(f"Average Confidence Score    : {avg_confidence}")
    print(f"Average Same-Queue Ratio    : {avg_same_queue_ratio}")


def save_results_to_csv(results: List[Dict[str, Any]], output_csv: str) -> None:
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    if not results:
        print("[WARN] No results to save.")
        return

    fieldnames = [
        "name",
        "issue",
        "type",
        "queue",
        "ml_priority",
        "recommended_priority_rule",
        "llm_priority",
        "confidence_score",
        "confidence_level",
        "same_queue_count",
        "num_incidents",
        "same_queue_ratio",
        "escalation",
        "retrieval_query",
    ]

    with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n[INFO] Saved evaluation results to: {output_csv}")


def main():
    results = []

    for test in TEST_CASES:
        try:
            result = evaluate_case(test)
            results.append(result)
            print_case_report(result)
        except Exception as e:
            print("\n" + "-" * 120)
            print(f"Case Failed: {test['name']}")
            print("-" * 120)
            print(str(e))

    print_summary(results)
    save_results_to_csv(results, OUTPUT_CSV)


if __name__ == "__main__":
    main()
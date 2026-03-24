from src.rag.retrieve import retrieve_similar_incidents


CHROMA_PATH = "artifacts/rag/chroma_db"
COLLECTION_NAME = "incident_memory"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


TEST_QUERIES = [
    {
        "name": "Billing Issue",
        "query": "Payment API timeout errors for enterprise customers",
        "queue": None,
        "type": None,
    },
    {
        "name": "Billing Issue (Filtered)",
        "query": "Payment API timeout errors",
        "queue": "BILLING AND PAYMENTS",
        "type": None,
    },
    {
        "name": "Login Issue",
        "query": "Users unable to login after password reset",
        "queue": None,
        "type": None,
    },
    {
        "name": "Database Failure",
        "query": "Database connection timeout errors in production",
        "queue": None,
        "type": None,
    },
    {
        "name": "Account Lock",
        "query": "User account locked after multiple failed login attempts",
        "queue": None,
        "type": None,
    },
    {
        "name": "API Latency",
        "query": "High latency in API responses after deployment",
        "queue": None,
        "type": None,
    },
]


def print_summary(results):
    """Print a short summary for quick evaluation."""
    if not results:
        print("No results returned.\n")
        return

    for r in results:
        print(f"#{r['rank']} | Queue: {r['queue']} | Priority: {r['priority']} | Distance: {r['distance']:.3f}")
        print(f"Issue: {r['issue_description'][:120]}...")
        print("-" * 80)
    print()


def run_tests():
    print("\n" + "=" * 120)
    print("RETRIEVAL TEST SUITE")
    print("=" * 120)

    for test in TEST_QUERIES:
        print("\n" + "#" * 120)
        print(f"TEST: {test['name']}")
        print("#" * 120)

        results = retrieve_similar_incidents(
            query=test["query"],
            chroma_path=CHROMA_PATH,
            collection_name=COLLECTION_NAME,
            model_name=MODEL_NAME,
            top_k=3,
            queue_filter=test["queue"],
            type_filter=test["type"],
        )

        print("\n--- QUICK SUMMARY ---")
        print_summary(results)


if __name__ == "__main__":
    run_tests()

# python -m tests.test_retrieval
from src.pipeline.predict_and_retrieve import run_pipeline


TEST_CASES = [
    {
        "name": "Billing Issue",
        "issue": "Payment API timeout errors for enterprise customers",
        "type": "INCIDENT",
        "queue": "BILLING AND PAYMENTS",
    },
    {
        "name": "Login Issue",
        "issue": "Users unable to login after password reset",
        "type": "INCIDENT",
        "queue": "CUSTOMER SERVICE",
    },
    {
        "name": "Database Failure",
        "issue": "Database connection timeout errors in production",
        "type": "INCIDENT",
        "queue": "TECHNICAL SUPPORT",
    },
    {
        "name": "Account Lock",
        "issue": "User account locked after multiple failed login attempts",
        "type": "INCIDENT",
        "queue": "CUSTOMER SERVICE",
    },
    {
        "name": "API Latency",
        "issue": "High latency in API responses after deployment",
        "type": "INCIDENT",
        "queue": "PRODUCT SUPPORT",
    },
]


def print_summary(result):
    print("\n--- SUMMARY ---")

    print(f"Predicted Priority: {result['predicted_priority']}")

    print("\nTop Retrieved Incidents:")
    for r in result["retrieved_incidents"]:
        print(
            f"#{r['rank']} | Queue: {r['queue']} | Priority: {r['priority']} | Distance: {r['distance']:.3f}"
        )
        print(f"Issue: {r['issue_description'][:100]}...")
        print("-" * 80)


def run_tests():
    print("\n" + "=" * 120)
    print("PREDICT + RETRIEVE TEST SUITE")
    print("=" * 120)

    for test in TEST_CASES:
        print("\n" + "#" * 120)
        print(f"TEST: {test['name']}")
        print("#" * 120)

        result = run_pipeline(
            issue_description=test["issue"],
            ticket_type=test["type"],
            queue=test["queue"],
            top_k=3,
        )

        print_summary(result)


if __name__ == "__main__":
    run_tests()

# python -m tests.test_predict_and_retrieve
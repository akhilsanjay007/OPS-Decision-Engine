from src.pipeline.predict_retrieve_generate import run_full_pipeline


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


def run_tests():
    print("\n" + "=" * 120)
    print("FULL PIPELINE TEST SUITE (ML + RAG + LLM)")
    print("=" * 120)

    for idx, test in enumerate(TEST_CASES, start=1):
        print("\n" + "#" * 120)
        print(f"TEST {idx}: {test['name']}")
        print("#" * 120)

        try:
            decision = run_full_pipeline(
                issue_description=test["issue"],
                ticket_type=test["type"],
                queue=test["queue"],
                top_k=3,
            )

            print("\n" + "-" * 120)
            print("TEST RESULT")
            print("-" * 120)
            print(decision)

        except Exception as e:
            print("\n[ERROR] Test failed:")
            print(str(e))


if __name__ == "__main__":
    run_tests()

# python -m tests.test_predict_retrieve_generate
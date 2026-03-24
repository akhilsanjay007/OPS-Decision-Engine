"""
Edge Case Testing Script for Priority Classification Model

Purpose
-------
This script manually tests the trained ML model on unusual, ambiguous,
short, long, and out-of-distribution inputs to see whether predictions
behave reasonably.

Why this matters
----------------
- Metrics like accuracy and Macro F1 show average performance
- Edge case tests show how the model behaves on tricky real-world inputs

Model used
----------
Stage 5 Linear SVM model (see MODEL_PATH / ``src.runtime_paths.get_model_path()``).
"""

import joblib
import pandas as pd

from src.runtime_paths import get_model_path


def load_model(model_path: str):
    """
    Load the trained pipeline from disk.
    """
    model = joblib.load(model_path)
    print("Model loaded successfully.")
    print("=" * 70)
    return model


def build_edge_case_inputs() -> pd.DataFrame:
    """
    Create a set of diverse edge-case inputs.

    Notes:
    - type and queue are set to UNKNOWN to simulate missing structured metadata
    - this stresses the text side of the model more heavily
    """
    test_cases = [
        # --------------------------------------------------
        # 1. Very short / vague inputs
        # --------------------------------------------------
        "not working",
        "help",
        "please assist",

        # --------------------------------------------------
        # 2. High urgency / critical severity
        # --------------------------------------------------
        "urgent system failure, production is down",
        "critical outage affecting all users",
        "immediate help needed, service unavailable for customers",
        "emergency issue, major system crash across teams",

        # --------------------------------------------------
        # 3. Payment / billing related
        # --------------------------------------------------
        "payment failed",
        "charged twice, need refund immediately",
        "invoice amount looks incorrect on my account",
        "billing issue, transaction completed but order not confirmed",

        # --------------------------------------------------
        # 4. Access / login / authentication
        # --------------------------------------------------
        "cannot login to account",
        "authentication error, access denied",
        "password reset link is not working",
        "two-factor authentication code not received",

        # --------------------------------------------------
        # 5. Ambiguous / unclear severity
        # --------------------------------------------------
        "system is slow sometimes",
        "minor issue with dashboard layout",
        "application behaves strangely from time to time",
        "seeing occasional delay when opening reports",

        # --------------------------------------------------
        # 6. Mixed signals / conflicting wording
        # --------------------------------------------------
        "urgent refund request but system still works fine",
        "critical issue but no users are affected currently",
        "high priority complaint, but functionality appears normal",
        "system says failed but users can still proceed normally",

        # --------------------------------------------------
        # 7. Long complex input
        # --------------------------------------------------
        """Dear support team, after the recent update, the system crashes
        intermittently when uploading files. This issue is affecting multiple
        users across departments and needs immediate attention.""",

        """Hello team, I am writing to report that several employees are unable
        to access shared resources after the weekend deployment. Some users see
        timeout errors, while others are being logged out automatically. This is
        slowing down work significantly.""",

        # --------------------------------------------------
        # 8. Out-of-distribution / unseen domain
        # --------------------------------------------------
        "AI model hallucination issue in production pipeline",
        "vector database retrieval quality dropped after embedding refresh",
        "LLM prompt orchestration issue causing unstable answers",

        # --------------------------------------------------
        # 9. Obvious LOW-priority / informational requests
        # --------------------------------------------------
        "feature request for dashboard export",
        "need more information about invoice details",
        "requesting documentation for API integration",
        "dashboard color looks slightly off on mobile",
        "question about product compatibility with smart home devices",

        # --------------------------------------------------
        # 10. Typos / messy text
        # --------------------------------------------------
        "logn problm cant acces acount",
        "paymnt faild need hlp asap",
        "systm crsh wen uplod file",

        # --------------------------------------------------
        # 11. Multiple issues in one ticket
        # --------------------------------------------------
        "payment failed and login also broken after update",
        "cannot access account and billing page shows wrong charges",
        "dashboard is slow, file upload crashes, and users are getting signed out",

        # --------------------------------------------------
        # 12. Support-style realistic moderate issues
        # --------------------------------------------------
        "printer connection keeps dropping on macbook",
        "vpn access issue for remote employee",
        "report generation feature not working as expected",
        "query regarding system integration capabilities",
    ]

    # Build DataFrame in the same structure the model expects
    df = pd.DataFrame(
        {
            "issue_description": test_cases,
            "type": ["UNKNOWN"] * len(test_cases),
            "queue": ["UNKNOWN"] * len(test_cases),
        }
    )

    return df


def run_predictions(model, test_df: pd.DataFrame) -> pd.DataFrame:
    """
    Run predictions on the edge-case inputs and return a results DataFrame.
    """
    predictions = model.predict(test_df)

    results_df = test_df.copy()
    results_df["predicted_priority"] = predictions
    return results_df


def print_results(results_df: pd.DataFrame) -> None:
    """
    Print edge-case predictions in a readable format.
    """
    print("\nEDGE CASE TEST RESULTS")
    print("=" * 70)

    for i, row in results_df.iterrows():
        print(f"\nTest Case #{i + 1}")
        print(f"Input Text:\n{row['issue_description']}")
        print(f"Predicted Priority: {row['predicted_priority']}")
        print("-" * 70)


def save_results(results_df: pd.DataFrame, output_path: str) -> None:
    """
    Save results to CSV for later inspection.
    """
    results_df.to_csv(output_path, index=False)
    print(f"\nSaved edge case results to: {output_path}")


def main():
    """
    Main edge-case testing flow.
    """
    model_path = str(get_model_path())
    output_path = "outputs/ml/stage5_svm/edge_case_predictions.csv"

    model = load_model(model_path)
    test_df = build_edge_case_inputs()
    results_df = run_predictions(model, test_df)
    print_results(results_df)
    save_results(results_df, output_path)

    print("\nHow to review results:")
    print("1. Check if urgent / critical cases are predicted as HIGH")
    print("2. Check if vague or cosmetic issues become LOW or MEDIUM")
    print("3. Check if the model over-predicts one class")
    print("4. Check if typo-heavy or out-of-domain cases behave reasonably")


if __name__ == "__main__":
    main()
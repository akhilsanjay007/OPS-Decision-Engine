from pathlib import Path
import json
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix,
)


def load_data(file_path: str) -> pd.DataFrame:
    """
    Load the processed ML dataset from CSV.

    Expected columns:
    - issue_description
    - priority
    """
    df = pd.read_csv(file_path)
    print(f"Loaded dataset shape: {df.shape}")
    print("Columns:", df.columns.tolist())
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Minimal cleaning for Stage 2.

    We keep only the baseline text + target columns:
    - issue_description
    - priority

    Then we:
    - drop missing rows
    - strip spaces
    - standardize labels
    - remove empty descriptions

    We are still keeping the pipeline simple and focused.
    """
    # Keep only the columns needed for this stage
    df = df[["issue_description", "priority"]].copy()

    print(f"\nShape after selecting columns: {df.shape}")

    # Drop rows where either text or target is missing
    df = df.dropna(subset=["issue_description", "priority"]).copy()
    print(f"Shape after dropna: {df.shape}")

    # Standardize the text and label columns
    df["issue_description"] = df["issue_description"].astype(str).str.strip()
    df["priority"] = df["priority"].astype(str).str.strip().str.upper()

    # Remove rows with empty issue descriptions
    df = df[df["issue_description"] != ""].copy()
    print(f"Shape after removing empty descriptions: {df.shape}")

    # Helpful sanity check
    print(f"Unique issue descriptions: {df['issue_description'].nunique()}")

    return df


def inspect_target(df: pd.DataFrame) -> None:
    """
    Show the class distribution of the target labels.

    This helps us understand whether the dataset is imbalanced.
    """
    print("\nPriority distribution (count):")
    print(df["priority"].value_counts())

    print("\nPriority distribution (percentage):")
    print((df["priority"].value_counts(normalize=True) * 100).round(2))


def split_data(df: pd.DataFrame):
    """
    Split the dataset into train and test sets.

    stratify=y keeps the class proportions similar
    in train and test sets.
    """
    X = df["issue_description"]
    y = df["priority"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    print(f"\nTrain size: {len(X_train)}")
    print(f"Test size: {len(X_test)}")

    return X_train, X_test, y_train, y_test


def build_pipeline() -> Pipeline:
    """
    Build the Stage 2 pipeline.

    Improvements over Stage 1:
    1. Use unigrams + bigrams
       - helps capture phrases like 'payment failed', 'account locked'
    2. Use min_df=2
       - ignores words/phrases that appear only once
    3. Increase max_features
       - allows a larger vocabulary
    4. Use class_weight='balanced'
       - helps the model pay more attention to smaller classes
    """
    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    stop_words="english",
                    ngram_range=(1, 2),   # use both single words and 2-word phrases
                    min_df=2,             # ignore tokens that appear only once
                    max_features=20000,   # allow a larger vocabulary than Stage 1
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=1000,
                    random_state=42,
                    class_weight="balanced",  # help minority classes
                ),
            ),
        ]
    )
    return pipeline


def evaluate_model(model: Pipeline, X_test, y_test, output_dir: Path) -> None:
    """
    Evaluate the trained model on the test set.

    Also save all evaluation outputs to the outputs folder.
    """
    # Predict labels for the test set
    y_pred = model.predict(X_test)

    # Compute evaluation metrics
    accuracy = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro")
    weighted_f1 = f1_score(y_test, y_pred, average="weighted")

    # Generate detailed reports
    report_text = classification_report(y_test, y_pred, zero_division=0)
    report_dict = classification_report(y_test, y_pred, zero_division=0, output_dict=True)

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)

    # Sorted label names for saving the confusion matrix nicely
    labels = sorted(y_test.unique())

    # Print results to terminal
    print("\nEvaluation Metrics")
    print("-" * 50)
    print(f"Accuracy    : {accuracy:.4f}")
    print(f"Macro F1    : {macro_f1:.4f}")
    print(f"Weighted F1 : {weighted_f1:.4f}")

    print("\nClassification Report")
    print("-" * 50)
    print(report_text)

    print("\nConfusion Matrix")
    print("-" * 50)
    print(cm)

    # Make sure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save summary metrics as JSON
    metrics = {
        "accuracy": round(float(accuracy), 4),
        "macro_f1": round(float(macro_f1), 4),
        "weighted_f1": round(float(weighted_f1), 4),
        "test_size": int(len(y_test)),
        "labels": labels,
    }

    with open(output_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # Save classification report as text
    with open(output_dir / "classification_report.txt", "w", encoding="utf-8") as f:
        f.write(report_text)

    # Save classification report as JSON
    with open(output_dir / "classification_report.json", "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2)

    # Save confusion matrix as CSV
    cm_df = pd.DataFrame(cm, index=labels, columns=labels)
    cm_df.to_csv(output_dir / "confusion_matrix.csv", index=True)

    # Save all test predictions
    predictions_df = pd.DataFrame(
        {
            "issue_description": X_test.reset_index(drop=True),
            "actual_priority": y_test.reset_index(drop=True),
            "predicted_priority": pd.Series(y_pred),
        }
    )

    # Mark whether each prediction was correct
    predictions_df["correct"] = (
        predictions_df["actual_priority"] == predictions_df["predicted_priority"]
    )

    predictions_df.to_csv(output_dir / "test_predictions.csv", index=False)

    # Save only misclassified examples for error analysis
    errors_df = predictions_df[~predictions_df["correct"]].copy()
    errors_df.to_csv(output_dir / "misclassified_samples.csv", index=False)

    print(f"\nSaved evaluation outputs to: {output_dir}")


def save_model(model: Pipeline, output_path: str) -> None:
    """
    Save the full trained pipeline to disk.

    We save the whole pipeline, not just the classifier,
    so later we can directly pass raw text into it.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, output_file)
    print(f"\nSaved model to: {output_file}")


def main():
    """
    Main training flow for Stage 2.
    """
    data_path = "data/processed/ml_priority_dataset.csv"
    model_path = "artifacts/ml/priority_stage2_pipeline.joblib"
    output_dir = Path("outputs/ml/stage2")

    # 1. Load dataset
    df = load_data(data_path)

    # 2. Clean dataset
    df = clean_data(df)

    # 3. Inspect label distribution
    inspect_target(df)

    # 4. Split into train and test sets
    X_train, X_test, y_train, y_test = split_data(df)

    # 5. Build Stage 2 pipeline
    model = build_pipeline()

    # 6. Train the model
    model.fit(X_train, y_train)
    print("\nStage 2 model training completed.")

    # 7. Evaluate model and save outputs
    evaluate_model(model, X_test, y_test, output_dir)

    # 8. Save trained model artifact
    save_model(model, model_path)


if __name__ == "__main__":
    main()
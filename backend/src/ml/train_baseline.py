from pathlib import Path
import json
import pandas as pd
import joblib
import numpy as np

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
    df = pd.read_csv(file_path)
    print(f"Loaded dataset shape: {df.shape}")
    print("Columns:", df.columns.tolist())
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df[["issue_description", "priority"]].copy()

    print(f"\nShape after selecting baseline columns: {df.shape}")

    df = df.dropna(subset=["issue_description", "priority"]).copy()
    print(f"Shape after dropna: {df.shape}")

    df["issue_description"] = df["issue_description"].astype(str).str.strip()
    df["priority"] = df["priority"].astype(str).str.strip().str.upper()

    df = df[df["issue_description"] != ""].copy()
    print(f"Shape after removing empty descriptions: {df.shape}")

    print(f"Unique issue descriptions: {df['issue_description'].nunique()}")
    return df


def inspect_target(df: pd.DataFrame) -> None:
    print("\nPriority distribution (count):")
    print(df["priority"].value_counts())

    print("\nPriority distribution (percentage):")
    print((df["priority"].value_counts(normalize=True) * 100).round(2))


def split_data(df: pd.DataFrame):
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
    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    stop_words="english",
                    ngram_range=(1, 1),
                    max_features=10000,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=1000,
                    random_state=42,
                ),
            ),
        ]
    )
    return pipeline


def evaluate_model(model: Pipeline, X_test, y_test, output_dir: Path) -> None:
    y_pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro")
    weighted_f1 = f1_score(y_test, y_pred, average="weighted")

    report_text = classification_report(y_test, y_pred, zero_division=0)
    report_dict = classification_report(y_test, y_pred, zero_division=0, output_dict=True)
    cm = confusion_matrix(y_test, y_pred)
    labels = sorted(y_test.unique())

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

    output_dir.mkdir(parents=True, exist_ok=True)

    metrics = {
        "accuracy": round(float(accuracy), 4),
        "macro_f1": round(float(macro_f1), 4),
        "weighted_f1": round(float(weighted_f1), 4),
        "test_size": int(len(y_test)),
        "labels": labels,
    }

    with open(output_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    with open(output_dir / "classification_report.txt", "w", encoding="utf-8") as f:
        f.write(report_text)

    with open(output_dir / "classification_report.json", "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2)

    cm_df = pd.DataFrame(cm, index=labels, columns=labels)
    cm_df.to_csv(output_dir / "confusion_matrix.csv", index=True)

    predictions_df = pd.DataFrame(
        {
            "issue_description": X_test.reset_index(drop=True),
            "actual_priority": y_test.reset_index(drop=True),
            "predicted_priority": pd.Series(y_pred),
        }
    )
    predictions_df["correct"] = (
        predictions_df["actual_priority"] == predictions_df["predicted_priority"]
    )
    predictions_df.to_csv(output_dir / "test_predictions.csv", index=False)

    errors_df = predictions_df[~predictions_df["correct"]].copy()
    errors_df.to_csv(output_dir / "misclassified_samples.csv", index=False)

    print(f"\nSaved evaluation outputs to: {output_dir}")


def save_model(model: Pipeline, output_path: str) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, output_file)
    print(f"\nSaved model to: {output_file}")


def main():
    data_path = "data/processed/ml_priority_dataset.csv"
    model_path = "artifacts/ml/priority_baseline_pipeline.joblib"
    output_dir = Path("outputs/ml/baseline")

    df = load_data(data_path)
    df = clean_data(df)
    inspect_target(df)

    X_train, X_test, y_train, y_test = split_data(df)

    model = build_pipeline()
    model.fit(X_train, y_train)
    print("\nModel training completed.")

    evaluate_model(model, X_test, y_test, output_dir)
    save_model(model, model_path)


if __name__ == "__main__":
    main()
from pathlib import Path
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
    Minimal cleaning for Stage 1 baseline.
    We intentionally keep this simple:
    - keep only issue_description and priority
    - drop missing rows
    - strip spaces
    - standardize priority labels
    - remove empty descriptions

    We do NOT drop duplicates yet because we want to inspect
    how the Kaggle dataset behaves first.
    """
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
    """
    Print class distribution for the target.
    """
    print("\nPriority distribution (count):")
    print(df["priority"].value_counts())

    print("\nPriority distribution (percentage):")
    print((df["priority"].value_counts(normalize=True) * 100).round(2))


def split_data(df: pd.DataFrame):
    """
    Split into train and test sets using stratification.
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
    Stage 1 baseline:
    TF-IDF + Logistic Regression
    """
    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    stop_words="english",
                    ngram_range=(1, 1),   # unigrams only for baseline
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


def evaluate_model(model: Pipeline, X_test, y_test) -> None:
    """
    Evaluate on the test set.
    """
    y_pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro")
    weighted_f1 = f1_score(y_test, y_pred, average="weighted")

    print("\nEvaluation Metrics")
    print("-" * 50)
    print(f"Accuracy    : {accuracy:.4f}")
    print(f"Macro F1    : {macro_f1:.4f}")
    print(f"Weighted F1 : {weighted_f1:.4f}")

    print("\nClassification Report")
    print("-" * 50)
    print(classification_report(y_test, y_pred, zero_division=0))

    print("\nConfusion Matrix")
    print("-" * 50)
    print(confusion_matrix(y_test, y_pred))


def save_model(model: Pipeline, output_path: str) -> None:
    """
    Save the full trained pipeline.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, output_file)
    print(f"\nSaved model to: {output_file}")


def main():
    """
    Main Stage 1 training flow.
    """
    data_path = "data/processed/ml_priority_dataset.csv"
    model_path = "artifacts/ml/priority_baseline_pipeline.joblib"

    # 1. Load dataset
    df = load_data(data_path)

    # 2. Clean dataset
    df = clean_data(df)

    # 3. Inspect label distribution
    inspect_target(df)

    # 4. Split data
    X_train, X_test, y_train, y_test = split_data(df)

    # 5. Build baseline pipeline
    model = build_pipeline()

    # 6. Train
    model.fit(X_train, y_train)
    print("\nModel training completed.")

    # 7. Evaluate
    evaluate_model(model, X_test, y_test)

    # 8. Save pipeline
    save_model(model, model_path)


if __name__ == "__main__":
    main()
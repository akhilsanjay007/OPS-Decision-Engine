from pathlib import Path
import json
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix,
)


def load_data(file_path: str) -> pd.DataFrame:
    """
    Load the Stage 4 processed dataset.

    Expected columns:
    - issue_description
    - type
    - queue
    - text_length
    - word_count
    - has_error_keyword
    - has_failure_keyword
    - has_urgent_keyword
    - has_access_keyword
    - has_payment_keyword
    - priority
    """
    df = pd.read_csv(file_path)
    print(f"Loaded dataset shape: {df.shape}")
    print("Columns:", df.columns.tolist())
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Basic cleaning for Stage 4.

    We keep:
    - issue_description -> text feature
    - type, queue -> categorical features
    - engineered numeric/binary features
    - priority -> target label
    """
    required_columns = [
        "issue_description",
        "type",
        "queue",
        "text_length",
        "word_count",
        "has_error_keyword",
        "has_failure_keyword",
        "has_urgent_keyword",
        "has_access_keyword",
        "has_payment_keyword",
        "priority",
    ]

    # Keep only the required Stage 4 columns
    df = df[required_columns].copy()

    print(f"\nShape after selecting Stage 4 columns: {df.shape}")

    # Drop rows where text or target is missing
    df = df.dropna(subset=["issue_description", "priority"]).copy()
    print(f"Shape after dropna on text/target: {df.shape}")

    # Standardize text / category / label columns
    df["issue_description"] = df["issue_description"].astype(str).str.strip()
    df["type"] = df["type"].fillna("UNKNOWN").astype(str).str.strip().str.upper()
    df["queue"] = df["queue"].fillna("UNKNOWN").astype(str).str.strip().str.upper()
    df["priority"] = df["priority"].astype(str).str.strip().str.upper()

    # Remove rows where issue_description is empty
    df = df[df["issue_description"] != ""].copy()
    print(f"Shape after removing empty descriptions: {df.shape}")

    # Make sure engineered features are numeric
    numeric_cols = [
        "text_length",
        "word_count",
        "has_error_keyword",
        "has_failure_keyword",
        "has_urgent_keyword",
        "has_access_keyword",
        "has_payment_keyword",
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows that became invalid after numeric conversion
    df = df.dropna(subset=numeric_cols).copy()

    # Sanity checks
    print(f"Unique issue descriptions: {df['issue_description'].nunique()}")
    print(f"Unique types: {df['type'].nunique()}")
    print(f"Unique queues: {df['queue'].nunique()}")

    return df


def inspect_target(df: pd.DataFrame) -> None:
    """
    Show class distribution of the target label.
    """
    print("\nPriority distribution (count):")
    print(df["priority"].value_counts())

    print("\nPriority distribution (percentage):")
    print((df["priority"].value_counts(normalize=True) * 100).round(2))


def split_data(df: pd.DataFrame):
    """
    Split data into train and test sets.

    We stratify by priority so class proportions remain similar
    in both train and test splits.
    """
    feature_cols = [
        "issue_description",
        "type",
        "queue",
        "text_length",
        "word_count",
        "has_error_keyword",
        "has_failure_keyword",
        "has_urgent_keyword",
        "has_access_keyword",
        "has_payment_keyword",
    ]

    X = df[feature_cols]
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
    Build the Stage 4 pipeline.

    This pipeline combines:
    1. Text features:
       - issue_description -> TF-IDF
    2. Categorical features:
       - type, queue -> OneHotEncoder
    3. Numeric/binary engineered features:
       - text_length
       - word_count
       - keyword flags
       -> StandardScaler

    Then everything is fed into Logistic Regression.
    """
    text_feature = "issue_description"
    categorical_features = ["type", "queue"]
    numeric_features = [
        "text_length",
        "word_count",
        "has_error_keyword",
        "has_failure_keyword",
        "has_urgent_keyword",
        "has_access_keyword",
        "has_payment_keyword",
    ]

    # Preprocess different column types differently
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "text",
                TfidfVectorizer(
                    lowercase=True,
                    stop_words="english",
                    ngram_range=(1, 2),   # use unigrams + bigrams
                    min_df=2,             # ignore terms appearing only once
                    max_features=20000,   # keep vocabulary manageable
                ),
                text_feature,
            ),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_features,
            ),
            (
                "num",
                StandardScaler(),
                numeric_features,
            ),
        ]
    )

    # Full pipeline: preprocessing + classifier
    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "clf",
                LogisticRegression(
                    max_iter=1000,
                    random_state=42,
                    class_weight="balanced",  # helps with smaller classes like LOW
                ),
            ),
        ]
    )

    return pipeline


def evaluate_model(model: Pipeline, X_test, y_test, output_dir: Path) -> None:
    """
    Evaluate the trained model on the test set
    and save analysis outputs to the outputs folder.
    """
    # Predict on the test set
    y_pred = model.predict(X_test)

    # Compute core metrics
    accuracy = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro")
    weighted_f1 = f1_score(y_test, y_pred, average="weighted")

    # Detailed text + JSON reports
    report_text = classification_report(y_test, y_pred, zero_division=0)
    report_dict = classification_report(y_test, y_pred, zero_division=0, output_dict=True)

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    labels = sorted(y_test.unique())

    # Print to terminal
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

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save summary metrics
    metrics = {
        "accuracy": round(float(accuracy), 4),
        "macro_f1": round(float(macro_f1), 4),
        "weighted_f1": round(float(weighted_f1), 4),
        "test_size": int(len(y_test)),
        "labels": labels,
    }

    with open(output_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # Save classification reports
    with open(output_dir / "classification_report.txt", "w", encoding="utf-8") as f:
        f.write(report_text)

    with open(output_dir / "classification_report.json", "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2)

    # Save confusion matrix as CSV
    cm_df = pd.DataFrame(cm, index=labels, columns=labels)
    cm_df.to_csv(output_dir / "confusion_matrix.csv", index=True)

    # Save all predictions
    predictions_df = X_test.reset_index(drop=True).copy()
    predictions_df["actual_priority"] = y_test.reset_index(drop=True)
    predictions_df["predicted_priority"] = pd.Series(y_pred)
    predictions_df["correct"] = (
        predictions_df["actual_priority"] == predictions_df["predicted_priority"]
    )

    predictions_df.to_csv(output_dir / "test_predictions.csv", index=False)

    # Save only wrong predictions for error analysis
    errors_df = predictions_df[~predictions_df["correct"]].copy()
    errors_df.to_csv(output_dir / "misclassified_samples.csv", index=False)

    print(f"\nSaved evaluation outputs to: {output_dir}")


def save_model(model: Pipeline, output_path: str) -> None:
    """
    Save the full trained Stage 4 pipeline to disk.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, output_file)
    print(f"\nSaved model to: {output_file}")


def main():
    """
    Main Stage 4 training flow.
    """
    data_path = "data/processed/ml_priority_dataset_stage4.csv"
    model_path = "artifacts/ml/priority_stage4_pipeline.joblib"
    output_dir = Path("outputs/ml/stage4")

    # 1. Load processed dataset
    df = load_data(data_path)

    # 2. Clean and validate dataset
    df = clean_data(df)

    # 3. Inspect class distribution
    inspect_target(df)

    # 4. Split into train/test
    X_train, X_test, y_train, y_test = split_data(df)

    # 5. Build Stage 4 pipeline
    model = build_pipeline()

    # 6. Train model
    model.fit(X_train, y_train)
    print("\nStage 4 model training completed.")

    # 7. Evaluate and save outputs
    evaluate_model(model, X_test, y_test, output_dir)

    # 8. Save model artifact
    save_model(model, model_path)


if __name__ == "__main__":
    main()
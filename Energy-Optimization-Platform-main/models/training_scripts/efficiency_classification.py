"""
Model 2: Efficiency Classification using XGBoost
Classifies machine efficiency into efficient, moderate_waste, severe_waste
"""

import pandas as pd
import numpy as np
import joblib
import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
from sklearn.utils.class_weight import compute_class_weight
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("model_2_efficiency_training.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def load_and_prepare_data(filepath):
    """Load efficiency training data and prepare features"""
    logger.info(f"Loading data from {filepath}")
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df):,} records with {len(df.columns)} columns")

    # Define features
    feature_columns = [
        "power_kw",
        "load_percent",
        "output_units",
        "temperature_c",
        "vibration_mm_s",
        "ambient_temperature_c",
        "humidity_percent",
        "utilization_percent",
        "energy_per_unit",
        "idle_energy_ratio",
        "power_deviation_percent",
        "hour_of_day",
        "day_of_week",
        "weekend_flag",
    ]

    # Check available features
    available_features = [col for col in feature_columns if col in df.columns]
    logger.info(f"Using {len(available_features)} features: {available_features}")

    # Prepare feature matrix
    X = df[available_features].copy()

    # Handle missing values
    X = X.fillna(X.median())

    # Target variable
    y = df["efficiency_class"]
    logger.info(f"Target classes: {y.unique()}")
    logger.info(f"Class distribution:\n{y.value_counts()}")

    return X, y, available_features


def encode_target(y):
    """Encode target labels"""
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    # Map classes to numbers
    class_mapping = dict(
        zip(label_encoder.classes_, label_encoder.transform(label_encoder.classes_))
    )
    logger.info(f"Class mapping: {class_mapping}")

    return y_encoded, label_encoder


def train_xgboost_classifier(X_train, y_train, X_val, y_val):
    """Train XGBoost classifier with optimized parameters"""
    logger.info("Training XGBoost Classifier...")

    # Calculate class weights for imbalance handling
    classes = np.unique(y_train)
    class_weights = compute_class_weight("balanced", classes=classes, y=y_train)
    weight_dict = dict(zip(classes, class_weights))
    logger.info(f"Class weights: {weight_dict}")

    # Calculate sample weights
    sample_weights = np.array([weight_dict[y] for y in y_train])

    # Initialize model
    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric="mlogloss",
        early_stopping_rounds=50,
        use_label_encoder=False,
    )

    # Train with early stopping
    eval_set = [(X_train, y_train), (X_val, y_val)]
    model.fit(
        X_train, y_train, sample_weight=sample_weights, eval_set=eval_set, verbose=False
    )

    logger.info("XGBoost training completed")
    logger.info(f"Best iteration: {model.best_iteration}")
    logger.info(f"Best score: {model.best_score}")

    return model


def evaluate_model(model, X_test, y_test, label_encoder):
    """Evaluate classification performance"""
    logger.info("Evaluating model performance...")

    # Predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)

    # Metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average="weighted")
    recall = recall_score(y_test, y_pred, average="weighted")
    f1 = f1_score(y_test, y_pred, average="weighted")

    logger.info(f"Accuracy: {accuracy:.4f}")
    logger.info(f"Weighted Precision: {precision:.4f}")
    logger.info(f"Weighted Recall: {recall:.4f}")
    logger.info(f"Weighted F1-Score: {f1:.4f}")

    # Classification Report
    report = classification_report(y_test, y_pred, target_names=label_encoder.classes_)
    logger.info(f"Classification Report:\n{report}")

    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    logger.info(f"Confusion Matrix:\n{cm}")

    return (
        y_pred,
        y_pred_proba,
        {"accuracy": accuracy, "precision": precision, "recall": recall, "f1": f1},
    )


def plot_results(model, X_test, y_test, y_pred, feature_names, label_encoder):
    """Generate comprehensive visualizations"""
    logger.info("Generating visualizations...")

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))

    # 1. Confusion Matrix
    ax1 = axes[0, 0]
    cm = confusion_matrix(y_test, y_pred)
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        ax=ax1,
        cmap="Blues",
        xticklabels=label_encoder.classes_,
        yticklabels=label_encoder.classes_,
    )
    ax1.set_title("Confusion Matrix")
    ax1.set_xlabel("Predicted")
    ax1.set_ylabel("Actual")

    # 2. Feature Importance
    ax2 = axes[0, 1]
    importance = pd.DataFrame(
        {"feature": feature_names, "importance": model.feature_importances_}
    ).sort_values("importance", ascending=True)

    importance.tail(10).plot(
        kind="barh", x="feature", y="importance", ax=ax2, color="skyblue"
    )
    ax2.set_title("Top 10 Feature Importances")
    ax2.set_xlabel("Importance Score")

    # 3. Class Distribution
    ax3 = axes[0, 2]
    class_counts = (
        pd.Series(y_test).map(lambda x: label_encoder.classes_[x]).value_counts()
    )
    ax3.bar(class_counts.index, class_counts.values, color=["green", "orange", "red"])
    ax3.set_title("Class Distribution in Test Set")
    ax3.set_xlabel("Efficiency Class")
    ax3.set_ylabel("Count")
    ax3.tick_params(axis="x", rotation=45)

    # 4. Prediction Probabilities
    ax4 = axes[1, 0]
    y_pred_proba = model.predict_proba(X_test)
    for i, class_name in enumerate(label_encoder.classes_):
        # Get probabilities for this class where actual class = i
        mask = y_test == i
        if mask.sum() > 0:
            ax4.hist(y_pred_proba[mask][:, i], bins=30, alpha=0.5, label=class_name)
    ax4.set_title("Prediction Probabilities by Class")
    ax4.set_xlabel("Probability")
    ax4.set_ylabel("Frequency")
    ax4.legend()

    # 5. Error Analysis - FIXED: Use direct array indexing
    ax5 = axes[1, 1]
    errors = y_pred != y_test
    if errors.sum() > 0:
        error_types = []
        for i in range(len(y_test)):
            if errors[i]:  # FIXED: removed .iloc
                error_types.append(
                    f"{label_encoder.classes_[y_test[i]]}→{label_encoder.classes_[y_pred[i]]}"
                )
        error_counts = pd.Series(error_types).value_counts()
        ax5.bar(range(len(error_counts)), error_counts.values)
        ax5.set_xticks(range(len(error_counts)))
        ax5.set_xticklabels(error_counts.index, rotation=45, ha="right")
        ax5.set_title(f"Error Types (Total: {errors.sum()})")
        ax5.set_ylabel("Count")
    else:
        ax5.text(
            0.5,
            0.5,
            "✨ No Errors! Perfect Classification ✨",
            ha="center",
            va="center",
            transform=ax5.transAxes,
            fontsize=14,
        )
        ax5.set_title("Error Analysis - Perfect Model!")

    # 6. Confidence Distribution
    ax6 = axes[1, 2]
    max_probs = y_pred_proba.max(axis=1)
    ax6.hist(max_probs, bins=50, color="green", alpha=0.7, edgecolor="black")
    ax6.axvline(x=0.9, color="red", linestyle="--", label="High Confidence Threshold")
    ax6.set_title("Model Confidence Distribution")
    ax6.set_xlabel("Maximum Prediction Probability")
    ax6.set_ylabel("Frequency")
    ax6.legend()

    plt.tight_layout()
    plt.savefig("model_2_efficiency_results.png", dpi=150, bbox_inches="tight")
    plt.show()
    logger.info("Visualizations saved to 'model_2_efficiency_results.png'")


def save_model(model, label_encoder, feature_names):
    """Save trained model and artifacts"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save model
    model_path = "models/model_efficiency.pkl"
    joblib.dump(model, model_path)
    logger.info(f"Model saved to {model_path}")

    # Save label encoder
    encoder_path = "models/label_encoder_efficiency.pkl"
    joblib.dump(label_encoder, encoder_path)
    logger.info(f"Label encoder saved to {encoder_path}")

    # Save feature names
    features_path = "models/features_efficiency.pkl"
    joblib.dump(feature_names, features_path)
    logger.info(f"Feature names saved to {features_path}")

    # Backups
    backup_model = f"models/model_efficiency_{timestamp}.pkl"
    backup_encoder = f"models/label_encoder_efficiency_{timestamp}.pkl"
    joblib.dump(model, backup_model)
    joblib.dump(label_encoder, backup_encoder)
    logger.info(f"Backups saved: {backup_model}, {backup_encoder}")


def main():
    """Main training pipeline"""
    logger.info("=" * 60)
    logger.info("MODEL 2: Efficiency Classification Training Pipeline")
    logger.info("=" * 60)

    # Create models directory
    import os

    os.makedirs("models", exist_ok=True)

    # Load data
    X, y, feature_names = load_and_prepare_data(
        "data/synthetic/processed/training_dataset_efficiency.csv"
    )

    # Encode target
    y_encoded, label_encoder = encode_target(y)

    # Split data (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )
    logger.info(f"Training set: {len(X_train):,} samples")
    logger.info(f"Test set: {len(X_test):,} samples")

    # Train model
    model = train_xgboost_classifier(X_train, y_train, X_test, y_test)

    # Evaluate
    y_pred, y_pred_proba, metrics = evaluate_model(model, X_test, y_test, label_encoder)

    # Visualize
    plot_results(model, X_test, y_test, y_pred, feature_names, label_encoder)

    # Save model
    save_model(model, label_encoder, feature_names)

    logger.info("=" * 60)
    logger.info("Model 2 Training Completed Successfully!")
    logger.info(f"Final Accuracy: {metrics['accuracy']:.4f}")
    logger.info(f"Final F1-Score: {metrics['f1']:.4f}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

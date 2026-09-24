"""
Model 1: Anomaly Detection using Isolation Forest
Detects abnormal energy consumption patterns in industrial equipment
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
)
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
        logging.FileHandler("model_1_anomaly_training.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def load_and_prepare_data(filepath):
    """Load telemetry data and prepare features for anomaly detection"""
    logger.info(f"Loading data from {filepath}")
    df = pd.read_csv(filepath)
    logger.info(
        f"Loaded {len(df):,} records with {len(df.columns)} columns and rows {len(df.rows)}"
    )

    # Define features for anomaly detection
    feature_columns = [
        "power_kw",
        "current_a",
        "voltage_v",
        "load_percent",
        "temperature_c",
        "vibration_mm_s",
        "power_factor",
        "energy_per_unit",
        "utilization_percent",
        "power_deviation_percent",
        "ambient_temperature_c",
        "humidity_percent",
        "idle_energy_ratio",
    ]

    # Check if all features exist
    available_features = [col for col in feature_columns if col in df.columns]
    missing_features = set(feature_columns) - set(available_features)
    if missing_features:
        logger.warning(f"Missing features: {missing_features}")

    logger.info(f"Using {len(available_features)} features: {available_features}")

    # Prepare feature matrix
    X = df[available_features].copy()

    # Handle infinite values and NaNs
    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.fillna(X.median())

    # Log statistics
    logger.info(f"Feature matrix shape: {X.shape}")
    logger.info(f"Feature statistics:\n{X.describe()}")

    return X, df["anomaly_flag"] if "anomaly_flag" in df.columns else None


def train_isolation_forest(X, contamination=0.02):
    """Train Isolation Forest model"""
    logger.info("Training Isolation Forest model...")

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    logger.info("Features scaled using StandardScaler")

    # Train Isolation Forest
    iso_forest = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        max_samples="auto",
        random_state=42,
        verbose=0,
    )

    iso_forest.fit(X_scaled)
    logger.info("Isolation Forest training completed")

    return iso_forest, scaler


def evaluate_model(model, scaler, X, y_true):
    """Evaluate anomaly detection performance"""
    logger.info("Evaluating model performance...")

    # Scale features
    X_scaled = scaler.transform(X)

    # Predict anomalies (-1 = anomaly, 1 = normal)
    predictions = model.predict(X_scaled)

    # Convert to binary (1 = anomaly, 0 = normal)
    y_pred = (predictions == -1).astype(int)

    # Calculate metrics
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    logger.info(f"Precision: {precision:.4f}")
    logger.info(f"Recall: {recall:.4f}")
    logger.info(f"F1-Score: {f1:.4f}")

    # Confusion Matrix
    cm = confusion_matrix(y_true, y_pred)
    logger.info(f"Confusion Matrix:\n{cm}")

    # Classification Report
    report = classification_report(y_true, y_pred, target_names=["Normal", "Anomaly"])
    logger.info(f"Classification Report:\n{report}")

    return y_pred, {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "confusion_matrix": cm,
    }


def plot_results(df, y_true, y_pred, feature_names):
    """Generate visualization plots"""
    logger.info("Generating visualizations...")

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))

    # 1. Anomaly Distribution
    ax1 = axes[0, 0]
    anomaly_counts = pd.Series(y_pred).value_counts()
    ax1.bar(["Normal", "Anomaly"], anomaly_counts.values, color=["green", "red"])
    ax1.set_title("Detected Anomalies Distribution")
    ax1.set_ylabel("Count")

    # 2. Confusion Matrix
    ax2 = axes[0, 1]
    cm = confusion_matrix(y_true, y_pred)
    sns.heatmap(cm, annot=True, fmt="d", ax=ax2, cmap="Blues")
    ax2.set_title("Confusion Matrix")
    ax2.set_xlabel("Predicted")
    ax2.set_ylabel("Actual")

    # 3. Feature Importance (using feature variance as proxy)
    ax3 = axes[0, 2]
    feature_variance = df[feature_names].var().sort_values(ascending=True)
    feature_variance.tail(10).plot(kind="barh", ax=ax3, color="skyblue")
    ax3.set_title("Top 10 Features by Variance")
    ax3.set_xlabel("Variance")

    # 4. Power Distribution by Anomaly Status
    ax4 = axes[1, 0]
    df_sample = df.copy()
    df_sample["predicted_anomaly"] = y_pred
    normal_power = df_sample[df_sample["predicted_anomaly"] == 0]["power_kw"].sample(
        min(10000, len(df_sample))
    )
    anomaly_power = df_sample[df_sample["predicted_anomaly"] == 1]["power_kw"].sample(
        min(10000, len(df_sample))
    )
    ax4.hist(
        [normal_power, anomaly_power],
        bins=50,
        label=["Normal", "Anomaly"],
        alpha=0.7,
        color=["green", "red"],
    )
    ax4.set_title("Power Distribution by Anomaly Status")
    ax4.set_xlabel("Power (kW)")
    ax4.set_ylabel("Frequency")
    ax4.legend()

    # 5. Temperature vs Vibration colored by anomaly
    ax5 = axes[1, 1]
    scatter = ax5.scatter(
        df_sample["temperature_c"].sample(5000),
        df_sample["vibration_mm_s"].sample(5000),
        c=df_sample["predicted_anomaly"].sample(5000),
        cmap="RdYlGn",
        alpha=0.6,
    )
    ax5.set_title("Temperature vs Vibration (Anomaly Highlighted)")
    ax5.set_xlabel("Temperature (°C)")
    ax5.set_ylabel("Vibration (mm/s)")
    plt.colorbar(scatter, ax=ax5)

    # 6. Anomaly Detection Rate by Hour
    ax6 = axes[1, 2]
    if "hour_of_day" in df.columns:
        hourly_anomaly_rate = df.groupby("hour_of_day")["anomaly_flag"].mean()
        ax6.plot(
            hourly_anomaly_rate.index,
            hourly_anomaly_rate.values,
            marker="o",
            color="purple",
        )
        ax6.set_title("Anomaly Rate by Hour of Day")
        ax6.set_xlabel("Hour")
        ax6.set_ylabel("Anomaly Rate")
        ax6.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("model_1_anomaly_results.png", dpi=150, bbox_inches="tight")
    plt.show()
    logger.info("Visualizations saved to 'model_1_anomaly_results.png'")


def save_model(model, scaler):
    """Save trained model and scaler"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save model
    model_path = "models/model_anomaly.pkl"
    joblib.dump(model, model_path)
    logger.info(f"Model saved to {model_path}")

    # Save scaler
    scaler_path = "models/scaler_anomaly.pkl"
    joblib.dump(scaler, scaler_path)
    logger.info(f"Scaler saved to {scaler_path}")

    # Save backup with timestamp
    backup_model = f"models/model_anomaly_{timestamp}.pkl"
    backup_scaler = f"models/scaler_anomaly_{timestamp}.pkl"
    joblib.dump(model, backup_model)
    joblib.dump(scaler, backup_scaler)
    logger.info(f"Backups saved: {backup_model}, {backup_scaler}")


def main():
    """Main training pipeline"""
    logger.info("=" * 60)
    logger.info("MODEL 1: Anomaly Detection Training Pipeline")
    logger.info("=" * 60)

    # Create models directory
    import os

    os.makedirs("models", exist_ok=True)

    # Load data
    X, y_true = load_and_prepare_data("data/synthetic/raw/telemetry_machine_level.csv")

    # Split for validation (80% train, 20% validation)
    X_train, X_val, y_train, y_val = train_test_split(
        X, y_true, test_size=0.2, random_state=42, stratify=y_true
    )
    logger.info(f"Training set: {len(X_train):,} samples")
    logger.info(f"Validation set: {len(X_val):,} samples")
    logger.info(f"Anomaly rate in training: {y_train.mean() * 100:.2f}%")

    # Train model
    model, scaler = train_isolation_forest(X_train, contamination=y_train.mean())

    # Evaluate
    y_pred, metrics = evaluate_model(model, scaler, X_val, y_val)

    # Visualize
    plot_results(X_val, y_val, y_pred, X.columns.tolist())

    # Save model
    save_model(model, scaler)

    logger.info("=" * 60)
    logger.info("Model 1 Training Completed Successfully!")
    logger.info(f"Final F1-Score: {metrics['f1']:.4f}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

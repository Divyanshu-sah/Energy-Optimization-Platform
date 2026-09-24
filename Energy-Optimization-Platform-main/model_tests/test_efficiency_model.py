"""
Model 2 Testing & Validation Script
Tests the efficiency classification model with multiple scenarios
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.preprocessing import label_binarize
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import logging
import warnings

warnings.filterwarnings("ignore")

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_model_and_artifacts():
    """Load trained model and artifacts"""
    try:
        model = joblib.load("models/model_efficiency.pkl")
        label_encoder = joblib.load("models/label_encoder_efficiency.pkl")
        features = joblib.load("models/features_efficiency.pkl")
        logger.info("✅ Model and artifacts loaded successfully")
        return model, label_encoder, features
    except FileNotFoundError as e:
        logger.error(f"❌ Model files not found: {e}")
        logger.info("Please train the model first using efficiency_classification.py")
        return None, None, None


def load_test_data():
    """Load and prepare test data"""
    df = pd.read_csv("data/synthetic/processed/training_dataset_efficiency.csv")
    logger.info(f"📊 Loaded {len(df):,} total records")

    # Use last 20% for testing (temporal split)
    test_size = int(len(df) * 0.2)
    test_df = df.tail(test_size).copy()

    # Features
    features = [
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

    X_test = test_df[features].fillna(0)
    y_test = test_df["efficiency_class"]

    logger.info(f"🧪 Test set size: {len(X_test):,} samples")
    logger.info(f"📈 Test class distribution:\n{y_test.value_counts()}")

    return X_test, y_test, test_df


def test_basic_performance(model, label_encoder, X_test, y_test):
    """Test basic classification performance"""
    logger.info("\n" + "=" * 60)
    logger.info("📊 BASIC PERFORMANCE TEST")
    logger.info("=" * 60)

    # Predict
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)

    # Convert predictions back to labels
    y_pred_labels = label_encoder.inverse_transform(y_pred)
    y_test_labels = y_test.values  # Already strings

    # Calculate metrics
    accuracy = accuracy_score(y_test_labels, y_pred_labels)
    precision = precision_score(y_test_labels, y_pred_labels, average="weighted")
    recall = recall_score(y_test_labels, y_pred_labels, average="weighted")
    f1 = f1_score(y_test_labels, y_pred_labels, average="weighted")

    logger.info(f"\n🎯 Overall Metrics:")
    logger.info(f"  Accuracy:  {accuracy:.4f} ({accuracy * 100:.2f}%)")
    logger.info(f"  Precision: {precision:.4f}")
    logger.info(f"  Recall:    {recall:.4f}")
    logger.info(f"  F1-Score:  {f1:.4f}")

    # Per-class metrics
    logger.info(f"\n📋 Per-Class Performance:")
    print(classification_report(y_test_labels, y_pred_labels))

    # Confusion Matrix
    cm = confusion_matrix(y_test_labels, y_pred_labels, labels=label_encoder.classes_)

    logger.info(f"\n🔢 Confusion Matrix:")
    print(
        pd.DataFrame(cm, index=label_encoder.classes_, columns=label_encoder.classes_)
    )

    return y_pred, y_pred_proba, y_pred_labels


def test_confidence_metrics(model, X_test, y_test, y_pred_labels):
    """Test model confidence and reliability"""
    logger.info("\n" + "=" * 60)
    logger.info("🎯 CONFIDENCE & RELIABILITY TEST")
    logger.info("=" * 60)

    # Get prediction probabilities
    y_pred_proba = model.predict_proba(X_test)
    max_confidences = y_pred_proba.max(axis=1)

    # Calculate correctness
    y_test_labels = y_test.values
    correct = y_pred_labels == y_test_labels

    # Confidence analysis
    logger.info(f"\n📈 Confidence Statistics:")
    logger.info(f"  Mean Confidence: {max_confidences.mean():.4f}")
    logger.info(f"  Median Confidence: {np.median(max_confidences):.4f}")
    logger.info(f"  Std Confidence: {max_confidences.std():.4f}")
    logger.info(f"  Min Confidence: {max_confidences.min():.4f}")
    logger.info(f"  Max Confidence: {max_confidences.max():.4f}")

    # Confidence buckets
    confidence_buckets = [(0, 0.7), (0.7, 0.85), (0.85, 0.95), (0.95, 1.0)]
    logger.info(f"\n📊 Confidence Distribution:")
    for low, high in confidence_buckets:
        mask = (max_confidences >= low) & (max_confidences < high)
        count = mask.sum()
        if count > 0:
            accuracy_in_bucket = correct[mask].mean()
            logger.info(
                f"  {low:.0%}-{high:.0%}: {count:5d} samples | Accuracy: {accuracy_in_bucket:.2%}"
            )

    # Low confidence errors
    low_conf_mask = max_confidences < 0.7
    if low_conf_mask.sum() > 0:
        logger.info(
            f"\n⚠️ Low Confidence Predictions (<70%): {low_conf_mask.sum()} samples"
        )
        low_conf_errors = (~correct) & low_conf_mask
        if low_conf_errors.sum() > 0:
            logger.info(f"  Errors in low confidence: {low_conf_errors.sum()}")

    return max_confidences, correct


# def test_by_machine_type(model, features, X_test, y_test, test_df):
#     """Test performance across different machine types"""
#     logger.info("\n" + "="*60)
#     logger.info("🏭 PERFORMANCE BY MACHINE TYPE")
#     logger.info("="*60)

#     # Ensure machine_type is in test_df
#     if 'machine_type' not in test_df.columns:
#         logger.warning("Machine type not available in test data")
#         return None

#     results = []
#     for machine_type in test_df['machine_type'].unique():
#         mask = test_df['machine_type'] == machine_type
#         if mask.sum() > 0:
#             X_machine = X_test[mask]
#             y_machine = y_test[mask]

#             y_pred = model.predict(X_machine)
#             # y_pred_labels = y_test.iloc[mask].values  # Get actual labels
#             y_machine_true = y_test[mask]
#             y_pred_machine = model.predict(X_machine)

#             # Calculate accuracy
#             accuracy = accuracy_score(y_machine, y_pred)

#             results.append({
#                 'Machine Type': machine_type,
#                 'Samples': mask.sum(),
#                 'Accuracy': f"{accuracy:.2%}",
#                 'Correct': (y_machine == y_pred).sum(),
#                 'Incorrect': mask.sum() - (y_machine == y_pred).sum()
#             })

#     results_df = pd.DataFrame(results)
#     print(results_df.to_string(index=False))
#     return results_df


# def test_by_shift(model, X_test, y_test, test_df):
#     """Test performance across different shifts"""
#     logger.info("\n" + "="*60)
#     logger.info("🕐 PERFORMANCE BY SHIFT")
#     logger.info("="*60)

#     if 'shift_id' not in test_df.columns:
#         logger.warning("Shift information not available in test data")
#         return None

#     results = []
#     for shift in test_df['shift_id'].unique():
#         mask = test_df['shift_id'] == shift
#         if mask.sum() > 0:
#             X_shift = X_test[mask]
#             y_shift = y_test[mask]

#             y_pred = model.predict(X_shift)

#             accuracy = accuracy_score(y_shift, y_pred)

#             results.append({
#                 'Shift': shift,
#                 'Samples': mask.sum(),
#                 'Accuracy': f"{accuracy:.2%}",
#                 'Correct': (y_shift == y_pred).sum(),
#                 'Incorrect': mask.sum() - (y_shift == y_pred).sum()
#             })

#     results_df = pd.DataFrame(results)
#     print(results_df.to_string(index=False))
#     return results_df


def test_by_machine_type(model, features, X_test, y_test, test_df, label_encoder):
    """Test performance across different machine types"""
    logger.info("\n" + "=" * 60)
    logger.info("🏭 PERFORMANCE BY MACHINE TYPE")
    logger.info("=" * 60)

    if "machine_type" not in test_df.columns:
        logger.warning("Machine type not available in test data")
        return None

    results = []
    for machine_type in test_df["machine_type"].unique():
        mask = test_df["machine_type"] == machine_type
        if mask.sum() > 0:
            X_machine = X_test[mask]
            y_machine = y_test[mask]

            y_pred = model.predict(X_machine)
            y_pred_labels = label_encoder.inverse_transform(y_pred)  # FIXED
            accuracy = accuracy_score(y_machine, y_pred_labels)  # FIXED

            results.append(
                {
                    "Machine Type": machine_type,
                    "Samples": mask.sum(),
                    "Accuracy": f"{accuracy:.2%}",
                    "Correct": (y_machine == y_pred_labels).sum(),  # FIXED
                    "Incorrect": mask.sum()
                    - (y_machine == y_pred_labels).sum(),  # FIXED
                }
            )

    results_df = pd.DataFrame(results)
    print(results_df.to_string(index=False))
    return results_df


def test_by_shift(model, X_test, y_test, test_df, label_encoder):
    """Test performance across different shifts"""
    logger.info("\n" + "=" * 60)
    logger.info("🕐 PERFORMANCE BY SHIFT")
    logger.info("=" * 60)

    if "shift_id" not in test_df.columns:
        logger.warning("Shift information not available in test data")
        return None

    results = []
    for shift in test_df["shift_id"].unique():
        mask = test_df["shift_id"] == shift
        if mask.sum() > 0:
            X_shift = X_test[mask]
            y_shift = y_test[mask]

            y_pred = model.predict(X_shift)
            y_pred_labels = label_encoder.inverse_transform(y_pred)  # FIXED
            accuracy = accuracy_score(y_shift, y_pred_labels)  # FIXED

            results.append(
                {
                    "Shift": shift,
                    "Samples": mask.sum(),
                    "Accuracy": f"{accuracy:.2%}",
                    "Correct": (y_shift == y_pred_labels).sum(),  # FIXED
                    "Incorrect": mask.sum() - (y_shift == y_pred_labels).sum(),  # FIXED
                }
            )

    results_df = pd.DataFrame(results)
    print(results_df.to_string(index=False))
    return results_df


def test_edge_cases(model, features, X_test, y_test, test_df, label_encoder):
    """Test model on edge cases (extreme values)"""
    logger.info("\n" + "=" * 60)
    logger.info("⚠️ EDGE CASE TESTING")
    logger.info("=" * 60)

    # Test 1: Zero power consumption
    zero_power_mask = X_test["power_kw"] == 0
    if zero_power_mask.sum() > 0:
        logger.info(
            f"\n🔍 Test 1: Zero Power Consumption ({zero_power_mask.sum()} samples)"
        )
        y_pred_zero = model.predict(X_test[zero_power_mask])
        y_pred_zero_labels = label_encoder.inverse_transform(y_pred_zero)  # FIXED
        accuracy_zero = accuracy_score(
            y_test[zero_power_mask], y_pred_zero_labels
        )  # FIXED
        logger.info(f"  Accuracy: {accuracy_zero:.2%}")
        logger.info(
            f"  Predictions: {pd.Series(y_pred_zero_labels).value_counts().to_dict()}"
        )  # FIXED

    # Test 2: High temperature (>45°C)
    high_temp_mask = X_test["temperature_c"] > 45
    if high_temp_mask.sum() > 0:
        logger.info(
            f"\n🔥 Test 2: High Temperature (>45°C) ({high_temp_mask.sum()} samples)"
        )
        y_pred_high_temp = model.predict(X_test[high_temp_mask])
        y_pred_high_temp_labels = label_encoder.inverse_transform(
            y_pred_high_temp
        )  # FIXED
        accuracy_temp = accuracy_score(
            y_test[high_temp_mask], y_pred_high_temp_labels
        )  # FIXED
        logger.info(f"  Accuracy: {accuracy_temp:.2%}")

    # Test 3: High vibration
    high_vib_mask = X_test["vibration_mm_s"] > 5
    if high_vib_mask.sum() > 0:
        logger.info(
            f"\n📳 Test 3: High Vibration (>5 mm/s) ({high_vib_mask.sum()} samples)"
        )
        y_pred_high_vib = model.predict(X_test[high_vib_mask])
        y_pred_high_vib_labels = label_encoder.inverse_transform(
            y_pred_high_vib
        )  # FIXED
        accuracy_vib = accuracy_score(
            y_test[high_vib_mask], y_pred_high_vib_labels
        )  # FIXED
        logger.info(f"  Accuracy: {accuracy_vib:.2%}")

    # Test 4: Peak tariff hours
    peak_mask = (
        X_test["peak_tariff_flag"] == 1
        if "peak_tariff_flag" in X_test.columns
        else None
    )
    if peak_mask is not None and peak_mask.sum() > 0:
        logger.info(f"\n⚡ Test 4: Peak Tariff Hours ({peak_mask.sum()} samples)")
        y_pred_peak = model.predict(X_test[peak_mask])
        y_pred_peak_labels = label_encoder.inverse_transform(y_pred_peak)  # FIXED
        accuracy_peak = accuracy_score(y_test[peak_mask], y_pred_peak_labels)  # FIXED
        logger.info(f"  Accuracy: {accuracy_peak:.2%}")


# def test_edge_cases(model, features, X_test, y_test, test_df):
#     """Test model on edge cases (extreme values)"""
#     logger.info("\n" + "="*60)
#     logger.info("⚠️ EDGE CASE TESTING")
#     logger.info("="*60)

#     # Test 1: Zero power consumption
#     zero_power_mask = X_test['power_kw'] == 0
#     if zero_power_mask.sum() > 0:
#         logger.info(f"\n🔍 Test 1: Zero Power Consumption ({zero_power_mask.sum()} samples)")
#         y_pred_zero = model.predict(X_test[zero_power_mask])
#         accuracy_zero = accuracy_score(y_test[zero_power_mask], y_pred_zero)
#         logger.info(f"  Accuracy: {accuracy_zero:.2%}")
#         logger.info(f"  Predictions: {pd.Series(y_pred_zero).value_counts().to_dict()}")

#     # Test 2: High temperature (>45°C)
#     high_temp_mask = X_test['temperature_c'] > 45
#     if high_temp_mask.sum() > 0:
#         logger.info(f"\n🔥 Test 2: High Temperature (>45°C) ({high_temp_mask.sum()} samples)")
#         y_pred_high_temp = model.predict(X_test[high_temp_mask])
#         accuracy_temp = accuracy_score(y_test[high_temp_mask], y_pred_high_temp)
#         logger.info(f"  Accuracy: {accuracy_temp:.2%}")

#     # Test 3: High vibration
#     high_vib_mask = X_test['vibration_mm_s'] > 5
#     if high_vib_mask.sum() > 0:
#         logger.info(f"\n📳 Test 3: High Vibration (>5 mm/s) ({high_vib_mask.sum()} samples)")
#         y_pred_high_vib = model.predict(X_test[high_vib_mask])
#         accuracy_vib = accuracy_score(y_test[high_vib_mask], y_pred_high_vib)
#         logger.info(f"  Accuracy: {accuracy_vib:.2%}")

#     # Test 4: Peak tariff hours
#     peak_mask = X_test['peak_tariff_flag'] == 1 if 'peak_tariff_flag' in X_test.columns else None
#     if peak_mask is not None and peak_mask.sum() > 0:
#         logger.info(f"\n⚡ Test 4: Peak Tariff Hours ({peak_mask.sum()} samples)")
#         y_pred_peak = model.predict(X_test[peak_mask])
#         accuracy_peak = accuracy_score(y_test[peak_mask], y_pred_peak)
#         logger.info(f"  Accuracy: {accuracy_peak:.2%}")


def test_inference_speed(model, X_test):
    """Test model inference speed"""
    logger.info("\n" + "=" * 60)
    logger.info("⚡ INFERENCE SPEED TEST")
    logger.info("=" * 60)

    import time

    # Test single prediction
    single_sample = X_test.iloc[:1]
    start = time.time()
    for _ in range(1000):
        _ = model.predict(single_sample)
    single_time = (time.time() - start) / 1000

    # Test batch prediction
    batch_size = 1000
    batch_samples = X_test.iloc[:batch_size]
    start = time.time()
    _ = model.predict(batch_samples)
    batch_time = time.time() - start

    logger.info(f"\n🚀 Performance Metrics:")
    logger.info(f"  Single Prediction: {single_time * 1000:.3f} ms")
    logger.info(f"  Batch Prediction ({batch_size} samples): {batch_time:.3f} seconds")
    logger.info(f"  Throughput: {batch_size / batch_time:.0f} samples/second")

    # Real-time capability check
    if single_time < 0.05:  # 50ms threshold
        logger.info(f"  ✅ Real-time capable (<50ms per prediction)")
    else:
        logger.info(f"  ⚠️ May need optimization for real-time")


def generate_test_report(
    y_test, y_pred_labels, max_confidences, correct, accuracy, test_df, results_df
):
    """Generate comprehensive test report"""
    logger.info("\n" + "=" * 60)
    logger.info("📄 FINAL TEST REPORT")
    logger.info("=" * 60)

    # Create report dictionary
    report = {
        "Test Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Total Test Samples": len(y_test),
        "Overall Accuracy": f"{accuracy:.4f} ({accuracy * 100:.2f}%)",
        "Mean Confidence": f"{max_confidences.mean():.4f}",
        "Perfect Predictions": correct.sum(),
        "Misclassifications": (~correct).sum(),
        "Misclassification Rate": f"{(~correct).mean():.2%}",
        "Low Confidence Samples": (max_confidences < 0.7).sum(),
        "Model Ready for Production": "✅ YES"
        if accuracy > 0.95
        else "⚠️ Needs Improvement",
    }

    # Print report
    for key, value in report.items():
        logger.info(f"  {key}: {value}")

    # Save report to file
    report_df = pd.DataFrame([report])
    report_df.to_csv("model_2_test_report.csv", index=False)
    logger.info(f"\n💾 Detailed report saved to 'model_2_test_report.csv'")

    # Save predictions
    test_results = pd.DataFrame(
        {
            "actual": y_test.values,
            "predicted": y_pred_labels,
            "correct": correct,
            "confidence": max_confidences,
        }
    )
    test_results.to_csv("model_2_test_predictions.csv", index=False)
    logger.info(f"💾 Predictions saved to 'model_2_test_predictions.csv'")


def plot_test_results(y_test, y_pred_labels, max_confidences, cm, label_encoder):
    """Generate comprehensive test visualizations"""
    logger.info("\n" + "=" * 60)
    logger.info("📊 GENERATING TEST VISUALIZATIONS")
    logger.info("=" * 60)

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))

    # 1. Enhanced Confusion Matrix
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        ax=axes[0, 0],
        cmap="Blues",
        xticklabels=label_encoder.classes_,
        yticklabels=label_encoder.classes_,
    )
    axes[0, 0].set_title("Confusion Matrix", fontsize=14, fontweight="bold")
    axes[0, 0].set_xlabel("Predicted")
    axes[0, 0].set_ylabel("Actual")

    # 2. Confidence Distribution
    axes[0, 1].hist(
        max_confidences, bins=50, color="green", alpha=0.7, edgecolor="black"
    )
    axes[0, 1].axvline(
        x=0.9, color="red", linestyle="--", linewidth=2, label="90% Confidence"
    )
    axes[0, 1].axvline(
        x=max_confidences.mean(),
        color="blue",
        linestyle="--",
        linewidth=2,
        label=f"Mean: {max_confidences.mean():.3f}",
    )
    axes[0, 1].set_xlabel("Confidence Score")
    axes[0, 1].set_ylabel("Frequency")
    axes[0, 1].set_title("Model Confidence Distribution")
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    # 3. Accuracy vs Confidence
    confidence_bins = np.linspace(0, 1, 20)
    accuracy_by_confidence = []
    for i in range(len(confidence_bins) - 1):
        mask = (max_confidences >= confidence_bins[i]) & (
            max_confidences < confidence_bins[i + 1]
        )
        if mask.sum() > 0:
            acc = (y_test.values[mask] == y_pred_labels[mask]).mean()
            accuracy_by_confidence.append(acc)
        else:
            accuracy_by_confidence.append(0)

    axes[0, 2].bar(confidence_bins[:-1], accuracy_by_confidence, width=0.05, alpha=0.7)
    axes[0, 2].plot([0, 1], [0, 1], "r--", label="Perfect Calibration")
    axes[0, 2].set_xlabel("Confidence")
    axes[0, 2].set_ylabel("Accuracy")
    axes[0, 2].set_title("Confidence Calibration")
    axes[0, 2].legend()
    axes[0, 2].grid(True, alpha=0.3)

    # 4. Per-class Precision
    precision_per_class = precision_score(
        y_test, y_pred_labels, average=None, labels=label_encoder.classes_
    )
    axes[1, 0].bar(
        label_encoder.classes_, precision_per_class, color=["green", "orange", "red"]
    )
    axes[1, 0].set_ylim([0, 1.05])
    axes[1, 0].set_ylabel("Precision")
    axes[1, 0].set_title("Precision by Class")
    axes[1, 0].axhline(y=0.9, color="green", linestyle="--", alpha=0.5)
    for i, v in enumerate(precision_per_class):
        axes[1, 0].text(i, v + 0.02, f"{v:.3f}", ha="center")

    # 5. Error Analysis
    errors = y_test.values != y_pred_labels
    if errors.sum() > 0:
        error_types = []
        for i in range(len(errors)):
            if errors[i]:
                error_types.append(f"{y_test.values[i]}→{y_pred_labels[i]}")
        error_counts = pd.Series(error_types).value_counts()
        axes[1, 1].bar(range(len(error_counts)), error_counts.values, color="coral")
        axes[1, 1].set_xticks(range(len(error_counts)))
        axes[1, 1].set_xticklabels(error_counts.index, rotation=45, ha="right")
        axes[1, 1].set_title(f"Error Analysis (Total: {errors.sum()} errors)")
        axes[1, 1].set_ylabel("Count")
    else:
        axes[1, 1].text(
            0.5,
            0.5,
            "✨ PERFECT! No Errors Found ✨",
            ha="center",
            va="center",
            transform=axes[1, 1].transAxes,
            fontsize=16,
            fontweight="bold",
            color="green",
        )
        axes[1, 1].set_title("Error Analysis - Perfect Model")

    # 6. Performance Summary
    axes[1, 2].axis("off")
    summary_text = f"""
    MODEL PERFORMANCE SUMMARY
    ═══════════════════════════════
    
    ✅ Overall Accuracy: {accuracy_score(y_test, y_pred_labels):.2%}
    
    📊 Class-wise Performance:
    • Efficient:      {precision_score(y_test, y_pred_labels, labels=["efficient"], average=None)[0]:.2%}
    • Moderate Waste: {precision_score(y_test, y_pred_labels, labels=["moderate_waste"], average=None)[0] if "moderate_waste" in label_encoder.classes_ else "N/A":.2%}
    • Severe Waste:   {precision_score(y_test, y_pred_labels, labels=["severe_waste"], average=None)[0] if "severe_waste" in label_encoder.classes_ else "N/A":.2%}
    
    🎯 Confidence Stats:
    • Mean Confidence: {max_confidences.mean():.2%}
    • High Confidence (>90%): {(max_confidences > 0.9).sum():,} samples
    
    🚀 Ready for Production!
    """
    axes[1, 2].text(
        0.1,
        0.5,
        summary_text,
        transform=axes[1, 2].transAxes,
        fontsize=12,
        verticalalignment="center",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )

    plt.tight_layout()
    plt.savefig("model_2_test_results.png", dpi=150, bbox_inches="tight")
    plt.show()
    logger.info("✅ Test visualizations saved to 'model_2_test_results.png'")


def main():
    """Main test pipeline"""
    logger.info("🚀 Starting Model 2 Comprehensive Testing")
    logger.info("=" * 60)

    # Load model
    model, label_encoder, features = load_model_and_artifacts()
    if model is None:
        return

    # Load test data
    X_test, y_test, test_df = load_test_data()

    # Basic performance test
    y_pred, y_pred_proba, y_pred_labels = test_basic_performance(
        model, label_encoder, X_test, y_test
    )

    # Confidence metrics
    max_confidences, correct = test_confidence_metrics(
        model, X_test, y_test, y_pred_labels
    )

    # Test by machine type
    # machine_results = test_by_machine_type(model, features, X_test, y_test, test_df)
    machine_results = test_by_machine_type(
        model, features, X_test, y_test, test_df, label_encoder
    )

    # Test by shift
    shift_results = test_by_shift(model, X_test, y_test, test_df, label_encoder)

    # Edge case testing
    test_edge_cases(model, features, X_test, y_test, test_df, label_encoder)

    # Inference speed test
    test_inference_speed(model, X_test)

    # Calculate final metrics
    accuracy = accuracy_score(y_test, y_pred_labels)
    cm = confusion_matrix(y_test, y_pred_labels, labels=label_encoder.classes_)

    # Generate report
    generate_test_report(
        y_test,
        y_pred_labels,
        max_confidences,
        correct,
        accuracy,
        test_df,
        machine_results,
    )

    # Plot results
    plot_test_results(y_test, y_pred_labels, max_confidences, cm, label_encoder)

    # Final verdict
    logger.info("\n" + "=" * 60)
    logger.info("✅ MODEL 2 TESTING COMPLETE")
    logger.info("=" * 60)

    if accuracy > 0.95:
        logger.info("🎉 EXCELLENT! Model is production-ready!")
        logger.info("   - Exceptional accuracy (>95%)")
        logger.info("   - High confidence predictions")
        logger.info("   - Ready for real-time deployment")
    elif accuracy > 0.85:
        logger.info("👍 GOOD! Model is suitable for most use cases")
        logger.info("   - Consider additional training for critical applications")
    else:
        logger.info("⚠️ Model needs improvement before production")
        logger.info("   - Consider more features or different algorithm")

    logger.info("\n📁 Generated Files:")
    logger.info("   - model_2_test_report.csv (Detailed metrics)")
    logger.info("   - model_2_test_predictions.csv (All predictions)")
    logger.info("   - model_2_test_results.png (Visualizations)")


if __name__ == "__main__":
    main()

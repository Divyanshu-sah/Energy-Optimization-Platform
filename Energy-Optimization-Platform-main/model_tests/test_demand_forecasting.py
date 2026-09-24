"""
Model 3 Testing & Validation Script
Tests the demand forecasting model with multiple scenarios
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    mean_absolute_percentage_error,
)
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
        model = joblib.load("models/model_forecast.pkl")
        features = joblib.load("models/features_forecast.pkl")
        logger.info("✅ Model and artifacts loaded successfully")
        return model, features
    except FileNotFoundError as e:
        logger.error(f"❌ Model files not found: {e}")
        logger.info("Please train the model first using demand_forecast.py")
        return None, None


def load_test_data():
    """Load and prepare test data (use last 20% for temporal testing)"""
    df = pd.read_csv("data/synthetic/processed/training_dataset_forecast.csv")
    logger.info(f"📊 Loaded {len(df):,} total records")

    # Convert timestamp to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Use last 20% for testing (temporal split)
    test_size = int(len(df) * 0.2)
    test_df = df.tail(test_size).copy()

    # Features (exclude target and non-feature columns)
    exclude_cols = ["timestamp", "plant_id", "target_next_power_kw"]
    feature_columns = [col for col in test_df.columns if col not in exclude_cols]

    X_test = test_df[feature_columns].fillna(0)
    y_test = test_df["target_next_power_kw"]
    timestamps = test_df["timestamp"]

    logger.info(f"🧪 Test set size: {len(X_test):,} samples")
    logger.info(f"📈 Test time range: {timestamps.min()} to {timestamps.max()}")
    logger.info(f"📊 Target statistics:\n{y_test.describe()}")

    return X_test, y_test, timestamps, test_df, feature_columns


def test_basic_performance(model, X_test, y_test):
    """Test basic regression performance"""
    logger.info("\n" + "=" * 60)
    logger.info("📊 BASIC PERFORMANCE TEST")
    logger.info("=" * 60)

    # Predict
    y_pred = model.predict(X_test)

    # Calculate metrics
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)
    mape = mean_absolute_percentage_error(y_test, y_pred) * 100

    logger.info(f"\n🎯 Overall Metrics:")
    logger.info(f"  MAE:  {mae:.4f} kW")
    logger.info(f"  MSE:  {mse:.4f} kW²")
    logger.info(f"  RMSE: {rmse:.4f} kW")
    logger.info(f"  R²:   {r2:.4f} ({r2 * 100:.2f}%)")
    logger.info(f"  MAPE: {mape:.2f}%")

    # Calculate accuracy within thresholds
    abs_error = np.abs(y_test - y_pred)
    within_5kw = (abs_error <= 5).mean() * 100
    within_10kw = (abs_error <= 10).mean() * 100
    within_20kw = (abs_error <= 20).mean() * 100

    logger.info(f"\n📏 Prediction Accuracy:")
    logger.info(f"  Within ±5 kW:  {within_5kw:.1f}% of predictions")
    logger.info(f"  Within ±10 kW: {within_10kw:.1f}% of predictions")
    logger.info(f"  Within ±20 kW: {within_20kw:.1f}% of predictions")

    return y_pred, {"mae": mae, "rmse": rmse, "r2": r2, "mape": mape}


def test_temporal_accuracy(model, X_test, y_test, timestamps, y_pred):
    """Test accuracy over time periods"""
    logger.info("\n" + "=" * 60)
    logger.info("🕐 TEMPORAL ACCURACY TEST")
    logger.info("=" * 60)

    # Add time features to test_df for grouping
    test_df = pd.DataFrame(
        {
            "timestamp": timestamps,
            "actual": y_test,
            "predicted": y_pred,
            "error": np.abs(y_test - y_pred),
        }
    )

    test_df["hour"] = test_df["timestamp"].dt.hour
    test_df["day"] = test_df["timestamp"].dt.dayofweek
    test_df["weekend"] = test_df["day"] >= 5

    # Performance by hour
    logger.info(f"\n📊 Performance by Hour of Day:")
    hourly_mae = test_df.groupby("hour")["error"].mean()
    for hour in range(24):
        if hour in hourly_mae.index:
            logger.info(f"  Hour {hour:02d}:00 - MAE: {hourly_mae[hour]:.4f} kW")

    # Performance by day type
    logger.info(f"\n📅 Performance by Day Type:")
    weekday_mae = test_df[~test_df["weekend"]]["error"].mean()
    weekend_mae = test_df[test_df["weekend"]]["error"].mean()
    logger.info(f"  Weekdays:  MAE = {weekday_mae:.4f} kW")
    logger.info(f"  Weekends:  MAE = {weekend_mae:.4f} kW")

    # Best and worst performing hours
    best_hour = hourly_mae.idxmin()
    worst_hour = hourly_mae.idxmax()
    logger.info(
        f"\n⭐ Best performing hour: {best_hour}:00 (MAE: {hourly_mae[best_hour]:.4f} kW)"
    )
    logger.info(
        f"⚠️ Worst performing hour: {worst_hour}:00 (MAE: {hourly_mae[worst_hour]:.4f} kW)"
    )

    return test_df


def test_peak_demand_prediction(model, X_test, y_test, y_pred):
    """Test accuracy during peak demand periods"""
    logger.info("\n" + "=" * 60)
    logger.info("⚡ PEAK DEMAND TEST")
    logger.info("=" * 60)

    # Identify peak demand periods (top 10%)
    peak_threshold = y_test.quantile(0.9)
    peak_mask = y_test >= peak_threshold

    peak_actual = y_test[peak_mask]
    peak_predicted = y_pred[peak_mask]

    if len(peak_actual) > 0:
        peak_mae = mean_absolute_error(peak_actual, peak_predicted)
        peak_mape = mean_absolute_percentage_error(peak_actual, peak_predicted) * 100

        logger.info(f"\n📈 Peak Demand Analysis (Top 10%: >{peak_threshold:.1f} kW):")
        logger.info(
            f"  Peak samples: {len(peak_actual)} ({len(peak_actual) / len(y_test) * 100:.1f}%)"
        )
        logger.info(f"  Peak MAE:  {peak_mae:.4f} kW")
        logger.info(f"  Peak MAPE: {peak_mape:.2f}%")

        # Compare with normal demand
        normal_mask = y_test < peak_threshold
        normal_mae = mean_absolute_error(y_test[normal_mask], y_pred[normal_mask])
        logger.info(f"\n  Normal demand MAE: {normal_mae:.4f} kW")
        logger.info(f"  Peak vs Normal: {peak_mae - normal_mae:+.4f} kW difference")

        if peak_mae > normal_mae * 1.5:
            logger.info(f"  ⚠️ Peak prediction needs improvement")
        else:
            logger.info(f"  ✅ Peak prediction is good")

    return peak_mask


def test_feature_importance(model, feature_names):
    """Analyze feature importance"""
    logger.info("\n" + "=" * 60)
    logger.info("🔍 FEATURE IMPORTANCE ANALYSIS")
    logger.info("=" * 60)

    importance_df = pd.DataFrame(
        {"feature": feature_names, "importance": model.feature_importances_}
    ).sort_values("importance", ascending=False)

    logger.info(f"\n📊 Top 10 Most Important Features:")
    for i, row in importance_df.head(10).iterrows():
        logger.info(f"  {row['feature']:<25} : {row['importance']:.4f}")

    logger.info(f"\n📊 Bottom 5 Least Important Features:")
    for i, row in importance_df.tail(5).iterrows():
        logger.info(f"  {row['feature']:<25} : {row['importance']:.4f}")

    # Cumulative importance
    cumulative_importance = importance_df["importance"].cumsum()
    features_for_95 = (cumulative_importance <= 0.95).sum()
    logger.info(f"\n🎯 {features_for_95} features explain 95% of importance")

    return importance_df


def test_error_analysis(y_test, y_pred, timestamps):
    """Analyze prediction errors in detail"""
    logger.info("\n" + "=" * 60)
    logger.info("📉 ERROR ANALYSIS")
    logger.info("=" * 60)

    errors = y_test - y_pred
    abs_errors = np.abs(errors)

    logger.info(f"\n📊 Error Statistics:")
    logger.info(f"  Mean Error:     {errors.mean():.4f} kW")
    logger.info(f"  Std Error:      {errors.std():.4f} kW")
    logger.info(f"  Median Error:   {np.median(errors):.4f} kW")
    logger.info(f"  90th Percentile: {np.percentile(abs_errors, 90):.4f} kW")
    logger.info(f"  95th Percentile: {np.percentile(abs_errors, 95):.4f} kW")
    logger.info(f"  99th Percentile: {np.percentile(abs_errors, 99):.4f} kW")

    # Bias analysis (systematic over/under prediction)
    bias = errors.mean()
    if bias > 0:
        logger.info(f"\n⚠️ Model systematically UNDER-predicts by {abs(bias):.4f} kW")
    elif bias < 0:
        logger.info(f"\n⚠️ Model systematically OVER-predicts by {abs(bias):.4f} kW")
    else:
        logger.info(f"\n✅ No systematic bias detected")

    # Find worst predictions
    error_df = pd.DataFrame(
        {
            "timestamp": timestamps,
            "actual": y_test,
            "predicted": y_pred,
            "error": abs_errors,
        }
    ).sort_values("error", ascending=False)

    logger.info(f"\n🔴 Top 5 Worst Predictions:")
    for i, row in error_df.head(5).iterrows():
        logger.info(
            f"  {row['timestamp']}: Actual={row['actual']:.2f}kW, "
            f"Predicted={row['predicted']:.2f}kW, Error={row['error']:.2f}kW"
        )

    return errors, error_df


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
    batch_size = min(1000, len(X_test))
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


def plot_test_results(y_test, y_pred, errors, timestamps, importance_df, metrics):
    """Generate comprehensive test visualizations"""
    logger.info("\n" + "=" * 60)
    logger.info("📊 GENERATING TEST VISUALIZATIONS")
    logger.info("=" * 60)

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))

    # 1. Actual vs Predicted Scatter
    ax1 = axes[0, 0]
    ax1.scatter(y_test, y_pred, alpha=0.5, s=10, c="blue", edgecolors="none")
    ax1.plot(
        [y_test.min(), y_test.max()],
        [y_test.min(), y_test.max()],
        "r--",
        lw=2,
        label="Perfect Prediction",
    )
    ax1.set_xlabel("Actual Power (kW)")
    ax1.set_ylabel("Predicted Power (kW)")
    ax1.set_title(f"Actual vs Predicted (R² = {metrics['r2']:.3f})")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 2. Time Series Comparison
    ax2 = axes[0, 1]
    sample_size = min(200, len(timestamps))
    indices = np.linspace(0, len(timestamps) - 1, sample_size, dtype=int)
    ax2.plot(
        timestamps.iloc[indices],
        y_test.iloc[indices],
        label="Actual",
        alpha=0.7,
        linewidth=1.5,
        color="blue",
    )
    ax2.plot(
        timestamps.iloc[indices],
        y_pred[indices],
        label="Predicted",
        alpha=0.7,
        linewidth=1.5,
        color="red",
        linestyle="--",
    )
    ax2.set_xlabel("Timestamp")
    ax2.set_ylabel("Power (kW)")
    ax2.set_title("Time Series: Actual vs Predicted")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

    # 3. Residuals Distribution
    ax3 = axes[0, 2]
    ax3.hist(errors, bins=50, edgecolor="black", alpha=0.7, color="purple")
    ax3.axvline(x=0, color="red", linestyle="--", linewidth=2, label="Zero Error")
    ax3.axvline(
        x=errors.mean(),
        color="blue",
        linestyle="--",
        linewidth=2,
        label=f"Mean: {errors.mean():.2f}",
    )
    ax3.set_xlabel("Residuals (kW)")
    ax3.set_ylabel("Frequency")
    ax3.set_title("Residuals Distribution")
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # 4. Feature Importance
    ax4 = axes[1, 0]
    top_features = importance_df.head(10)
    ax4.barh(
        range(len(top_features)), top_features["importance"].values, color="skyblue"
    )
    ax4.set_yticks(range(len(top_features)))
    ax4.set_yticklabels(top_features["feature"].values)
    ax4.set_xlabel("Importance Score")
    ax4.set_title("Top 10 Feature Importances")
    ax4.invert_yaxis()

    # 5. Error by Hour
    ax5 = axes[1, 1]
    error_df = pd.DataFrame({"hour": timestamps.dt.hour, "error": np.abs(errors)})
    hourly_error = error_df.groupby("hour")["error"].mean()
    ax5.bar(hourly_error.index, hourly_error.values, color="coral", alpha=0.7)
    ax5.set_xlabel("Hour of Day")
    ax5.set_ylabel("Mean Absolute Error (kW)")
    ax5.set_title("Prediction Error by Hour")
    ax5.grid(True, alpha=0.3)

    # 6. Error Metrics Comparison
    ax6 = axes[1, 2]
    metrics_names = ["MAE", "RMSE", "MAPE (%)"]
    metrics_values = [metrics["mae"], metrics["rmse"], metrics["mape"]]
    colors = ["blue", "orange", "green"]
    bars = ax6.bar(metrics_names, metrics_values, color=colors, alpha=0.7)
    ax6.set_title("Error Metrics")
    ax6.set_ylabel("Value")
    for bar, value in zip(bars, metrics_values):
        ax6.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.01,
            f"{value:.2f}",
            ha="center",
            va="bottom",
        )

    plt.tight_layout()
    plt.savefig("model_3_test_results.png", dpi=150, bbox_inches="tight")
    plt.show()
    logger.info("✅ Test visualizations saved to 'model_3_test_results.png'")

    # Additional plot: Residuals over time
    fig2, ax = plt.subplots(figsize=(12, 6))
    ax.scatter(timestamps, errors, alpha=0.5, s=10, c="red")
    ax.axhline(y=0, color="black", linestyle="-", linewidth=1)
    ax.axhline(
        y=metrics["mae"],
        color="blue",
        linestyle="--",
        label=f"MAE: {metrics['mae']:.2f}",
    )
    ax.axhline(y=-metrics["mae"], color="blue", linestyle="--")
    ax.set_xlabel("Timestamp")
    ax.set_ylabel("Prediction Error (kW)")
    ax.set_title("Prediction Errors Over Time")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("model_3_errors_over_time.png", dpi=150, bbox_inches="tight")
    plt.show()


def generate_test_report(metrics, test_df, error_df, importance_df):
    """Generate comprehensive test report"""
    logger.info("\n" + "=" * 60)
    logger.info("📄 FINAL TEST REPORT")
    logger.info("=" * 60)

    # Calculate additional metrics
    within_5kw = (np.abs(test_df["error"]) <= 5).mean() * 100
    within_10kw = (np.abs(test_df["error"]) <= 10).mean() * 100

    report = {
        "Test Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Total Test Samples": len(test_df),
        "MAE (kW)": f"{metrics['mae']:.4f}",
        "RMSE (kW)": f"{metrics['rmse']:.4f}",
        "R² Score": f"{metrics['r2']:.4f} ({metrics['r2'] * 100:.2f}%)",
        "MAPE (%)": f"{metrics['mape']:.2f}%",
        "Within ±5 kW": f"{within_5kw:.1f}%",
        "Within ±10 kW": f"{within_10kw:.1f}%",
        "Top Feature": importance_df.iloc[0]["feature"],
        "Top Feature Importance": f"{importance_df.iloc[0]['importance']:.4f}",
        "Model Ready for Production": "✅ YES"
        if metrics["r2"] > 0.85
        else "⚠️ Needs Improvement",
    }

    # Print report
    logger.info(f"\n📊 Performance Summary:")
    for key, value in report.items():
        logger.info(f"  {key}: {value}")

    # Save report to file
    report_df = pd.DataFrame([report])
    report_df.to_csv("model_3_test_report.csv", index=False)
    logger.info(f"\n💾 Detailed report saved to 'model_3_test_report.csv'")

    # Save predictions
    predictions_df = pd.DataFrame(
        {
            "timestamp": test_df["timestamp"],
            "actual_power_kw": test_df["actual"],
            "predicted_power_kw": test_df["predicted"],
            "error_kw": test_df["error"],
            "abs_error_kw": np.abs(test_df["error"]),
        }
    )
    predictions_df.to_csv("model_3_test_predictions.csv", index=False)
    logger.info(f"💾 Predictions saved to 'model_3_test_predictions.csv'")


def main():
    """Main test pipeline"""
    logger.info("🚀 Starting Model 3 Comprehensive Testing")
    logger.info("=" * 60)

    # Load model and data
    model, features = load_model_and_artifacts()
    if model is None:
        return

    X_test, y_test, timestamps, test_df, feature_names = load_test_data()

    # Basic performance test
    y_pred, metrics = test_basic_performance(model, X_test, y_test)

    # Temporal accuracy test
    temporal_df = test_temporal_accuracy(model, X_test, y_test, timestamps, y_pred)

    # Peak demand test
    peak_mask = test_peak_demand_prediction(model, X_test, y_test, y_pred)

    # Feature importance analysis
    importance_df = test_feature_importance(model, feature_names)

    # Error analysis
    errors, error_df = test_error_analysis(y_test, y_pred, timestamps)

    # Inference speed test
    test_inference_speed(model, X_test)

    # Create test DataFrame for reporting
    test_results_df = pd.DataFrame(
        {
            "timestamp": timestamps,
            "actual": y_test,
            "predicted": y_pred,
            "error": errors,
        }
    )

    # Plot results
    plot_test_results(y_test, y_pred, errors, timestamps, importance_df, metrics)

    # Generate report
    generate_test_report(metrics, test_results_df, error_df, importance_df)

    # Final verdict
    logger.info("\n" + "=" * 60)
    logger.info("✅ MODEL 3 TESTING COMPLETE")
    logger.info("=" * 60)

    if metrics["r2"] > 0.85:
        logger.info("🎉 EXCELLENT! Model is production-ready!")
        logger.info(f"   - R² Score: {metrics['r2']:.2%} (excellent)")
        logger.info(f"   - MAPE: {metrics['mape']:.2f}% (very good)")
        logger.info("   - Ready for real-time forecasting")
    elif metrics["r2"] > 0.70:
        logger.info("👍 GOOD! Model is suitable for most use cases")
        logger.info(f"   - R² Score: {metrics['r2']:.2%}")
        logger.info(f"   - MAPE: {metrics['mape']:.2f}%")
        logger.info("   - Consider additional features for improvement")
    else:
        logger.info("⚠️ Model needs improvement before production")
        logger.info(f"   - R² Score: {metrics['r2']:.2%} (below threshold)")
        logger.info("   - Consider more features or different algorithm")

    logger.info("\n📁 Generated Files:")
    logger.info("   - model_3_test_report.csv (Detailed metrics)")
    logger.info("   - model_3_test_predictions.csv (All predictions)")
    logger.info("   - model_3_test_results.png (Visualizations)")
    logger.info("   - model_3_errors_over_time.png (Error timeline)")


if __name__ == "__main__":
    main()

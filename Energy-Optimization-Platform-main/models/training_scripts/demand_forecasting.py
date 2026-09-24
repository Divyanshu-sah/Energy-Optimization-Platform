"""
Model 3: Demand Forecasting using XGBoost Regressor
Predicts next-step energy demand for industrial plants
"""

import pandas as pd
import numpy as np
import joblib
import xgboost as xgb
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
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
        logging.FileHandler("model_3_forecast_training.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def load_and_prepare_data(filepath):
    """Load forecast training data"""
    logger.info(f"Loading data from {filepath}")
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df):,} records with {len(df.columns)} columns")

    # Convert timestamp to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Define feature columns (exclude target and non-feature columns)
    exclude_cols = ["timestamp", "plant_id", "target_next_power_kw"]
    feature_columns = [col for col in df.columns if col not in exclude_cols]

    logger.info(f"Using {len(feature_columns)} features: {feature_columns[:10]}...")

    # Prepare feature matrix
    X = df[feature_columns].copy()

    # Handle missing values
    X = X.fillna(X.median())

    # Target variable
    y = df["target_next_power_kw"]

    # Log target statistics
    logger.info(f"Target statistics:\n{y.describe()}")

    return X, y, feature_columns, df["timestamp"]


def train_xgboost_regressor(X_train, y_train, X_val, y_val):
    """Train XGBoost regressor with optimized parameters"""
    logger.info("Training XGBoost Regressor...")

    # Initialize model
    model = xgb.XGBRegressor(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric="rmse",
        early_stopping_rounds=50,
    )

    # Train with early stopping
    eval_set = [(X_train, y_train), (X_val, y_val)]
    model.fit(X_train, y_train, eval_set=eval_set, verbose=False)

    logger.info("XGBoost training completed")
    logger.info(f"Best iteration: {model.best_iteration}")
    logger.info(f"Best RMSE: {model.best_score:.4f}")

    return model


def evaluate_model(model, X_test, y_test, timestamps):
    """Evaluate regression performance"""
    logger.info("Evaluating model performance...")

    # Predictions
    y_pred = model.predict(X_test)

    # Metrics
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    # Calculate MAPE (avoid division by zero)
    mape = np.mean(np.abs((y_test - y_pred) / (y_test + 1e-6))) * 100

    logger.info(f"Mean Absolute Error (MAE): {mae:.4f} kW")
    logger.info(f"Root Mean Square Error (RMSE): {rmse:.4f} kW")
    logger.info(f"R² Score: {r2:.4f}")
    logger.info(f"Mean Absolute Percentage Error (MAPE): {mape:.2f}%")

    # Calculate additional metrics
    mse = mean_squared_error(y_test, y_pred)
    logger.info(f"Mean Squared Error (MSE): {mse:.4f}")

    return y_pred, {"mae": mae, "rmse": rmse, "r2": r2, "mape": mape, "mse": mse}


def plot_results(model, X_test, y_test, y_pred, timestamps, feature_names):
    """Generate comprehensive visualizations"""
    logger.info("Generating visualizations...")

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))

    # 1. Actual vs Predicted
    ax1 = axes[0, 0]
    ax1.scatter(y_test, y_pred, alpha=0.5, s=10)
    ax1.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], "r--", lw=2)
    ax1.set_xlabel("Actual Power (kW)")
    ax1.set_ylabel("Predicted Power (kW)")
    ax1.set_title("Actual vs Predicted Values")
    ax1.grid(True, alpha=0.3)

    # 2. Time Series Plot
    ax2 = axes[0, 1]
    sample_size = min(500, len(timestamps))
    indices = np.random.choice(len(timestamps), sample_size, replace=False)
    indices.sort()

    ax2.plot(
        timestamps.iloc[indices],
        y_test.iloc[indices],
        label="Actual",
        alpha=0.7,
        linewidth=1,
    )
    ax2.plot(
        timestamps.iloc[indices],
        y_pred[indices],
        label="Predicted",
        alpha=0.7,
        linewidth=1,
    )
    ax2.set_xlabel("Timestamp")
    ax2.set_ylabel("Power (kW)")
    ax2.set_title("Time Series: Actual vs Predicted")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

    # 3. Residuals Distribution
    ax3 = axes[0, 2]
    residuals = y_test - y_pred
    ax3.hist(residuals, bins=50, edgecolor="black", alpha=0.7)
    ax3.axvline(x=0, color="red", linestyle="--", linewidth=2)
    ax3.set_xlabel("Residuals (kW)")
    ax3.set_ylabel("Frequency")
    ax3.set_title("Residuals Distribution")
    ax3.grid(True, alpha=0.3)

    # 4. Feature Importance
    ax4 = axes[1, 0]
    importance = pd.DataFrame(
        {"feature": feature_names, "importance": model.feature_importances_}
    ).sort_values("importance", ascending=True)

    importance.tail(10).plot(
        kind="barh", x="feature", y="importance", ax=ax4, color="skyblue"
    )
    ax4.set_title("Top 10 Feature Importances")
    ax4.set_xlabel("Importance Score")

    # 5. Residuals vs Predicted
    ax5 = axes[1, 1]
    ax5.scatter(y_pred, residuals, alpha=0.5, s=10)
    ax5.axhline(y=0, color="red", linestyle="--", linewidth=2)
    ax5.set_xlabel("Predicted Power (kW)")
    ax5.set_ylabel("Residuals (kW)")
    ax5.set_title("Residuals vs Predicted Values")
    ax5.grid(True, alpha=0.3)

    # 6. Error Metrics Bar Chart
    ax6 = axes[1, 2]
    metrics = {
        "MAE": np.mean(np.abs(residuals)),
        "RMSE": np.sqrt(np.mean(residuals**2)),
        "MAPE (%)": np.mean(np.abs(residuals / (y_test + 1e-6))) * 100,
    }
    bars = ax6.bar(metrics.keys(), metrics.values(), color=["blue", "orange", "green"])
    ax6.set_title("Error Metrics")
    ax6.set_ylabel("Value")

    # Add value labels on bars
    for bar, value in zip(bars, metrics.values()):
        ax6.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.01,
            f"{value:.2f}",
            ha="center",
            va="bottom",
        )

    plt.tight_layout()
    plt.savefig("model_3_forecast_results.png", dpi=150, bbox_inches="tight")
    plt.show()
    logger.info("Visualizations saved to 'model_3_forecast_results.png'")

    # Additional plot: Residuals Q-Q plot
    fig2, ax = plt.subplots(figsize=(8, 6))
    from scipy import stats

    stats.probplot(residuals, dist="norm", plot=ax)
    ax.set_title("Q-Q Plot of Residuals")
    ax.grid(True, alpha=0.3)
    plt.savefig("model_3_residuals_qqplot.png", dpi=150, bbox_inches="tight")
    plt.show()


def save_model(model, feature_names):
    """Save trained model and artifacts"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save model
    model_path = "models/model_forecast.pkl"
    joblib.dump(model, model_path)
    logger.info(f"Model saved to {model_path}")

    # Save feature names
    features_path = "models/features_forecast.pkl"
    joblib.dump(feature_names, features_path)
    logger.info(f"Feature names saved to {features_path}")

    # Backups
    backup_model = f"models/model_forecast_{timestamp}.pkl"
    backup_features = f"models/features_forecast_{timestamp}.pkl"
    joblib.dump(model, backup_model)
    joblib.dump(feature_names, backup_features)
    logger.info(f"Backups saved: {backup_model}, {backup_features}")


def main():
    """Main training pipeline"""
    logger.info("=" * 60)
    logger.info("MODEL 3: Demand Forecasting Training Pipeline")
    logger.info("=" * 60)

    # Create models directory
    import os

    os.makedirs("models", exist_ok=True)

    # Load data
    X, y, feature_names, timestamps = load_and_prepare_data(
        "data/synthetic/processed/training_dataset_forecast.csv"
    )

    # Time-based split (maintain temporal order)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    timestamps_train, timestamps_test = timestamps[:split_idx], timestamps[split_idx:]

    logger.info(
        f"Training set: {len(X_train):,} samples (before {timestamps_train.iloc[-1]})"
    )
    logger.info(f"Test set: {len(X_test):,} samples (after {timestamps_test.iloc[0]})")

    # Further split training for validation
    val_idx = int(len(X_train) * 0.8)
    X_train_final, X_val = X_train[:val_idx], X_train[val_idx:]
    y_train_final, y_val = y_train[:val_idx], y_train[val_idx:]

    # Train model
    model = train_xgboost_regressor(X_train_final, y_train_final, X_val, y_val)

    # Evaluate
    y_pred, metrics = evaluate_model(model, X_test, y_test, timestamps_test)

    # Visualize
    plot_results(model, X_test, y_test, y_pred, timestamps_test, feature_names)

    # Save model
    save_model(model, feature_names)

    logger.info("=" * 60)
    logger.info("Model 3 Training Completed Successfully!")
    logger.info(f"Final RMSE: {metrics['rmse']:.4f} kW")
    logger.info(f"Final R² Score: {metrics['r2']:.4f}")
    logger.info(f"Final MAPE: {metrics['mape']:.2f}%")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

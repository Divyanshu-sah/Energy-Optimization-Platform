from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data" / "synthetic"

ANOMALY_MODEL_PATH = MODELS_DIR / "model_anomaly.pkl"
ANOMALY_SCALER_PATH = MODELS_DIR / "scaler_anomaly.pkl"

EFFICIENCY_MODEL_PATH = MODELS_DIR / "model_efficiency.pkl"
EFFICIENCY_ENCODER_PATH = MODELS_DIR / "label_encoder_efficiency.pkl"
EFFICIENCY_FEATURES_PATH = MODELS_DIR / "features_efficiency.pkl"

FORECAST_MODEL_PATH = MODELS_DIR / "model_forecast.pkl"
FORECAST_FEATURES_PATH = MODELS_DIR / "features_forecast.pkl"

TELEMETRY_DATA_PATH = DATA_DIR / "raw" / "telemetry_machine_level.csv"
MACHINE_METADATA_PATH = DATA_DIR / "raw" / "machine_metadata.csv"
RECOMMENDATIONS_REF_PATH = DATA_DIR / "processed" / "recommendations_reference.csv"
PLANT_DEMAND_PATH = DATA_DIR / "processed" / "plant_demand_timeseries.csv"

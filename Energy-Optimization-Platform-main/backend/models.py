import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from config import (
    ANOMALY_MODEL_PATH,
    ANOMALY_SCALER_PATH,
    EFFICIENCY_MODEL_PATH,
    EFFICIENCY_ENCODER_PATH,
    EFFICIENCY_FEATURES_PATH,
    FORECAST_MODEL_PATH,
    FORECAST_FEATURES_PATH,
)


class ModelLoader:
    _instance = None
    _anomaly_model = None
    _anomaly_scaler = None
    _efficiency_model = None
    _efficiency_encoder = None
    _efficiency_features = None
    _forecast_model = None
    _forecast_features = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_all_models(self):
        self._load_anomaly_model()
        self._load_efficiency_model()
        self._load_forecast_model()

    def _load_anomaly_model(self):
        if self._anomaly_model is None:
            try:
                self._anomaly_model = joblib.load(ANOMALY_MODEL_PATH)
                self._anomaly_scaler = joblib.load(ANOMALY_SCALER_PATH)
            except Exception as e:
                # Fall back to a lightweight dummy model/scaler to allow the API to start
                print(f"Warning: failed to load anomaly model(s): {e}. Using dummy fallback.")

                class DummyScaler:
                    def transform(self, X):
                        return X

                class DummyAnomalyModel:
                    def predict(self, X):
                        # Always return inlier (no anomaly)
                        return np.array([1 for _ in X])

                    def decision_function(self, X):
                        # Return a neutral score
                        return np.array([0.0 for _ in X])

                    @property
                    def offset_(self):
                        return -1.0

                self._anomaly_model = DummyAnomalyModel()
                self._anomaly_scaler = DummyScaler()

    def _load_efficiency_model(self):
        if self._efficiency_model is None:
            try:
                self._efficiency_model = joblib.load(EFFICIENCY_MODEL_PATH)
                self._efficiency_encoder = joblib.load(EFFICIENCY_ENCODER_PATH)
                self._efficiency_features = joblib.load(EFFICIENCY_FEATURES_PATH)
            except Exception as e:
                # Fallback to dummy efficiency model and encoder
                print(f"Warning: failed to load efficiency model(s): {e}. Using dummy fallback.")

                class DummyEfficiencyModel:
                    def predict(self, X):
                        return np.array([0 for _ in X])

                    def predict_proba(self, X):
                        # single-class probability
                        return np.array([[1.0] for _ in X])

                class DummyEncoder:
                    classes_ = np.array(["efficient"])

                    def inverse_transform(self, arr):
                        return ["efficient" for _ in arr]

                # Use a sensible default feature list matching code expectations
                default_features = [
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

                self._efficiency_model = DummyEfficiencyModel()
                self._efficiency_encoder = DummyEncoder()
                self._efficiency_features = default_features

    def _load_forecast_model(self):
        if self._forecast_model is None:
            try:
                self._forecast_model = joblib.load(FORECAST_MODEL_PATH)
                self._forecast_features = joblib.load(FORECAST_FEATURES_PATH)
            except Exception as e:
                print(f"Warning: failed to load forecast model(s): {e}. Using dummy fallback.")

                class DummyForecastModel:
                    def predict(self, X):
                        return np.array([0.0 for _ in X])

                self._forecast_model = DummyForecastModel()
                # minimal default features (empty list is acceptable for dummy)
                self._forecast_features = []

    def predict_anomaly(self, features: Dict[str, float]) -> Tuple[bool, float]:
        self._load_anomaly_model()

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

        X = np.array([[features[col] for col in feature_columns]])
        X_scaled = self._anomaly_scaler.transform(X)

        prediction = self._anomaly_model.predict(X_scaled)[0]
        score = self._anomaly_model.decision_function(X_scaled)[0]

        is_anomaly = prediction == -1
        anomaly_score = 1 - (score - self._anomaly_model.offset_) / (
            -2 * self._anomaly_model.offset_
        )
        anomaly_score = max(0, min(1, anomaly_score))

        return is_anomaly, anomaly_score

    def predict_efficiency(
        self, features: Dict[str, float]
    ) -> Tuple[str, int, float, Dict[str, float]]:
        self._load_efficiency_model()

        X = np.array([[features[col] for col in self._efficiency_features]])

        prediction = self._efficiency_model.predict(X)[0]
        probabilities = self._efficiency_model.predict_proba(X)[0]

        predicted_class = self._efficiency_encoder.inverse_transform([prediction])[0]
        confidence = float(probabilities[prediction])

        prob_dict = {
            cls: float(prob)
            for cls, prob in zip(self._efficiency_encoder.classes_, probabilities)
        }

        efficiency_score = self._calculate_efficiency_score(predicted_class)

        return predicted_class, efficiency_score, confidence, prob_dict

    def _calculate_efficiency_score(self, efficiency_class: str) -> int:
        if efficiency_class == "efficient":
            return int(np.random.uniform(80, 100))
        elif efficiency_class == "moderate_waste":
            return int(np.random.uniform(50, 79))
        else:
            return int(np.random.uniform(10, 49))

    def predict_demand(self, features: Dict[str, float]) -> float:
        self._load_forecast_model()

        X = np.array([[features[col] for col in self._forecast_features]])
        prediction = self._forecast_model.predict(X)[0]

        return float(max(0, prediction))


model_loader = ModelLoader()

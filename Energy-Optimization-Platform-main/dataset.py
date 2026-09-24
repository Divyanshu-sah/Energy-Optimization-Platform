"""
EnergiX Copilot - Synthetic Industrial Energy Dataset Generator
"""

import argparse
import math
import random
import warnings
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

MACHINE_TYPES = {
    "compressor": {
        "rated_power_kw": (75, 150),
        "normal_load_pct": (60, 85),
        "efficiency_baseline": 0.85,
        "temp_sensitivity": 0.02,
        "vibration_normal": (1.5, 3.0),
        "output_per_load": 2.5,
    },
    "conveyor_motor": {
        "rated_power_kw": (15, 45),
        "normal_load_pct": (50, 80),
        "efficiency_baseline": 0.90,
        "temp_sensitivity": 0.01,
        "vibration_normal": (2.0, 4.0),
        "output_per_load": 1.2,
    },
    "cooling_unit": {
        "rated_power_kw": (30, 90),
        "normal_load_pct": (40, 70),
        "efficiency_baseline": 0.75,
        "temp_sensitivity": 0.05,
        "vibration_normal": (1.0, 2.5),
        "output_per_load": 1.8,
    },
    "packaging_machine": {
        "rated_power_kw": (10, 30),
        "normal_load_pct": (65, 90),
        "efficiency_baseline": 0.92,
        "temp_sensitivity": 0.005,
        "vibration_normal": (0.5, 1.5),
        "output_per_load": 3.0,
    },
    "cnc_machine": {
        "rated_power_kw": (20, 60),
        "normal_load_pct": (55, 85),
        "efficiency_baseline": 0.88,
        "temp_sensitivity": 0.015,
        "vibration_normal": (1.0, 2.0),
        "output_per_load": 2.2,
    },
}

SHIFTS = {"morning": (6, 14), "evening": (14, 22), "night": (22, 6)}
SHIFT_NAMES = list(SHIFTS.keys())
PEAK_TARIFF_HOURS = (17, 20)

ANOMALY_SCENARIOS = {
    "idle_waste": 0.08,
    "overload_spike": 0.05,
    "gradual_drift": 0.10,
    "temp_overconsumption": 0.06,
    "maintenance_degradation": 0.04,
    "underutilized": 0.07,
    "peak_demand": 0.03,
}


@dataclass
class MachineMetadata:
    machine_id: str
    machine_type: str
    plant_id: str
    zone_id: str
    rated_power_kw: float
    normal_load_min: float
    normal_load_max: float
    efficiency_baseline: float
    temp_sensitivity: float
    vibration_normal_min: float
    vibration_normal_max: float
    output_per_load: float
    shift_preference: str


@dataclass
class PlantConfig:
    plant_id: str
    num_zones: int
    machines_per_zone: Dict[str, int]


def generate_metadata(plants: List[PlantConfig], output_dir: Path) -> pd.DataFrame:
    records = []
    machine_counter = 1
    for plant in plants:
        for zone_idx in range(1, plant.num_zones + 1):
            zone_id = f"{plant.plant_id}_Z{zone_idx:02d}"
            for machine_type, count in plant.machines_per_zone.items():
                params = MACHINE_TYPES[machine_type]
                for _ in range(count):
                    if machine_type in ["compressor", "cooling_unit"]:
                        shift_pref = "night"
                    elif machine_type in ["cnc_machine"]:
                        shift_pref = "evening"
                    else:
                        shift_pref = random.choice(["morning", "evening"])
                    rated_power = np.random.uniform(*params["rated_power_kw"])
                    normal_load_min, normal_load_max = params["normal_load_pct"]
                    efficiency_baseline = params[
                        "efficiency_baseline"
                    ] * np.random.uniform(0.95, 1.05)
                    records.append(
                        {
                            "machine_id": f"M{machine_counter:04d}",
                            "machine_type": machine_type,
                            "plant_id": plant.plant_id,
                            "zone_id": zone_id,
                            "rated_power_kw": rated_power,
                            "normal_load_min": normal_load_min,
                            "normal_load_max": normal_load_max,
                            "efficiency_baseline": efficiency_baseline,
                            "temp_sensitivity": params["temp_sensitivity"],
                            "vibration_normal_min": params["vibration_normal"][0],
                            "vibration_normal_max": params["vibration_normal"][1],
                            "output_per_load": params["output_per_load"],
                            "shift_preference": shift_pref,
                        }
                    )
                    machine_counter += 1
    df = pd.DataFrame(records)
    df.to_csv(output_dir / "machine_metadata.csv", index=False)
    df.to_parquet(output_dir / "machine_metadata.parquet", index=False)
    print(f"Generated metadata for {len(df)} machines")
    return df


def get_shift_id(timestamp: datetime) -> str:
    hour = timestamp.hour
    if SHIFTS["morning"][0] <= hour < SHIFTS["morning"][1]:
        return "morning"
    elif SHIFTS["evening"][0] <= hour < SHIFTS["evening"][1]:
        return "evening"
    else:
        return "night"


def compute_baseline_power(machine: MachineMetadata, load_percent: float) -> float:
    """Compute expected power draw based on load and rated power."""
    if load_percent <= 0:
        return 0.0
    raw_power = machine.rated_power_kw * (load_percent / 100.0) ** 1.2
    efficiency_factor = 1.0 / machine.efficiency_baseline
    return raw_power * efficiency_factor


def compute_efficiency_score(
    power_kw: float,
    output_units: float,
    baseline_power: float,
    idle_energy_ratio: float,
    load_percent: float,
    temperature_c: float,
    vibration_mm_s: float,
    machine: MachineMetadata,
) -> float:
    score = 100.0
    if output_units > 0:
        energy_per_unit = power_kw / output_units
        expected_epu = baseline_power / (
            machine.output_per_load * (load_percent / 100.0) + 1e-6
        )
        ratio = energy_per_unit / expected_epu
        if ratio > 1:
            score -= min(30, (ratio - 1) * 50)
    if baseline_power > 0:
        dev_pct = abs(power_kw - baseline_power) / baseline_power * 100
        score -= min(25, dev_pct * 0.8)
    if output_units < 0.1 * machine.output_per_load:
        score -= min(20, idle_energy_ratio * 100)
    normal_load_min = machine.normal_load_min
    normal_load_max = machine.normal_load_max
    if load_percent < normal_load_min:
        penalty = (normal_load_min - load_percent) * 0.5
        score -= min(15, penalty)
    elif load_percent > normal_load_max:
        penalty = (load_percent - normal_load_max) * 0.6
        score -= min(20, penalty)
    temp_penalty = max(0, (temperature_c - 45)) * 1.5
    score -= min(10, temp_penalty)
    vib_penalty = max(0, (vibration_mm_s - machine.vibration_normal_max)) * 5
    score -= min(10, vib_penalty)
    return max(0, min(100, score))


def classify_efficiency(score: float) -> str:
    if score >= 80:
        return "efficient"
    elif score >= 50:
        return "moderate_waste"
    else:
        return "severe_waste"


def get_recommendation(
    anomaly_flag: bool,
    anomaly_type: Optional[str],
    efficiency_class: str,
    load_percent: float,
    runtime_state: str,
    temperature_c: float,
    vibration_mm_s: float,
    machine: MachineMetadata,
) -> str:
    if anomaly_flag:
        if anomaly_type == "idle_waste":
            return "shutdown_idle_machine"
        elif anomaly_type == "overload_spike":
            return "redistribute_load"
        elif anomaly_type == "gradual_drift":
            return "schedule_maintenance"
        elif anomaly_type == "temp_overconsumption":
            return "inspect_cooling"
        elif anomaly_type == "maintenance_degradation":
            return "schedule_maintenance"
        elif anomaly_type == "underutilized":
            return "optimize_shift_schedule"
        elif anomaly_type == "peak_demand":
            return "reduce_peak_load"
        else:
            return "schedule_inspection"
    else:
        if efficiency_class == "severe_waste":
            return "schedule_maintenance"
        elif efficiency_class == "moderate_waste":
            return "optimize_operation"
        else:
            return "normal_operation"


def apply_idle_waste(row: Dict, machine: MachineMetadata) -> Dict:
    if row["runtime_state"] == "idle":
        row["power_kw"] = row["baseline_power_kw"] * np.random.uniform(0.6, 0.9)
        row["idle_energy_ratio"] = row["power_kw"] / (row["baseline_power_kw"] + 1e-6)
        row["anomaly_flag"] = 1
        row["anomaly_type"] = "idle_waste"
    return row


def apply_overload_spike(row: Dict, machine: MachineMetadata) -> Dict:
    row["load_percent"] = min(120, row["load_percent"] * np.random.uniform(1.5, 2.0))
    row["power_kw"] = compute_baseline_power(machine, row["load_percent"])
    row["current_a"] = (
        row["power_kw"] * 1000 / (row["voltage_v"] * row["power_factor"] + 1e-6)
    )
    row["temperature_c"] += np.random.uniform(5, 12)
    row["vibration_mm_s"] += np.random.uniform(2, 5)
    row["anomaly_flag"] = 1
    row["anomaly_type"] = "overload_spike"
    return row


def apply_gradual_drift(
    row: Dict, machine: MachineMetadata, drift_factor: float
) -> Dict:
    row["power_kw"] = row["baseline_power_kw"] * (1 + drift_factor)
    row["power_deviation_percent"] = drift_factor * 100
    row["anomaly_flag"] = 1
    row["anomaly_type"] = "gradual_drift"
    return row


def apply_temp_overconsumption(row: Dict, machine: MachineMetadata) -> Dict:
    temp_excess = max(0, row["ambient_temperature_c"] - 30)
    extra_power = row["baseline_power_kw"] * machine.temp_sensitivity * temp_excess
    row["power_kw"] += extra_power
    row["temperature_c"] += temp_excess * 0.5
    row["anomaly_flag"] = 1
    row["anomaly_type"] = "temp_overconsumption"
    return row


def apply_maintenance_degradation(
    row: Dict, machine: MachineMetadata, deg_factor: float
) -> Dict:
    row["vibration_mm_s"] *= 1 + deg_factor * 2
    row["power_kw"] *= 1 + deg_factor * 0.3
    row["anomaly_flag"] = 1
    row["anomaly_type"] = "maintenance_degradation"
    return row


def apply_underutilized(row: Dict, machine: MachineMetadata) -> Dict:
    row["output_units"] *= np.random.uniform(0.3, 0.6)
    row["utilization_percent"] = (row["load_percent"] / 100) * 100
    row["anomaly_flag"] = 1
    row["anomaly_type"] = "underutilized"
    return row


def generate_telemetry(
    machine_metadata: pd.DataFrame,
    start_date: datetime,
    num_days: int,
    interval_minutes: int,
    output_dir: Path,
) -> pd.DataFrame:
    timestamps = []
    current = start_date
    end_date = start_date + timedelta(days=num_days)
    while current < end_date:
        timestamps.append(current)
        current += timedelta(minutes=interval_minutes)

    records = []
    drift_state = {mid: 0.0 for mid in machine_metadata["machine_id"]}
    maintenance_state = {mid: 0.0 for mid in machine_metadata["machine_id"]}
    anomaly_schedule = {}
    for _, mach in machine_metadata.iterrows():
        mid = mach["machine_id"]
        anomaly_schedule[mid] = {}
        for scenario in ANOMALY_SCENARIOS:
            if scenario == "peak_demand":
                continue
            prob = ANOMALY_SCENARIOS[scenario]
            days_with_anomaly = set()
            for day in range(num_days):
                if np.random.random() < prob:
                    days_with_anomaly.add(day)
            anomaly_schedule[mid][scenario] = days_with_anomaly

    total_steps = len(timestamps) * len(machine_metadata)
    step = 0

    for ts in timestamps:
        shift_id = get_shift_id(ts)
        day_of_week = ts.weekday()
        hour = ts.hour
        is_weekend = day_of_week >= 5
        peak_tariff = 1 if PEAK_TARIFF_HOURS[0] <= hour < PEAK_TARIFF_HOURS[1] else 0

        for _, mach in machine_metadata.iterrows():
            step += 1
            if step % 50000 == 0:
                print(f"Generating telemetry... {step / total_steps * 100:.1f}%")

            mid = mach["machine_id"]
            machine_obj = MachineMetadata(
                machine_id=mid,
                machine_type=mach["machine_type"],
                plant_id=mach["plant_id"],
                zone_id=mach["zone_id"],
                rated_power_kw=mach["rated_power_kw"],
                normal_load_min=mach["normal_load_min"],
                normal_load_max=mach["normal_load_max"],
                efficiency_baseline=mach["efficiency_baseline"],
                temp_sensitivity=mach["temp_sensitivity"],
                vibration_normal_min=mach["vibration_normal_min"],
                vibration_normal_max=mach["vibration_normal_max"],
                output_per_load=mach["output_per_load"],
                shift_preference=mach["shift_preference"],
            )

            active = False
            if mach["shift_preference"] == shift_id:
                active = True
            elif mach["shift_preference"] == "night" and shift_id == "night":
                active = True
            elif is_weekend and shift_id in ["morning", "evening"]:
                active = np.random.random() < 0.5
            else:
                active = False

            if not active:
                runtime_state = "off"
                load_percent = 0.0
                output_units = 0.0
                temperature_c = 20 + np.random.normal(0, 2)
                vibration_mm_s = 0.1
            else:
                base_load = np.random.uniform(
                    mach["normal_load_min"], mach["normal_load_max"]
                )
                time_factor = 1.0 + 0.1 * np.sin(2 * np.pi * (hour - 12) / 24)
                load_percent = min(100, base_load * time_factor)
                if np.random.random() < 0.05:
                    load_percent *= np.random.uniform(0.9, 1.1)
                load_percent = max(0, min(100, load_percent))
                runtime_state = "active"
                output_units = (
                    machine_obj.output_per_load
                    * (load_percent / 100.0)
                    * np.random.uniform(0.95, 1.05)
                )
                temperature_c = 25 + (load_percent / 100) * 15 + np.random.normal(0, 2)
                vibration_mm_s = np.random.uniform(
                    machine_obj.vibration_normal_min, machine_obj.vibration_normal_max
                )

            day_of_year = ts.timetuple().tm_yday
            seasonal_temp = 15 + 10 * np.sin(2 * np.pi * day_of_year / 365)
            daily_temp = 5 * np.sin(2 * np.pi * (hour - 14) / 24)
            ambient_temperature_c = seasonal_temp + daily_temp + np.random.normal(0, 1)

            baseline_power = compute_baseline_power(machine_obj, load_percent)
            if baseline_power > 0:
                power_kw = baseline_power * np.random.normal(1, 0.03)
            else:
                power_kw = 0.0

            power_factor = np.random.uniform(0.8, 0.95)
            voltage_v = np.random.normal(400, 5)
            if voltage_v > 0 and power_factor > 0:
                current_a = power_kw * 1000 / (voltage_v * power_factor + 1e-6)
            else:
                current_a = 0.0
            interval_hours = interval_minutes / 60.0
            energy_kwh_interval = power_kw * interval_hours

            if output_units > 0:
                cycle_time_sec = 3600 * interval_hours / output_units
            else:
                cycle_time_sec = 0

            utilization_percent = (
                (load_percent / 100) * 100 if runtime_state == "active" else 0
            )
            energy_per_unit = power_kw / output_units if output_units > 0 else 0
            idle_energy_ratio = (
                power_kw / (baseline_power + 1e-6) if runtime_state == "idle" else 0
            )
            if baseline_power > 0:
                power_deviation_percent = (
                    (power_kw - baseline_power) / baseline_power * 100
                )
            else:
                power_deviation_percent = 0.0

            anomaly_flag = 0
            anomaly_type = None

            day_index = (ts - start_date).days
            for scenario, days_set in anomaly_schedule[mid].items():
                if day_index in days_set:
                    if scenario == "idle_waste" and runtime_state == "idle":
                        row_dict = {
                            "runtime_state": runtime_state,
                            "power_kw": power_kw,
                            "baseline_power_kw": baseline_power,
                            "idle_energy_ratio": idle_energy_ratio,
                        }
                        row_dict = apply_idle_waste(row_dict, machine_obj)
                        power_kw = row_dict["power_kw"]
                        idle_energy_ratio = row_dict["idle_energy_ratio"]
                        anomaly_flag = 1
                        anomaly_type = "idle_waste"
                    elif scenario == "overload_spike" and runtime_state == "active":
                        row_dict = {
                            "load_percent": load_percent,
                            "power_kw": power_kw,
                            "current_a": current_a,
                            "voltage_v": voltage_v,
                            "power_factor": power_factor,
                            "temperature_c": temperature_c,
                            "vibration_mm_s": vibration_mm_s,
                        }
                        row_dict = apply_overload_spike(row_dict, machine_obj)
                        load_percent = row_dict["load_percent"]
                        power_kw = row_dict["power_kw"]
                        current_a = row_dict["current_a"]
                        temperature_c = row_dict["temperature_c"]
                        vibration_mm_s = row_dict["vibration_mm_s"]
                        anomaly_flag = 1
                        anomaly_type = "overload_spike"
                    elif scenario == "gradual_drift":
                        drift_state[mid] = min(0.3, drift_state[mid] + 0.005)
                        row_dict = {
                            "baseline_power_kw": baseline_power,
                            "power_kw": power_kw,
                            "power_deviation_percent": power_deviation_percent,
                        }
                        row_dict = apply_gradual_drift(
                            row_dict, machine_obj, drift_state[mid]
                        )
                        power_kw = row_dict["power_kw"]
                        power_deviation_percent = row_dict["power_deviation_percent"]
                        anomaly_flag = 1
                        anomaly_type = "gradual_drift"
                    elif scenario == "temp_overconsumption":
                        row_dict = {
                            "baseline_power_kw": baseline_power,
                            "power_kw": power_kw,
                            "temperature_c": temperature_c,
                            "ambient_temperature_c": ambient_temperature_c,
                        }
                        row_dict = apply_temp_overconsumption(row_dict, machine_obj)
                        power_kw = row_dict["power_kw"]
                        temperature_c = row_dict["temperature_c"]
                        anomaly_flag = 1
                        anomaly_type = "temp_overconsumption"
                    elif scenario == "maintenance_degradation":
                        maintenance_state[mid] = min(0.4, maintenance_state[mid] + 0.01)
                        row_dict = {
                            "vibration_mm_s": vibration_mm_s,
                            "power_kw": power_kw,
                        }
                        row_dict = apply_maintenance_degradation(
                            row_dict, machine_obj, maintenance_state[mid]
                        )
                        vibration_mm_s = row_dict["vibration_mm_s"]
                        power_kw = row_dict["power_kw"]
                        anomaly_flag = 1
                        anomaly_type = "maintenance_degradation"
                    elif scenario == "underutilized" and runtime_state == "active":
                        row_dict = {
                            "output_units": output_units,
                            "load_percent": load_percent,
                            "utilization_percent": utilization_percent,
                        }
                        row_dict = apply_underutilized(row_dict, machine_obj)
                        output_units = row_dict["output_units"]
                        utilization_percent = row_dict["utilization_percent"]
                        anomaly_flag = 1
                        anomaly_type = "underutilized"

            efficiency_score = compute_efficiency_score(
                power_kw,
                output_units,
                baseline_power,
                idle_energy_ratio,
                load_percent,
                temperature_c,
                vibration_mm_s,
                machine_obj,
            )
            efficiency_class = classify_efficiency(efficiency_score)
            inefficiency_flag = 1 if efficiency_class != "efficient" else 0
            inefficiency_type = efficiency_class if inefficiency_flag else "none"

            recommendation = get_recommendation(
                anomaly_flag,
                anomaly_type,
                efficiency_class,
                load_percent,
                runtime_state,
                temperature_c,
                vibration_mm_s,
                machine_obj,
            )

            record = {
                "timestamp": ts,
                "plant_id": mach["plant_id"],
                "zone_id": mach["zone_id"],
                "machine_id": mid,
                "machine_type": mach["machine_type"],
                "shift_id": shift_id,
                "voltage_v": voltage_v,
                "current_a": current_a,
                "power_kw": power_kw,
                "energy_kwh_interval": energy_kwh_interval,
                "power_factor": power_factor,
                "runtime_state": runtime_state,
                "load_percent": load_percent,
                "output_units": output_units,
                "cycle_time_sec": cycle_time_sec,
                "utilization_percent": utilization_percent,
                "temperature_c": temperature_c,
                "vibration_mm_s": vibration_mm_s,
                "ambient_temperature_c": ambient_temperature_c,
                "humidity_percent": np.random.uniform(30, 70),
                "energy_per_unit": energy_per_unit,
                "idle_energy_ratio": idle_energy_ratio,
                "baseline_power_kw": baseline_power,
                "power_deviation_percent": power_deviation_percent,
                "anomaly_flag": anomaly_flag,
                "anomaly_type": anomaly_type if anomaly_flag else "none",
                "inefficiency_flag": inefficiency_flag,
                "inefficiency_type": inefficiency_type,
                "efficiency_score": efficiency_score,
                "efficiency_class": efficiency_class,
                "predicted_recommendation_category": recommendation,
                "peak_tariff_flag": peak_tariff,
                "hour_of_day": hour,
                "day_of_week": day_of_week,
                "weekend_flag": is_weekend,
            }
            records.append(record)

    df = pd.DataFrame(records)
    df.to_csv(output_dir / "telemetry_machine_level.csv", index=False)
    df.to_parquet(output_dir / "telemetry_machine_level.parquet", index=False)
    print(f"Generated {len(df)} telemetry records")
    return df


def generate_plant_demand(telemetry_df: pd.DataFrame, output_dir: Path) -> pd.DataFrame:
    plant_df = (
        telemetry_df.groupby(["timestamp", "plant_id"])
        .agg(
            plant_total_power_kw=("power_kw", "sum"),
            plant_total_output_units=("output_units", "sum"),
            avg_load_percent=("load_percent", "mean"),
            num_active_machines=("runtime_state", lambda x: (x == "active").sum()),
            num_anomalies=("anomaly_flag", "sum"),
        )
        .reset_index()
    )
    plant_df["hour_of_day"] = plant_df["timestamp"].dt.hour
    plant_df["day_of_week"] = plant_df["timestamp"].dt.dayofweek
    plant_df["weekend_flag"] = plant_df["day_of_week"] >= 5
    plant_df["peak_tariff_flag"] = (
        plant_df["hour_of_day"]
        .between(PEAK_TARIFF_HOURS[0], PEAK_TARIFF_HOURS[1] - 1)
        .astype(int)
    )
    plant_df["demand_window_id"] = (
        plant_df["timestamp"].dt.floor("15min").astype("int64") // 1e9
    )
    plant_df = plant_df.sort_values(["plant_id", "timestamp"])
    plant_df.to_csv(output_dir / "plant_demand_timeseries.csv", index=False)
    plant_df.to_parquet(output_dir / "plant_demand_timeseries.parquet", index=False)
    print(f"Generated plant demand: {len(plant_df)} records")
    return plant_df


def build_efficiency_training_dataset(
    telemetry_df: pd.DataFrame, output_dir: Path
) -> pd.DataFrame:
    feature_cols = [
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
    target_cols = [
        "efficiency_score",
        "efficiency_class",
        "inefficiency_flag",
        "inefficiency_type",
    ]
    keep_cols = (
        feature_cols
        + target_cols
        + ["timestamp", "machine_id", "machine_type", "plant_id"]
    )
    df = telemetry_df[keep_cols].copy()
    df.to_csv(output_dir / "training_dataset_efficiency.csv", index=False)
    df.to_parquet(output_dir / "training_dataset_efficiency.parquet", index=False)
    print(f"Efficiency training dataset: {len(df)} rows")
    return df


def build_forecast_training_dataset(
    plant_df: pd.DataFrame, output_dir: Path
) -> pd.DataFrame:
    df = plant_df.copy()
    df = df.sort_values(["plant_id", "timestamp"])
    for lag in [1, 2, 3, 6, 12, 24]:
        df[f"lag_{lag}_power_kw"] = df.groupby("plant_id")[
            "plant_total_power_kw"
        ].shift(lag)
    df["rolling_mean_6"] = df.groupby("plant_id")["plant_total_power_kw"].transform(
        lambda x: x.rolling(6, min_periods=1).mean()
    )
    df["rolling_std_6"] = df.groupby("plant_id")["plant_total_power_kw"].transform(
        lambda x: x.rolling(6, min_periods=1).std()
    )
    df["target_next_power_kw"] = df.groupby("plant_id")["plant_total_power_kw"].shift(
        -1
    )
    df_clean = df.dropna().copy()
    df_clean.to_csv(output_dir / "training_dataset_forecast.csv", index=False)
    df_clean.to_parquet(output_dir / "training_dataset_forecast.parquet", index=False)
    print(f"Forecast training dataset: {len(df_clean)} rows")
    return df_clean


def build_anomaly_reference_datasets(telemetry_df: pd.DataFrame, output_dir: Path):
    anomalies = telemetry_df[telemetry_df["anomaly_flag"] == 1].copy()
    anomalies.to_csv(output_dir / "anomalies_only.csv", index=False)
    anomalies.to_parquet(output_dir / "anomalies_only.parquet", index=False)
    print(f"Anomalies only: {len(anomalies)} records")
    rec_df = telemetry_df[
        [
            "timestamp",
            "machine_id",
            "efficiency_class",
            "predicted_recommendation_category",
            "anomaly_type",
        ]
    ].copy()
    rec_df.to_csv(output_dir / "recommendations_reference.csv", index=False)
    rec_df.to_parquet(output_dir / "recommendations_reference.parquet", index=False)
    print(f"Recommendations reference: {len(rec_df)} records")


def validate_data(df_dict: Dict[str, pd.DataFrame], output_dir: Path):
    print("\n=== Data Validation ===")
    for name, df in df_dict.items():
        print(f"\n{name}: {len(df)} rows, {len(df.columns)} columns")
        if "timestamp" in df.columns:
            print(f"  Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        if "anomaly_flag" in df.columns:
            anomaly_rate = df["anomaly_flag"].mean() * 100
            print(f"  Anomaly rate: {anomaly_rate:.2f}%")
        if "efficiency_score" in df.columns:
            print(
                f"  Efficiency score: mean={df['efficiency_score'].mean():.1f}, min={df['efficiency_score'].min():.1f}, max={df['efficiency_score'].max():.1f}"
            )
        if "efficiency_class" in df.columns:
            print(
                f"  Efficiency classes: {df['efficiency_class'].value_counts().to_dict()}"
            )
    report_path = output_dir / "validation_report.txt"
    with open(report_path, "w") as f:
        f.write("EnergiX Copilot - Synthetic Dataset Validation Report\n")
        f.write("=" * 60 + "\n")
        for name, df in df_dict.items():
            f.write(f"\n{name}:\n")
            f.write(f"  Rows: {len(df)}\n")
            f.write(f"  Columns: {list(df.columns)}\n")
            if "timestamp" in df.columns:
                f.write(
                    f"  Time range: {df['timestamp'].min()} to {df['timestamp'].max()}\n"
                )
    print(f"\nValidation report saved to {report_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic industrial energy dataset for EnergiX Copilot"
    )
    parser.add_argument("--plants", type=int, default=1, help="Number of plants")
    parser.add_argument(
        "--zones_per_plant", type=int, default=2, help="Zones per plant"
    )
    parser.add_argument(
        "--machines_per_zone",
        type=str,
        default="compressor:1,conveyor_motor:2,cooling_unit:1,packaging_machine:2,cnc_machine:1",
        help="Comma-separated machine_type:count pairs",
    )
    parser.add_argument(
        "--start_date", type=str, default="2024-01-01", help="Start date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--days", type=int, default=14, help="Number of days to generate"
    )
    parser.add_argument(
        "--interval_minutes", type=int, default=5, help="Sampling interval in minutes"
    )
    parser.add_argument(
        "--output_dir", type=str, default="./data/synthetic", help="Output directory"
    )
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="Random seed")
    args = parser.parse_args()

    np.random.seed(args.seed)
    random.seed(args.seed)

    machines_per_zone = {}
    for item in args.machines_per_zone.split(","):
        mtype, count = item.split(":")
        machines_per_zone[mtype] = int(count)

    output_path = Path(args.output_dir)
    raw_path = output_path / "raw"
    processed_path = output_path / "processed"
    for p in [raw_path, processed_path]:
        p.mkdir(parents=True, exist_ok=True)

    print(f"Generating dataset with seed={args.seed}")
    print(f"Plants: {args.plants}, Zones per plant: {args.zones_per_plant}")
    print(f"Machines per zone: {machines_per_zone}")
    print(
        f"Period: {args.days} days from {args.start_date}, interval {args.interval_minutes} min"
    )

    plants = []
    for i in range(1, args.plants + 1):
        plant = PlantConfig(
            plant_id=f"P{i:02d}",
            num_zones=args.zones_per_plant,
            machines_per_zone=machines_per_zone.copy(),
        )
        plants.append(plant)

    print("\n=== Generating Machine Metadata ===")
    metadata_df = generate_metadata(plants, raw_path)

    print("\n=== Generating Telemetry Data ===")
    start_dt = datetime.strptime(args.start_date, "%Y-%m-%d")
    telemetry_df = generate_telemetry(
        metadata_df, start_dt, args.days, args.interval_minutes, raw_path
    )

    print("\n=== Aggregating Plant Demand ===")
    plant_df = generate_plant_demand(telemetry_df, processed_path)

    print("\n=== Building ML Training Datasets ===")
    efficiency_df = build_efficiency_training_dataset(telemetry_df, processed_path)
    forecast_df = build_forecast_training_dataset(plant_df, processed_path)
    build_anomaly_reference_datasets(telemetry_df, processed_path)

    all_dfs = {
        "machine_metadata": metadata_df,
        "telemetry_machine_level": telemetry_df,
        "plant_demand_timeseries": plant_df,
        "training_dataset_efficiency": efficiency_df,
        "training_dataset_forecast": forecast_df,
    }
    validate_data(all_dfs, output_path)

    print("\n✅ Dataset generation complete!")
    print(f"All outputs saved to {output_path.absolute()}")
    print("\nSample of telemetry data:")
    print(telemetry_df.head(10).to_string())
    print("\nSample of plant demand:")
    print(plant_df.head(10).to_string())


if __name__ == "__main__":
    main()

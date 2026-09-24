import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Optional
import uuid
import time
import csv
import os
import threading

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import joblib
from config import (
    TELEMETRY_DATA_PATH,
    MACHINE_METADATA_PATH,
    ANOMALY_MODEL_PATH,
    ANOMALY_SCALER_PATH,
    EFFICIENCY_MODEL_PATH,
    EFFICIENCY_ENCODER_PATH,
    EFFICIENCY_FEATURES_PATH,
    FORECAST_MODEL_PATH,
    FORECAST_FEATURES_PATH,
)
from models import model_loader

app = FastAPI(
    title="EnergiX Copilot API",
    description="Industrial Energy Optimization Platform API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve a lightweight static UI so the app can be demoed without Node/npm
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

_models_loaded = False
_data_loaded = False
_machines_cache = []
_cache_timestamp = 0
CACHE_TTL = 60

# Live telemetry from simulator
_realtime_telemetry = {}
_telemetry_lock = threading.Lock()

LIVE_DATA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "live_data"
)
os.makedirs(LIVE_DATA_DIR, exist_ok=True)
_live_csv_path = os.path.join(LIVE_DATA_DIR, "live_telemetry.csv")

machines_df = None
telemetry_df = None


def load_models():
    model_loader.load_all_models()


def load_data():
    global machines_df, telemetry_df
    try:
        machines_df = pd.read_csv(MACHINE_METADATA_PATH)
    except Exception as e:
        print(f"Error loading machine metadata: {e}")
        machines_df = None
    try:
        telemetry_df = pd.read_csv(TELEMETRY_DATA_PATH)
        telemetry_df["timestamp"] = pd.to_datetime(telemetry_df["timestamp"])
    except FileNotFoundError:
        telemetry_df = None
    except pd.errors.EmptyDataError:
        telemetry_df = None
    except Exception as e:
        print(f"Error loading telemetry data: {e}")
        telemetry_df = None


def get_cached_machines():
    global _machines_cache, _cache_timestamp
    now = time.time()
    if now - _cache_timestamp < CACHE_TTL and len(_machines_cache) > 0:
        return _machines_cache
    machines = generate_all_machines()
    _machines_cache = machines
    _cache_timestamp = now
    return machines


def predict_anomaly(features: dict) -> tuple:
    return model_loader.predict_anomaly(features)


def predict_efficiency(features: dict) -> tuple:
    return model_loader.predict_efficiency(features)


def _build_machine_entry(
    machine_id,
    row,
    power,
    load,
    temp,
    voltage,
    current,
    power_factor,
    output_units,
    energy_per_unit,
    utilization,
    idle_ratio,
    power_dev,
    ambient_temp,
    humidity,
    vibration,
    runtime_state,
):
    anomaly_features = {
        "power_kw": power,
        "current_a": current,
        "voltage_v": voltage,
        "load_percent": load,
        "temperature_c": temp,
        "vibration_mm_s": vibration,
        "power_factor": power_factor,
        "energy_per_unit": energy_per_unit,
        "utilization_percent": utilization,
        "power_deviation_percent": power_dev,
        "ambient_temperature_c": ambient_temp,
        "humidity_percent": humidity,
        "idle_energy_ratio": idle_ratio,
    }
    is_anomaly, anomaly_score = predict_anomaly(anomaly_features)
    is_anomaly = bool(is_anomaly)

    efficiency_features = {
        "power_kw": power,
        "load_percent": load,
        "output_units": output_units,
        "temperature_c": temp,
        "vibration_mm_s": vibration,
        "ambient_temperature_c": ambient_temp,
        "humidity_percent": humidity,
        "utilization_percent": utilization,
        "energy_per_unit": energy_per_unit,
        "idle_energy_ratio": idle_ratio,
        "power_deviation_percent": power_dev,
        "hour_of_day": datetime.now().hour,
        "day_of_week": datetime.now().weekday(),
        "weekend_flag": 1 if datetime.now().weekday() >= 5 else 0,
    }
    eff_class, eff_score, confidence, prob_dict = predict_efficiency(
        efficiency_features
    )

    if is_anomaly and anomaly_score > 0.7:
        status = "critical" if anomaly_score > 0.85 else "warning"
    elif eff_class == "efficient":
        status = "efficient"
    elif eff_class == "moderate_waste":
        status = "moderate_waste"
    elif eff_class == "severe_waste":
        status = "severe_waste"
    else:
        status = "normal"

    type_names = {
        "compressor": "Compressor",
        "conveyor_motor": "Conveyor",
        "cooling_unit": "Cooling Unit",
        "packaging_machine": "Packaging Machine",
        "cnc_machine": "CNC Machine",
    }
    type_name = type_names.get(row["machine_type"], row["machine_type"].title())

    return {
        "machine_id": machine_id,
        "name": f"{type_name} {machine_id[-2:]}",
        "type": type_name,
        "plant_id": row["plant_id"],
        "zone_id": row["zone_id"],
        "rated_power_kw": round(row["rated_power_kw"], 2),
        "current_power_kw": round(power, 2),
        "load_percent": round(load, 1),
        "temperature_c": round(temp, 1),
        "runtime_state": runtime_state,
        "efficiency_score": eff_score,
        "efficiency_class": eff_class,
        "anomaly_score": round(anomaly_score, 2),
        "is_anomaly": is_anomaly,
        "predicted_demand_kw": round(power * 1.05, 2),
        "output_rate": int(min(100, output_units / 1.5)),
        "status": status,
    }


def _build_simulator_machine(tel):
    power = float(tel.get("power_kw", 90))
    load = float(tel.get("load_percent", 70))
    temp = float(tel.get("temperature_c", 40))
    voltage = float(tel.get("voltage_v", 400))
    current = float(tel.get("current_a", power * 1000 / (voltage * 0.9)))
    power_factor = float(tel.get("power_factor", 0.9))
    output_units = float(tel.get("output_units", 60))
    utilization = float(tel.get("utilization_percent", 65))
    idle_ratio = 0.1
    power_dev = 5.0
    ambient_temp = 30
    humidity = 60
    vibration = float(tel.get("vibration_mm_s", 2.0))
    runtime_state = str(tel.get("runtime_state", "active"))

    row = {
        "machine_type": "compressor",
        "plant_id": "P01",
        "zone_id": "P01_Z01",
        "rated_power_kw": 150.0,
    }
    energy_per_unit = power / max(output_units, 1)

    entry = _build_machine_entry(
        "SIM_COMP_001",
        row,
        power,
        load,
        temp,
        voltage,
        current,
        power_factor,
        output_units,
        energy_per_unit,
        utilization,
        idle_ratio,
        power_dev,
        ambient_temp,
        humidity,
        vibration,
        runtime_state,
    )
    entry["name"] = "Simulator Compressor 01"
    entry["type"] = "Compressor"
    return entry


def generate_all_machines():
    global machines_df, telemetry_df
    result = []
    latest_telemetry = (
        telemetry_df.groupby("machine_id").last().reset_index()
        if telemetry_df is not None
        else None
    )
    if machines_df is None:
        return result

    for _, row in machines_df.iterrows():
        machine_id = row["machine_id"]
        if (
            latest_telemetry is not None
            and machine_id in latest_telemetry["machine_id"].values
        ):
            tel = latest_telemetry[latest_telemetry["machine_id"] == machine_id].iloc[0]
            power = float(tel.get("power_kw", row["rated_power_kw"] * 0.7))
            load = float(tel.get("load_percent", 60))
            temp = float(tel.get("temperature_c", 50))
            voltage = float(tel.get("voltage_v", 415))
            current = float(tel.get("current_a", power * 1.73 * 1000 / (voltage * 0.9)))
            power_factor = float(tel.get("power_factor", 0.9))
            output_units = float(tel.get("output_units", 100))
            energy_per_unit = float(tel.get("energy_per_unit", 0.5))
            utilization = float(tel.get("utilization_percent", 70))
            idle_ratio = float(tel.get("idle_energy_ratio", 0.1))
            power_dev = float(tel.get("power_deviation_percent", 5))
            ambient_temp = float(tel.get("ambient_temperature_c", 30))
            humidity = float(tel.get("humidity_percent", 60))
            vibration = float(tel.get("vibration_mm_s", 2.0))
            runtime_state = str(tel.get("runtime_state", "active"))
        else:
            rated = row["rated_power_kw"]
            power = rated * np.random.uniform(0.5, 0.85)
            load = np.random.uniform(50, 80)
            temp = np.random.uniform(45, 75)
            voltage = 415
            current = power * 1.73 * 1000 / (voltage * 0.9)
            power_factor = np.random.uniform(0.88, 0.94)
            output_units = np.random.uniform(80, 140)
            energy_per_unit = np.random.uniform(0.4, 0.7)
            utilization = np.random.uniform(60, 85)
            idle_ratio = np.random.uniform(0.08, 0.15)
            power_dev = np.random.uniform(3, 8)
            ambient_temp = 28
            humidity = 55
            vibration = np.random.uniform(1.8, 2.8)
            runtime_state = "active"

        result.append(
            _build_machine_entry(
                machine_id,
                row,
                power,
                load,
                temp,
                voltage,
                current,
                power_factor,
                output_units,
                energy_per_unit,
                utilization,
                idle_ratio,
                power_dev,
                ambient_temp,
                humidity,
                vibration,
                runtime_state,
            )
        )

    # Add simulator machine if live data exists
    with _telemetry_lock:
        if "SIM_COMP_001" in _realtime_telemetry:
            result.append(_build_simulator_machine(_realtime_telemetry["SIM_COMP_001"]))

    return result


@app.on_event("startup")
async def startup_event():
    load_models()
    load_data()


@app.get("/")
async def root():
    # Redirect to the static demo UI
    return RedirectResponse(url="/static/index.html")


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/api/machines")
async def get_machines(plant_id: Optional[str] = None, zone_id: Optional[str] = None):
    machines = get_cached_machines()
    if plant_id:
        machines = [m for m in machines if m["plant_id"] == plant_id]
    if zone_id:
        machines = [m for m in machines if m["zone_id"] == zone_id]
    return machines


@app.get("/api/machines/{machine_id}")
async def get_machine(machine_id: str):
    machines = get_cached_machines()
    for m in machines:
        if m["machine_id"] == machine_id:
            return m
    raise HTTPException(status_code=404, detail="Machine not found")


@app.get("/api/alerts")
async def get_alerts(
    machine_id: Optional[str] = None,
    severity: Optional[str] = None,
    status_filter: Optional[str] = None,
):
    machines = get_cached_machines()
    alerts = []
    for m in machines:
        if machine_id and m["machine_id"] != machine_id:
            continue
        if m["is_anomaly"] and m["anomaly_score"] > 0.5:
            if m["anomaly_score"] > 0.8:
                sev, issue = "critical", "overload_spike"
                msg = f"Critical anomaly on {m['name']}. Immediate attention required."
                action = "Shut down and inspect for mechanical failure."
            elif m["anomaly_score"] > 0.6:
                sev, issue = "warning", "efficiency_drift"
                msg = f"Efficiency degradation detected on {m['name']}."
                action = "Schedule maintenance inspection."
            else:
                sev, issue = "info", "idle_energy_waste"
                msg = f"Minor anomaly on {m['name']}. Monitor closely."
                action = "Continue monitoring."
            if severity and severity != sev:
                continue
            alerts.append(
                {
                    "alert_id": f"ALT-{uuid.uuid4().hex[:6].upper()}",
                    "machine_id": m["machine_id"],
                    "severity": sev,
                    "issue_type": issue,
                    "message": msg,
                    "recommended_action": action,
                    "timestamp": datetime.now().isoformat(),
                    "status": "new",
                }
            )
    return alerts


@app.get("/api/recommendations")
async def get_recommendations(
    machine_id: Optional[str] = None,
    priority: Optional[str] = None,
    status_filter: Optional[str] = None,
):
    machines = get_cached_machines()
    recommendations = []
    for m in machines:
        if machine_id and m["machine_id"] != machine_id:
            continue
        should = False
        if m["efficiency_class"] == "severe_waste" or (
            m["is_anomaly"] and m["anomaly_score"] > 0.75
        ):
            pri, sav, cat = "critical", 22.0, "maintenance"
            title = f"Urgent maintenance for {m['name']}"
            reason = f"Severe efficiency issues (score: {m['efficiency_score']}%)"
            source = "anomaly_model"
            should = True
        elif m["efficiency_class"] == "moderate_waste" or m["is_anomaly"]:
            pri, sav, cat = "high", 15.0, "optimize_operation"
            title = f"Optimize {m['name']} operation"
            reason = f"Efficiency below optimal (score: {m['efficiency_score']}%)"
            source = "efficiency_model"
            should = True
        elif m["load_percent"] < 35:
            pri, sav, cat = "medium", 18.0, "idle_shutdown"
            title = f"Idle shutdown for {m['name']}"
            reason = f"Low load utilization ({m['load_percent']:.0f}%)"
            source = "anomaly_model"
            should = True
        elif m["load_percent"] > 88:
            pri, sav, cat = "medium", 12.0, "load_balancing"
            title = f"Redistribute load from {m['name']}"
            reason = f"High load ({m['load_percent']:.0f}%)"
            source = "efficiency_model"
            should = True
        if should:
            if priority and priority != pri:
                continue
            recommendations.append(
                {
                    "recommendation_id": f"REC-{uuid.uuid4().hex[:6]}",
                    "machine_id": m["machine_id"],
                    "category": cat,
                    "priority": pri,
                    "title": title,
                    "estimated_savings_percent": sav,
                    "reason": reason,
                    "source": source,
                }
            )
    return recommendations[:15]


@app.get("/api/dashboard-summary")
async def get_dashboard_summary():
    machines = get_cached_machines()
    alerts_list = await get_alerts()
    total_power = sum(m["current_power_kw"] for m in machines)
    avg_eff = (
        sum(m["efficiency_score"] for m in machines) / len(machines) if machines else 0
    )
    anomalies = sum(1 for m in machines if m["is_anomaly"])
    critical = sum(1 for a in alerts_list if a["severity"] == "critical")
    now = datetime.now()
    forecast = []
    for i in range(3, 0, -1):
        past = now - timedelta(hours=i)
        val = total_power * np.random.uniform(0.95, 1.05)
        forecast.append(
            {
                "time": past.strftime("%H:%M"),
                "actual": round(val, 2),
                "predicted": round(val * np.random.uniform(0.98, 1.02), 2),
            }
        )
    forecast.append(
        {
            "time": now.strftime("%H:%M"),
            "actual": round(total_power, 2),
            "predicted": round(total_power * 1.01, 2),
        }
    )
    for i in range(1, 5):
        future = now + timedelta(hours=i)
        pf = 1.12 if 14 <= future.hour <= 18 else 1.0
        forecast.append(
            {
                "time": future.strftime("%H:%M"),
                "actual": None,
                "predicted": round(total_power * pf, 2),
            }
        )
    return {
        "total_machines": len(machines),
        "active_machines": sum(1 for m in machines if m["runtime_state"] == "active"),
        "total_power_kw": round(total_power, 2),
        "avg_efficiency": round(avg_eff, 1),
        "anomalies_detected": anomalies,
        "critical_alerts": critical,
        "potential_savings_kwh": round(total_power * 0.10, 2),
        "forecast": {
            "current_demand_kw": round(total_power, 2),
            "predicted_next_hour_kw": round(total_power * 1.08, 2),
            "peak_window": "14:00-18:00" if 10 <= now.hour <= 14 else None,
            "forecast_points": forecast,
        },
        "summary": {
            "source": "ml_models",
            "title": "Operations Summary",
            "summary": f"Monitoring {len(machines)} machines. {anomalies} anomalies detected. {critical} critical alerts.",
        },
    }


@app.get("/api/plants")
async def get_plants():
    machines = get_cached_machines()
    plants = {}
    for m in machines:
        pid = m["plant_id"]
        if pid not in plants:
            plants[pid] = {
                "plant_id": pid,
                "total_machines": 0,
                "total_power_kw": 0,
                "efficiencies": [],
                "anomalies": 0,
            }
        plants[pid]["total_machines"] += 1
        plants[pid]["total_power_kw"] += m["current_power_kw"]
        plants[pid]["efficiencies"].append(m["efficiency_score"])
        if m["is_anomaly"]:
            plants[pid]["anomalies"] += 1
    return [
        {
            "plant_id": pid,
            "total_machines": d["total_machines"],
            "total_power_kw": round(d["total_power_kw"], 2),
            "avg_efficiency": round(sum(d["efficiencies"]) / len(d["efficiencies"]), 1),
            "anomaly_count": d["anomalies"],
        }
        for pid, d in plants.items()
    ]


@app.post("/api/simulate")
async def simulate_scenario(scenario: str = Query(...)):
    global _cache_timestamp
    _cache_timestamp = 0
    return {
        "scenario": scenario,
        "status": "applied",
        "message": f"Scenario '{scenario}' applied",
    }


# ============================================
# TELEMETRY INGEST - Machine Simulator
# ============================================


@app.post("/api/telemetry/ingest")
async def ingest_telemetry(telemetry: dict):
    """Receive telemetry from machine simulator, save to live_data CSV"""
    try:
        required = ["machine_id", "timestamp", "power_kw"]
        for f in required:
            if f not in telemetry:
                raise HTTPException(status_code=400, detail=f"Missing field: {f}")

        machine_id = telemetry["machine_id"]
        telemetry["received_at"] = datetime.now().isoformat()

        with _telemetry_lock:
            _realtime_telemetry[machine_id] = telemetry

        # Append to live CSV
        file_exists = (
            os.path.exists(_live_csv_path) and os.path.getsize(_live_csv_path) > 0
        )
        with open(_live_csv_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(telemetry.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(telemetry)

        global _cache_timestamp
        _cache_timestamp = 0

        return {
            "status": "success",
            "machine_id": machine_id,
            "timestamp": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

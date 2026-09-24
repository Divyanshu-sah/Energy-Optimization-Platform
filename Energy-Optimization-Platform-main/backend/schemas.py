from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class MachineStatus(str, Enum):
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    EFFICIENT = "efficient"
    MODERATE_WASTE = "moderate_waste"
    SEVERE_WASTE = "severe_waste"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"


class RecommendationCategory(str, Enum):
    IDLE_SHUTDOWN = "idle_shutdown"
    LOAD_BALANCING = "load_balancing"
    SCHEDULING_OPTIMIZATION = "scheduling_optimization"
    PEAK_ADJUSTMENT = "peak_adjustment"
    MAINTENANCE = "maintenance"
    OPTIMIZE_OPERATION = "optimize_operation"


class RecommendationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyFeatures(BaseModel):
    power_kw: float
    current_a: float
    voltage_v: float
    load_percent: float
    temperature_c: float
    vibration_mm_s: float
    power_factor: float
    energy_per_unit: float
    utilization_percent: float
    power_deviation_percent: float
    ambient_temperature_c: float
    humidity_percent: float
    idle_energy_ratio: float


class EfficiencyFeatures(BaseModel):
    power_kw: float
    load_percent: float
    output_units: float
    temperature_c: float
    vibration_mm_s: float
    ambient_temperature_c: float
    humidity_percent: float
    utilization_percent: float
    energy_per_unit: float
    idle_energy_ratio: float
    power_deviation_percent: float
    hour_of_day: int
    day_of_week: int
    weekend_flag: int


class ForecastFeatures(BaseModel):
    plant_total_power_kw: float
    plant_total_output_units: float
    avg_load_percent: float
    num_active_machines: int
    num_anomalies: int
    hour_of_day: int
    day_of_week: int
    weekend_flag: int
    peak_tariff_flag: int
    lag_1_power_kw: float
    lag_2_power_kw: float
    lag_3_power_kw: float
    lag_4_power_kw: float
    lag_5_power_kw: float
    lag_6_power_kw: float
    lag_12_power_kw: float
    lag_24_power_kw: float
    rolling_mean_6: float
    rolling_std_6: float


class AnomalyResult(BaseModel):
    is_anomaly: bool
    anomaly_score: float
    anomaly_type: Optional[str] = None


class EfficiencyResult(BaseModel):
    efficiency_class: str
    efficiency_score: int
    confidence: float
    probabilities: dict


class ForecastResult(BaseModel):
    current_power_kw: float
    predicted_next_power_kw: float
    peak_window: Optional[str] = None


class MachineBase(BaseModel):
    machine_id: str
    name: str
    type: str
    plant_id: str
    zone_id: str
    rated_power_kw: float
    current_power_kw: Optional[float] = None
    load_percent: Optional[float] = None
    temperature_c: Optional[float] = None
    runtime_state: Optional[str] = None
    efficiency_score: Optional[int] = None
    efficiency_class: Optional[str] = None
    anomaly_score: Optional[float] = None
    is_anomaly: Optional[bool] = None
    predicted_demand_kw: Optional[float] = None
    output_rate: Optional[int] = None


class MachineWithStatus(MachineBase):
    status: MachineStatus


class Alert(BaseModel):
    alert_id: str
    machine_id: str
    severity: AlertSeverity
    issue_type: str
    message: str
    recommended_action: str
    timestamp: datetime
    status: AlertStatus


class Recommendation(BaseModel):
    recommendation_id: str
    machine_id: str
    category: RecommendationCategory
    priority: RecommendationPriority
    title: str
    estimated_savings_percent: float
    reason: str
    source: str


class ForecastPoint(BaseModel):
    time: str
    actual: Optional[float] = None
    predicted: float


class ForecastData(BaseModel):
    current_demand_kw: float
    predicted_next_hour_kw: float
    peak_window: Optional[str] = None
    forecast_points: List[ForecastPoint]


class DashboardSummary(BaseModel):
    total_machines: int
    active_machines: int
    total_power_kw: float
    avg_efficiency: float
    anomalies_detected: int
    critical_alerts: int
    potential_savings_kwh: float
    forecast: ForecastData
    summary: dict


class PlantOverview(BaseModel):
    plant_id: str
    total_machines: int
    total_power_kw: float
    avg_efficiency: float
    anomaly_count: int

export const generateMockDataForScenario = (scenario) => {
  const baseMachines = [
    { machine_id: 'M-101', name: 'Compressor A', type: 'Compressor', status: 'warning', current_power_kw: 42.8, efficiency_score: 68, anomaly_score: 0.81, runtime_state: 'active', temperature_c: 71.2, predicted_demand_kw: 48.5, output_rate: 82 },
    { machine_id: 'M-102', name: 'Conveyor B', type: 'Conveyor', status: 'normal', current_power_kw: 18.2, efficiency_score: 92, anomaly_score: 0.12, runtime_state: 'active', temperature_c: 45.3, predicted_demand_kw: 19.0, output_rate: 95 },
    { machine_id: 'M-103', name: 'HVAC Unit', type: 'HVAC', status: 'critical', current_power_kw: 85.4, efficiency_score: 45, anomaly_score: 0.94, runtime_state: 'active', temperature_c: 82.1, predicted_demand_kw: 78.0, output_rate: 60 },
    { machine_id: 'M-104', name: 'Pump Station', type: 'Pump', status: 'warning', current_power_kw: 31.5, efficiency_score: 71, anomaly_score: 0.65, runtime_state: 'active', temperature_c: 63.4, predicted_demand_kw: 33.0, output_rate: 74 },
    { machine_id: 'M-105', name: 'Grinder C', type: 'Grinder', status: 'normal', current_power_kw: 55.2, efficiency_score: 88, anomaly_score: 0.23, runtime_state: 'idle', temperature_c: 38.5, predicted_demand_kw: 52.0, output_rate: 90 },
  ];

  const scenarioModifiers = {
    normal: {
      machines: baseMachines,
      alerts: [
        { alert_id: 'ALT-001', machine_id: 'M-101', severity: 'warning', issue_type: 'efficiency_drift', message: 'Efficiency dropping below target', recommended_action: 'Schedule maintenance', timestamp: new Date().toISOString(), status: 'new' },
        { alert_id: 'ALT-002', machine_id: 'M-103', severity: 'critical', issue_type: 'high_temperature', message: 'Temperature exceeding safe threshold', recommended_action: 'Reduce load and inspect cooling', timestamp: new Date().toISOString(), status: 'new' },
      ],
      recommendations: [
        { recommendation_id: 'REC-100', machine_id: 'M-101', category: 'maintenance', priority: 'high', title: 'Compressor A efficiency degradation', estimated_savings_percent: 12.5, reason: 'Anomaly score increased 40% in 2 hours', source: 'anomaly_model' },
        { recommendation_id: 'REC-101', machine_id: 'M-103', category: 'load_balancing', priority: 'critical', title: 'HVAC Unit overload risk', estimated_savings_percent: 18.0, reason: 'Power draw 35% above normal', source: 'forecast+efficiency_model' },
      ],
      forecast: {
        current_demand_kw: 182.4,
        predicted_next_hour_kw: 205.7,
        peak_window: '14:00-15:00',
        forecast_points: [
          { time: '13:00', actual: 180, predicted: 184 },
          { time: '14:00', actual: 188, predicted: 205 },
          { time: '15:00', actual: 0, predicted: 198 },
          { time: '16:00', actual: 0, predicted: 175 },
        ],
      },
      summary: { source: 'sarvam', title: 'Morning Shift Summary', summary: 'Three machines showed elevated energy use. Compressor A has highest inefficiency trend. Recommend load redistribution and maintenance review.' },
    },
     idle_energy_waste: {
       machines: baseMachines.map((m) => m.machine_id === 'M-105' ? { ...m, current_power_kw: 48.2, runtime_state: 'idle', efficiency_score: 32, anomaly_score: 0.89, status: 'critical' } : m),
       alerts: [
         { alert_id: 'ALT-101', machine_id: 'M-105', severity: 'critical', issue_type: 'idle_energy_waste', message: 'Grinder C consuming 48kW while idle', recommended_action: 'Implement auto-shutdown after 15min idle', timestamp: new Date().toISOString(), status: 'new' },
       ],
       recommendations: [
         { recommendation_id: 'REC-200', machine_id: 'M-105', category: 'idle_shutdown', priority: 'high', title: 'Idle energy waste detected', estimated_savings_percent: 42.0, reason: 'Machine in idle state for 45+ minutes at 48kW', source: 'anomaly_model' },
       ],
       forecast: { 
         current_demand_kw: 210.5, 
         predicted_next_hour_kw: 225.3, 
         peak_window: '13:30-14:30', 
         forecast_points: [
           { time: '12:00', actual: 195, predicted: 198 },
           { time: '13:00', actual: 205, predicted: 212 },
           { time: '14:00', actual: 210, predicted: 225 },
           { time: '15:00', actual: 0, predicted: 218 },
         ] 
       },
       summary: { source: 'sarvam', title: 'Idle Waste Alert', summary: 'Significant idle energy waste detected on Grinder C. Potential savings of 200kWh per shift if addressed.' },
     },
     overload_spike: {
       machines: baseMachines.map((m) => m.machine_id === 'M-101' ? { ...m, current_power_kw: 98.5, anomaly_score: 0.97, efficiency_score: 41, status: 'critical' } : m),
       alerts: [
         { alert_id: 'ALT-201', machine_id: 'M-101', severity: 'critical', issue_type: 'overload_spike', message: 'Power spike detected - 130% above nominal', recommended_action: 'Immediate load reduction', timestamp: new Date().toISOString(), status: 'new' },
       ],
       recommendations: [
         { recommendation_id: 'REC-300', machine_id: 'M-101', category: 'load_balancing', priority: 'critical', title: 'Overload spike on Compressor A', estimated_savings_percent: 25.0, reason: 'Sudden 130% power increase', source: 'anomaly_model' },
       ],
       forecast: { 
         current_demand_kw: 245.8, 
         predicted_next_hour_kw: 268.4, 
         peak_window: 'Now-14:30', 
         forecast_points: [
           { time: '12:00', actual: 230, predicted: 235 },
           { time: '13:00', actual: 240, predicted: 252 },
           { time: '14:00', actual: 245, predicted: 268 },
           { time: '15:00', actual: 0, predicted: 260 },
         ] 
       },
       summary: { source: 'fallback', title: 'Critical Overload', summary: 'Emergency: Overload detected on Compressor A. Immediate action required to prevent equipment damage.' },
     },
     peak_demand_surge: {
       machines: baseMachines,
       alerts: [
         { alert_id: 'ALT-301', machine_id: 'plant', severity: 'warning', issue_type: 'peak_demand', message: 'Plant demand approaching peak capacity', recommended_action: 'Shift non-critical loads to off-peak', timestamp: new Date().toISOString(), status: 'new' },
       ],
       recommendations: [
         { recommendation_id: 'REC-400', machine_id: 'plant', category: 'peak_adjustment', priority: 'high', title: 'Peak demand surge predicted', estimated_savings_percent: 15.0, reason: 'Forecast shows demand exceeding threshold by 18%', source: 'forecast_model' },
       ],
       forecast: { 
         current_demand_kw: 285.6, 
         predicted_next_hour_kw: 312.3, 
         peak_window: '14:00-16:00', 
         forecast_points: [
           { time: '12:00', actual: 265, predicted: 268 },
           { time: '13:00', actual: 275, predicted: 288 },
           { time: '14:00', actual: 285, predicted: 312 },
           { time: '15:00', actual: 0, predicted: 305 },
         ] 
       },
       summary: { source: 'sarvam', title: 'Peak Demand Warning', summary: 'Energy demand expected to exceed normal peak by 22% in next 2 hours. Load shedding recommended.' },
     },
  };

  return scenarioModifiers[scenario] || scenarioModifiers.normal;
};

export const getMachines = (scenarioData) => scenarioData.machines;
export const getAlerts = (scenarioData) => scenarioData.alerts;
export const getRecommendations = (scenarioData) => scenarioData.recommendations;
export const getForecast = (scenarioData) => scenarioData.forecast;
export const getSummary = (scenarioData) => scenarioData.summary;

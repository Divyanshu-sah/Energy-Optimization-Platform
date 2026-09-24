import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';

const ScenarioContext = createContext();
export const useScenario = () => useContext(ScenarioContext);

const DEMO_MACHINES = [
  { machine_id: 'M-101', name: 'Compressor A', type: 'Compressor', status: 'warning', current_power_kw: 85.3, efficiency_score: 68, anomaly_score: 0.81, runtime_state: 'active', temperature_c: 71.2, predicted_demand_kw: 92.5, output_rate: 78 },
  { machine_id: 'M-102', name: 'Conveyor B', type: 'Conveyor', status: 'normal', current_power_kw: 28.2, efficiency_score: 91, anomaly_score: 0.15, runtime_state: 'active', temperature_c: 42.3, predicted_demand_kw: 29.0, output_rate: 88 },
  { machine_id: 'M-103', name: 'HVAC Unit', type: 'HVAC', status: 'critical', current_power_kw: 125.4, efficiency_score: 52, anomaly_score: 0.89, runtime_state: 'active', temperature_c: 78.5, predicted_demand_kw: 118.0, output_rate: 65 },
  { machine_id: 'M-104', name: 'Pump Station', type: 'Pump', status: 'warning', current_power_kw: 45.8, efficiency_score: 74, anomaly_score: 0.62, runtime_state: 'active', temperature_c: 58.4, predicted_demand_kw: 48.2, output_rate: 72 },
  { machine_id: 'M-105', name: 'Grinder C', type: 'Grinder', status: 'normal', current_power_kw: 62.1, efficiency_score: 87, anomaly_score: 0.28, runtime_state: 'idle', temperature_c: 41.2, predicted_demand_kw: 58.5, output_rate: 85 },
];

function parseCSV(text) {
  const lines = text.trim().split('\n');
  if (lines.length < 2) return [];
  const headers = lines[0].split(',');
  return lines.slice(1).map(line => {
    const vals = line.split(',');
    const obj = {};
    headers.forEach((h, i) => { obj[h.trim()] = (vals[i] || '').trim(); });
    return obj;
  });
}

async function loadSimulatorMachine() {
  try {
    const res = await fetch('/live_telemetry.csv');
    if (!res.ok) return null;
    const text = await res.text();
    const rows = parseCSV(text);
    if (rows.length === 0) return null;
    const latest = rows[rows.length - 1];
    if (latest.machine_id !== 'SIM_COMP_001') return null;

    const power = parseFloat(latest.power_kw) || 90;
    const load = parseFloat(latest.load_percent) || 70;
    const temp = parseFloat(latest.temperature_c) || 40;
    const vib = parseFloat(latest.vibration_mm_s) || 2.0;
    const output = parseFloat(latest.output_units) || 60;
    const state = latest.runtime_state || 'active';
    const scenario = latest.scenario || 'normal';

    const eff = Math.max(20, Math.min(98, 85 - (scenario === 'overload_spike' ? 30 : scenario === 'idle_energy_waste' ? 40 : 0) + (Math.random() * 10 - 5))).toFixed(0);
    const anomaly = Math.min(1, Math.max(0, (scenario === 'overload_spike' ? 0.85 : scenario === 'idle_energy_waste' ? 0.7 : 0.2) + (Math.random() * 0.1 - 0.05))).toFixed(2);
    const st = anomaly > 0.8 ? 'critical' : anomaly > 0.6 ? 'warning' : 'normal';

    return {
      machine_id: 'SIM_COMP_001',
      name: 'Simulator Compressor 01',
      type: 'Compressor',
      status: st,
      current_power_kw: parseFloat(power.toFixed(1)),
      efficiency_score: parseInt(eff),
      anomaly_score: parseFloat(anomaly),
      runtime_state: state,
      temperature_c: parseFloat(temp.toFixed(1)),
      predicted_demand_kw: parseFloat((power * 1.05).toFixed(1)),
      output_rate: Math.min(100, Math.round(output / 1.5)),
      load_percent: parseFloat(load.toFixed(0)),
      vibration_mm_s: parseFloat(vib.toFixed(2)),
      scenario,
      is_simulator: true,
    };
  } catch {
    return null;
  }
}

const SCENARIOS = {
  normal: {
    alerts: [
      { alert_id: 'ALT-001', machine_id: 'M-101', severity: 'warning', issue_type: 'efficiency_drift', message: 'Efficiency dropping below target threshold', recommended_action: 'Schedule maintenance inspection', timestamp: new Date().toISOString(), status: 'new' },
      { alert_id: 'ALT-002', machine_id: 'M-103', severity: 'critical', issue_type: 'high_temperature', message: 'Temperature exceeding safe operating threshold', recommended_action: 'Reduce load and inspect cooling', timestamp: new Date().toISOString(), status: 'new' },
    ],
    recommendations: [
      { recommendation_id: 'REC-100', machine_id: 'M-101', category: 'maintenance', priority: 'high', title: 'Compressor A efficiency degradation', estimated_savings_percent: 14.5, reason: 'Anomaly score increased 45% in 2 hours', source: 'anomaly_model' },
      { recommendation_id: 'REC-101', machine_id: 'M-103', category: 'load_balancing', priority: 'critical', title: 'HVAC Unit overload risk', estimated_savings_percent: 18.0, reason: 'Power draw 32% above normal', source: 'forecast_model' },
    ],
    forecast: { current_demand_kw: 285.4, predicted_next_hour_kw: 312.7, peak_window: '14:00-16:00', forecast_points: [
      { time: '12:00', actual: 278, predicted: 282 }, { time: '13:00', actual: 285, predicted: 288 },
      { time: '14:00', actual: 292, predicted: 315 }, { time: '15:00', actual: 305, predicted: 318 },
      { time: '16:00', actual: null, predicted: 298 }, { time: '17:00', actual: null, predicted: 275 },
    ]},
    summary: { source: 'ml_models', title: 'Morning Operations Summary', summary: 'System monitoring machines. Compressor A showing efficiency drift. HVAC Unit at critical temperature.' },
  },
  idle_energy_waste: {
    alerts: [{ alert_id: 'ALT-101', machine_id: 'M-105', severity: 'critical', issue_type: 'idle_energy_waste', message: 'Grinder C consuming 58kW while idle', recommended_action: 'Implement auto-shutdown after 15min idle', timestamp: new Date().toISOString(), status: 'new' }],
    recommendations: [{ recommendation_id: 'REC-200', machine_id: 'M-105', category: 'idle_shutdown', priority: 'high', title: 'Idle energy waste on Grinder C', estimated_savings_percent: 45.0, reason: 'Machine idle for 45+ min at 58kW', source: 'anomaly_model' }],
    forecast: { current_demand_kw: 310.5, predicted_next_hour_kw: 325.3, peak_window: '13:30-14:30', forecast_points: [
      { time: '12:00', actual: 295, predicted: 298 }, { time: '13:00', actual: 305, predicted: 312 },
      { time: '14:00', actual: 310, predicted: 325 }, { time: '15:00', actual: null, predicted: 318 },
    ]},
    summary: { source: 'ml_models', title: 'Idle Waste Alert', summary: 'Significant idle energy waste on Grinder C. Potential savings of 280kWh per shift.' },
  },
  overload_spike: {
    alerts: [{ alert_id: 'ALT-201', machine_id: 'M-101', severity: 'critical', issue_type: 'overload_spike', message: 'Power spike - 125% above nominal', recommended_action: 'Immediate load reduction required', timestamp: new Date().toISOString(), status: 'new' }],
    recommendations: [{ recommendation_id: 'REC-300', machine_id: 'M-101', category: 'load_balancing', priority: 'critical', title: 'Overload on Compressor A', estimated_savings_percent: 28.0, reason: 'Sudden 125% power increase', source: 'anomaly_model' }],
    forecast: { current_demand_kw: 365.8, predicted_next_hour_kw: 388.4, peak_window: 'Now-14:30', forecast_points: [
      { time: '12:00', actual: 320, predicted: 325 }, { time: '13:00', actual: 345, predicted: 352 },
      { time: '14:00', actual: 365, predicted: 388 }, { time: '15:00', actual: null, predicted: 375 },
    ]},
    summary: { source: 'ml_models', title: 'Critical Overload Alert', summary: 'Emergency: Overload on Compressor A. Immediate action required.' },
  },
  peak_demand_surge: {
    alerts: [{ alert_id: 'ALT-301', machine_id: 'plant', severity: 'warning', issue_type: 'peak_demand', message: 'Plant demand approaching peak capacity', recommended_action: 'Shift non-critical loads to off-peak', timestamp: new Date().toISOString(), status: 'new' }],
    recommendations: [{ recommendation_id: 'REC-400', machine_id: 'plant', category: 'peak_adjustment', priority: 'high', title: 'Peak demand surge predicted', estimated_savings_percent: 16.0, reason: 'Demand exceeding threshold by 18%', source: 'forecast_model' }],
    forecast: { current_demand_kw: 395.6, predicted_next_hour_kw: 425.3, peak_window: '14:00-17:00', forecast_points: [
      { time: '12:00', actual: 365, predicted: 368 }, { time: '13:00', actual: 382, predicted: 388 },
      { time: '14:00', actual: 395, predicted: 425 }, { time: '15:00', actual: null, predicted: 418 },
    ]},
    summary: { source: 'ml_models', title: 'Peak Demand Warning', summary: 'Energy demand expected to exceed peak by 22%. Load shedding recommended.' },
  },
};

export const ScenarioProvider = ({ children }) => {
  const [currentScenario, setCurrentScenario] = useState('normal');
  const [simulationRunning, setSimulationRunning] = useState(false);
  const [simulationSpeed, setSimulationSpeed] = useState(1);
  const [eventLog, setEventLog] = useState([]);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Load machines: demo + simulator from CSV (NO API)
  useEffect(() => {
    const init = async () => {
      setLoading(true);
      const sim = await loadSimulatorMachine();
      const machines = [...DEMO_MACHINES];
      if (sim) machines.push(sim);
      const sc = SCENARIOS.normal;
      setData({ machines, alerts: sc.alerts, recommendations: sc.recommendations, forecast: sc.forecast, summary: { ...sc.summary, summary: `System monitoring ${machines.length} machines.` } });
      setLoading(false);
    };
    init();
  }, []);

  // Refresh simulator machine every 3s from CSV
  useEffect(() => {
    const interval = setInterval(async () => {
      const sim = await loadSimulatorMachine();
      if (!sim) return;
      setData(prev => {
        if (!prev) return prev;
        const machines = prev.machines.filter(m => m.machine_id !== 'SIM_COMP_001');
        machines.push(sim);
        const totalPower = machines.reduce((s, m) => s + m.current_power_kw, 0);
        return { ...prev, machines, summary: { ...prev.summary, summary: `System monitoring ${machines.length} machines. Total: ${totalPower.toFixed(0)} kW.` } };
      });
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  // Simulation loop
  useEffect(() => {
    let simulationInterval = null;
    if (simulationRunning) {
      const updateSimulation = () => {
        const newData = { ...data };
        if (newData.machines && newData.machines.length > 0) {
          newData.machines = newData.machines.map(machine => {
            const pv = 0.95 + Math.random() * 0.1;
            const ev = 0.97 + Math.random() * 0.06;
            const tv = 0.98 + Math.random() * 0.04;
            return {
              ...machine,
              current_power_kw: Number((machine.current_power_kw * pv).toFixed(1)),
              efficiency_score: Math.min(100, Math.max(0, Number((machine.efficiency_score * ev).toFixed(0)))),
              temperature_c: Number((machine.temperature_c * tv).toFixed(1)),
              runtime_state: Math.random() < 0.02 ? (machine.runtime_state === 'active' ? 'idle' : 'active') : machine.runtime_state
            };
          });
        }
        if (newData.forecast) {
          newData.forecast = {
            ...newData.forecast,
            current_demand_kw: Number((newData.forecast.current_demand_kw * (0.98 + Math.random() * 0.04)).toFixed(1)),
            predicted_next_hour_kw: Number((newData.forecast.predicted_next_hour_kw * (0.98 + Math.random() * 0.04)).toFixed(1))
          };
        }
        if (newData.summary) {
          newData.summary = { ...newData.summary, summary: `System monitoring ${newData.machines?.length || 0} machines. ${newData.alerts?.filter(a => a.status === 'new').length || 0} active alerts.` };
        }
        setData(newData);
        addEventLog(`Update at ${new Date().toLocaleTimeString()}`);
      };
      const interval = Math.max(200, 2000 / simulationSpeed);
      simulationInterval = setInterval(updateSimulation, interval);
      updateSimulation();
    } else if (simulationInterval) {
      clearInterval(simulationInterval);
    }
    return () => { if (simulationInterval) clearInterval(simulationInterval); };
  }, [simulationRunning, simulationSpeed, data]);

  const addEventLog = (message) => {
    setEventLog(prev => [{ id: Date.now(), timestamp: new Date().toISOString(), message }, ...prev].slice(0, 50));
  };

  const changeScenario = (scenarioId) => {
    setCurrentScenario(scenarioId);
    const sc = SCENARIOS[scenarioId] || SCENARIOS.normal;
    setData(prev => {
      const machines = prev ? prev.machines : [...DEMO_MACHINES];
      return { machines, alerts: sc.alerts, recommendations: sc.recommendations, forecast: sc.forecast, summary: { ...sc.summary, summary: `System monitoring ${machines.length} machines.` } };
    });
    addEventLog(`Scenario: ${scenarioId}`);
    if (simulationRunning) { setSimulationRunning(false); setTimeout(() => setSimulationRunning(true), 100); }
  };

  const startSimulation = () => { setSimulationRunning(true); addEventLog('Simulation started'); };
  const stopSimulation = () => { setSimulationRunning(false); addEventLog('Simulation paused'); };
  const triggerEvent = (eventType) => { addEventLog(`Event: ${eventType}`); changeScenario(eventType); };

  return (
    <ScenarioContext.Provider value={{ currentScenario, simulationRunning, simulationSpeed, eventLog, data, loading, changeScenario, startSimulation, stopSimulation, setSimulationSpeed, triggerEvent, addEventLog }}>
      {children}
    </ScenarioContext.Provider>
  );
};

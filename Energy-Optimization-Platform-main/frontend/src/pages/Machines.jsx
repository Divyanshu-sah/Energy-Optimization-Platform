import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useScenario } from '../context/ScenarioContext';
import MachineCard from '../components/ui/MachineCard';
import StatusBadge from '../components/ui/StatusBadge';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Gauge, Zap, Thermometer, Activity, TrendingUp } from 'lucide-react';

const Machines = () => {
  const { data } = useScenario();
  const { machines, alerts, recommendations } = data;
  const [selectedMachine, setSelectedMachine] = useState(machines?.[0] || null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (machines && machines.length > 0 && !selectedMachine) {
      setSelectedMachine(machines[0]);
    }
  }, [machines]);

  if (!machines || machines.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Loading machines...</p>
        </div>
      </div>
    );
  }

  const machineAlerts = alerts.filter((a) => a.machine_id === selectedMachine?.machine_id);
  const machineRecs = recommendations.filter((r) => r.machine_id === selectedMachine?.machine_id);

   const generateTelemetryHistory = () => {
     // Generate more realistic historical data with daily patterns
     const history = [];
     const basePower = selectedMachine.current_power_kw;
     const baseTemp = selectedMachine.temperature_c;
     
     for (let i = 0; i < 24; i++) {
       // Simulate daily patterns: lower power at night, higher during day
       const hour = i;
       const isWeekend = new Date().getDay() === 0 || new Date().getDay() === 6;
       const dailyFactor = isWeekend ? 0.7 : 0.6 + Math.sin((hour - 6) * Math.PI / 12) * 0.4;
       const powerVariation = 0.8 + Math.random() * 0.4; // 20% variation
       
       // Temperature follows power usage with some lag
       const tempVariation = 0.9 + Math.random() * 0.2;
       
       history.push({
         time: `${hour.toString().padStart(2, '0')}:00`,
         power: Number((basePower * dailyFactor * powerVariation).toFixed(1)),
         temperature: Number((baseTemp * tempVariation * 0.9 + 5).toFixed(1)) // Base temp + variation
       });
     }
     
     return history;
   };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-3">
          <h3 className="font-medium text-gray-200">Machine Fleet</h3>
          <div className="space-y-2 max-h-[600px] overflow-y-auto pr-2">
            {machines.map((machine) => (
              <div key={machine.machine_id} onClick={() => setSelectedMachine(machine)} className={`cursor-pointer transition-all rounded-lg ${selectedMachine?.machine_id === machine.machine_id ? 'ring-2 ring-cyan-500 bg-dark-800' : 'hover:bg-dark-800/50'}`}>
                <MachineCard machine={machine} />
              </div>
            ))}
          </div>
        </div>

        <div className="lg:col-span-2 space-y-6">
          {selectedMachine && (
            <AnimatePresence mode="wait">
              <motion.div key={selectedMachine.machine_id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="space-y-6">
                <div className="bg-dark-800/50 rounded-xl border border-dark-700 p-5">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h2 className="text-2xl font-bold text-gray-100">{selectedMachine.name}</h2>
                      <p className="text-gray-400">{selectedMachine.type} • ID: {selectedMachine.machine_id}</p>
                    </div>
                    <StatusBadge status={selectedMachine.status} size="lg" />
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-3 bg-dark-900/50 rounded-lg text-center"><Zap className="w-5 h-5 text-cyan-400 mx-auto mb-1" /><p className="text-xs text-gray-500">Power</p><p className="text-lg font-mono font-bold">{selectedMachine.current_power_kw} kW</p></div>
                    <div className="p-3 bg-dark-900/50 rounded-lg text-center"><Gauge className="w-5 h-5 text-emerald-400 mx-auto mb-1" /><p className="text-xs text-gray-500">Efficiency</p><p className="text-lg font-mono font-bold">{selectedMachine.efficiency_score}%</p></div>
                    <div className="p-3 bg-dark-900/50 rounded-lg text-center"><Thermometer className="w-5 h-5 text-orange-400 mx-auto mb-1" /><p className="text-xs text-gray-500">Temperature</p><p className="text-lg font-mono font-bold">{selectedMachine.temperature_c}°C</p></div>
                    <div className="p-3 bg-dark-900/50 rounded-lg text-center"><Activity className="w-5 h-5 text-purple-400 mx-auto mb-1" /><p className="text-xs text-gray-500">Anomaly Score</p><p className="text-lg font-mono font-bold">{(selectedMachine.anomaly_score * 100).toFixed(0)}%</p></div>
                  </div>
                </div>

                <div className="bg-dark-800/50 rounded-xl border border-dark-700 p-4">
                  <h3 className="text-sm font-medium text-gray-300 mb-3">Live Telemetry Trend</h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <LineChart data={generateTelemetryHistory()}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="time" stroke="#64748b" />
                      <YAxis yAxisId="left" stroke="#06b6d4" />
                      <YAxis yAxisId="right" orientation="right" stroke="#f59e0b" />
                      <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                      <Line yAxisId="left" type="monotone" dataKey="power" stroke="#06b6d4" strokeWidth={2} name="Power (kW)" />
                      <Line yAxisId="right" type="monotone" dataKey="temperature" stroke="#f59e0b" strokeWidth={2} name="Temp (°C)" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                {machineAlerts.length > 0 && (
                  <div className="bg-rose-500/10 rounded-xl border border-rose-500/30 p-4">
                    <h3 className="text-sm font-medium text-rose-400 mb-2">Active Alerts</h3>
                    {machineAlerts.map((alert) => <p key={alert.alert_id} className="text-sm text-gray-300">⚠ {alert.message}</p>)}
                  </div>
                )}

                {machineRecs.length > 0 && (
                  <div className="bg-cyan-500/10 rounded-xl border border-cyan-500/30 p-4">
                    <h3 className="text-sm font-medium text-cyan-400 mb-2 flex items-center gap-2"><TrendingUp className="w-4 h-4" />Recommendations</h3>
                    {machineRecs.map((rec) => <p key={rec.recommendation_id} className="text-sm text-gray-300">→ {rec.title}</p>)}
                  </div>
                )}
              </motion.div>
            </AnimatePresence>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default Machines;

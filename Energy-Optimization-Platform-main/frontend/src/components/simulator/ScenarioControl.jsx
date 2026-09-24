import React from 'react';
import { motion } from 'framer-motion';
import { Play, Square, Zap, Wind, AlertTriangle, BarChart3, Gauge, FastForward } from 'lucide-react';
import { useScenario } from '../../context/ScenarioContext';

const scenarios = [
  { id: 'normal', name: 'Normal Operation', icon: <BarChart3 className="w-4 h-4" />, color: 'emerald' },
  { id: 'idle_energy_waste', name: 'Idle Energy Waste', icon: <Zap className="w-4 h-4" />, color: 'amber' },
  { id: 'overload_spike', name: 'Overload Spike', icon: <AlertTriangle className="w-4 h-4" />, color: 'rose' },
  { id: 'peak_demand_surge', name: 'Peak Demand Surge', icon: <Gauge className="w-4 h-4" />, color: 'purple' },
];

const scenarioStyles = {
  emerald: 'border-emerald-500 bg-emerald-500/10 shadow-lg shadow-emerald-500/20',
  amber: 'border-amber-500 bg-amber-500/10 shadow-lg shadow-amber-500/20',
  rose: 'border-rose-500 bg-rose-500/10 shadow-lg shadow-rose-500/20',
  purple: 'border-purple-500 bg-purple-500/10 shadow-lg shadow-purple-500/20',
};

const ScenarioControl = () => {
  const { currentScenario, simulationRunning, simulationSpeed, changeScenario, startSimulation, stopSimulation, setSimulationSpeed, triggerEvent, eventLog } = useScenario();

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {scenarios.map((scenario) => (
          <motion.button
            key={scenario.id}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => changeScenario(scenario.id)}
            className={`p-3 rounded-xl border transition-all ${currentScenario === scenario.id ? scenarioStyles[scenario.color] : 'border-dark-700 bg-dark-800/50 hover:border-gray-600'}`}
          >
            <div className="flex items-center gap-2 justify-center">
              {scenario.icon}
              <span className="text-sm font-medium">{scenario.name}</span>
            </div>
          </motion.button>
        ))}
      </div>

      <div className="flex flex-wrap gap-3 items-center justify-between p-4 bg-dark-800/30 rounded-xl border border-dark-700">
        <div className="flex gap-2">
          {!simulationRunning ? (
            <button onClick={startSimulation} className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-lg flex items-center gap-2 transition-colors">
              <Play className="w-4 h-4" /> Start Simulation
            </button>
          ) : (
            <button onClick={stopSimulation} className="px-4 py-2 bg-rose-600 hover:bg-rose-500 rounded-lg flex items-center gap-2 transition-colors">
              <Square className="w-4 h-4" /> Stop
            </button>
          )}
          <button onClick={() => triggerEvent('overload_spike')} className="px-3 py-2 bg-amber-600/20 hover:bg-amber-600/40 text-amber-400 rounded-lg flex items-center gap-2 transition-colors">
            <AlertTriangle className="w-4 h-4" /> Trigger Overload
          </button>
        </div>
        <div className="flex items-center gap-2">
          <FastForward className="w-4 h-4 text-gray-400" />
          <input type="range" min="0.5" max="3" step="0.5" value={simulationSpeed} onChange={(e) => setSimulationSpeed(parseFloat(e.target.value))} className="w-32 accent-cyan-500" />
          <span className="text-sm text-gray-400">{simulationSpeed}x</span>
        </div>
      </div>

      <div className="bg-dark-900/50 rounded-xl border border-dark-700 p-4">
        <h4 className="text-sm font-medium text-gray-300 mb-2">Event Log</h4>
        <div className="space-y-1 max-h-40 overflow-y-auto font-mono text-xs">
          {eventLog.map((event) => (
            <div key={event.id} className="text-gray-400 border-l-2 border-cyan-500 pl-2 py-1">
              [{new Date(event.timestamp).toLocaleTimeString()}] {event.message}
            </div>
          ))}
          {eventLog.length === 0 && <p className="text-gray-500 text-center py-2">No events yet</p>}
        </div>
      </div>
    </div>
  );
};

export default ScenarioControl;

import React from 'react';
import { motion } from 'framer-motion';
import ScenarioControl from '../components/simulator/ScenarioControl';
import { useScenario } from '../context/ScenarioContext';
import { Cpu, Activity } from 'lucide-react';

const Simulator = () => {
  const { simulationRunning, currentScenario } = useScenario();

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-100">Simulation Control Center</h2>
          <p className="text-sm text-gray-400">Test different operational scenarios and see real-time impact</p>
        </div>
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${simulationRunning ? 'bg-emerald-600/20 text-emerald-400' : 'bg-gray-600/20 text-gray-400'}`}>
          <Activity className="w-4 h-4" />
          <span className="text-sm font-mono">{simulationRunning ? 'LIVE' : 'PAUSED'}</span>
        </div>
      </div>

      <div className="bg-dark-800/30 rounded-xl border border-dark-700 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Cpu className="w-5 h-5 text-cyan-400" />
          <h3 className="font-medium">Scenario Manager</h3>
        </div>
        <ScenarioControl />
      </div>

      <div className="bg-dark-800/50 rounded-xl border border-dark-700 p-4 text-center text-gray-400 text-sm">
        <p>Active Scenario: <span className="text-cyan-400 font-mono">{currentScenario}</span></p>
        <p className="mt-1">All dashboard data will reflect the selected scenario in real-time.</p>
      </div>
    </motion.div>
  );
};

export default Simulator;

import React from 'react';
import { motion } from 'framer-motion';
import { Gauge, Zap, Thermometer, Activity } from 'lucide-react';
import StatusBadge from './StatusBadge';

const MachineCard = ({ machine, onClick }) => {
  const getEfficiencyColor = (score) => {
    if (score >= 80) return 'text-emerald-400';
    if (score >= 60) return 'text-amber-400';
    return 'text-rose-400';
  };

  return (
    <motion.div
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      onClick={onClick}
      className="bg-dark-800/50 backdrop-blur-sm rounded-xl border border-dark-700 hover:border-cyan-500/50 p-4 cursor-pointer transition-all duration-300 group"
    >
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="font-semibold text-gray-100 group-hover:text-cyan-400 transition-colors">{machine.name}</h3>
          <p className="text-xs text-gray-500">{machine.type} • ID: {machine.machine_id}</p>
        </div>
        <StatusBadge status={machine.status} size="sm" />
      </div>

      <div className="grid grid-cols-2 gap-3 mt-3">
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-cyan-400" />
          <div>
            <p className="text-xs text-gray-500">Power</p>
            <p className="text-sm font-mono font-medium">{machine.current_power_kw} kW</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Thermometer className="w-4 h-4 text-orange-400" />
          <div>
            <p className="text-xs text-gray-500">Temp</p>
            <p className="text-sm font-mono font-medium">{machine.temperature_c}°C</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Gauge className={`w-4 h-4 ${getEfficiencyColor(machine.efficiency_score)}`} />
          <div>
            <p className="text-xs text-gray-500">Efficiency</p>
            <p className={`text-sm font-mono font-bold ${getEfficiencyColor(machine.efficiency_score)}`}>{machine.efficiency_score}%</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-purple-400" />
          <div>
            <p className="text-xs text-gray-500">Anomaly</p>
            <p className="text-sm font-mono font-medium">{(machine.anomaly_score * 100).toFixed(0)}%</p>
          </div>
        </div>
      </div>

      <div className="mt-3 pt-2 border-t border-dark-700">
        <div className="flex justify-between text-xs">
          <span className="text-gray-500">Output Rate</span>
          <span className="text-cyan-400 font-mono">{machine.output_rate}%</span>
        </div>
        <div className="w-full bg-dark-700 rounded-full h-1 mt-1">
          <div className="bg-gradient-to-r from-cyan-500 to-cyan-400 h-1 rounded-full transition-all" style={{ width: `${machine.output_rate}%` }} />
        </div>
      </div>
    </motion.div>
  );
};

export default MachineCard;

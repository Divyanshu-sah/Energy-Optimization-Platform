import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, AlertCircle } from 'lucide-react';

const KPICard = ({ title, value, unit, change, changeType, icon, color = 'cyan', animate = true }) => {
  const colorClasses = {
    cyan: 'from-cyan-600/20 to-cyan-800/10 border-cyan-500/30',
    emerald: 'from-emerald-600/20 to-emerald-800/10 border-emerald-500/30',
    amber: 'from-amber-600/20 to-amber-800/10 border-amber-500/30',
    rose: 'from-rose-600/20 to-rose-800/10 border-rose-500/30',
    purple: 'from-purple-600/20 to-purple-800/10 border-purple-500/30',
  };

  return (
    <motion.div
      initial={animate ? { y: 20, opacity: 0 } : false}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.3 }}
      whileHover={{ scale: 1.02, transition: { duration: 0.2 } }}
      className={`relative overflow-hidden rounded-2xl bg-gradient-to-br ${colorClasses[color]} border backdrop-blur-sm p-5 card-hover`}
    >
      <div className="flex justify-between items-start">
        <div>
          <p className="text-gray-400 text-sm font-medium uppercase tracking-wide">{title}</p>
          <div className="flex items-baseline gap-1 mt-2">
            <span className="text-3xl font-bold text-white">{value}</span>
            {unit && <span className="text-gray-400 text-sm">{unit}</span>}
          </div>
          {change !== undefined && (
            <div className="flex items-center gap-1 mt-2">
              {changeType === 'up' ? (
                <TrendingUp className="w-4 h-4 text-emerald-400" />
              ) : changeType === 'down' ? (
                <TrendingDown className="w-4 h-4 text-rose-400" />
              ) : (
                <AlertCircle className="w-4 h-4 text-amber-400" />
              )}
              <span className={`text-sm font-medium ${changeType === 'up' ? 'text-emerald-400' : changeType === 'down' ? 'text-rose-400' : 'text-amber-400'}`}>
                {change}%
              </span>
              <span className="text-gray-500 text-xs">vs last shift</span>
            </div>
          )}
        </div>
        <div className="p-2 rounded-xl bg-white/5 backdrop-blur-sm">
          {icon}
        </div>
      </div>
      <div className="absolute -bottom-8 -right-8 w-24 h-24 bg-gradient-to-br from-cyan-500/10 to-transparent rounded-full blur-2xl" />
    </motion.div>
  );
};

export default KPICard;

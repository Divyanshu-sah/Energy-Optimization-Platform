import React from 'react';
import { motion } from 'framer-motion';

const StatusBadge = ({ status, size = 'md', showIcon = true }) => {
  const config = {
    normal: { label: 'Normal', color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30', icon: '●' },
    warning: { label: 'Warning', color: 'bg-amber-500/20 text-amber-400 border-amber-500/30', icon: '⚠' },
    critical: { label: 'Critical', color: 'bg-rose-500/20 text-rose-400 border-rose-500/30', icon: '‼' },
    efficient: { label: 'Efficient', color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30', icon: '✓' },
    moderate_waste: { label: 'Moderate Waste', color: 'bg-amber-500/20 text-amber-400 border-amber-500/30', icon: '!' },
    severe_waste: { label: 'Severe Waste', color: 'bg-rose-500/20 text-rose-400 border-rose-500/30', icon: '‼' },
    online: { label: 'Online', color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30', icon: '●' },
    offline: { label: 'Offline', color: 'bg-gray-600/20 text-gray-400 border-gray-600/30', icon: '○' },
  };

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-1.5 text-base',
  };

  const { label, color, icon } = config[status] || config.normal;

  return (
    <motion.span
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className={`inline-flex items-center gap-1.5 font-mono font-medium rounded-full border ${color} ${sizeClasses[size]}`}
    >
      {showIcon && <span className="text-xs">{icon}</span>}
      {label}
    </motion.span>
  );
};

export default StatusBadge;

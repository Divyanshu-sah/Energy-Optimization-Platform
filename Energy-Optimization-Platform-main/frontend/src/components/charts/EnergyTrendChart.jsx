import React from 'react';
import { LineChart, Line, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { motion } from 'framer-motion';

const EnergyTrendChart = ({ data, title, height = 300 }) => {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-dark-800/50 rounded-xl border border-dark-700 p-4">
      <h3 className="text-sm font-medium text-gray-300 mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="time" stroke="#64748b" tick={{ fill: '#94a3b8' }} />
          <YAxis stroke="#64748b" tick={{ fill: '#94a3b8' }} />
          <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }} />
          <Legend wrapperStyle={{ color: '#94a3b8' }} />
          <Area type="monotone" dataKey="actual" stroke="#06b6d4" fill="#06b6d420" strokeWidth={2} name="Actual (kW)" />
          <Line type="monotone" dataKey="predicted" stroke="#f59e0b" strokeWidth={2} strokeDasharray="5 5" name="Predicted (kW)" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </motion.div>
  );
};

export default EnergyTrendChart;

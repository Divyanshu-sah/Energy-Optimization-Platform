import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useScenario } from '../context/ScenarioContext';
import EnergyTrendChart from '../components/charts/EnergyTrendChart';
import { Clock, AlertTriangle, TrendingUp } from 'lucide-react';

const Forecast = () => {
  const { data } = useScenario();
  const { forecast } = data;
  const [timeRange, setTimeRange] = useState('4h');

   const extendedData = [...forecast.forecast_points];
   if (timeRange === '8h' || timeRange === '12h') {
     // Generate forecast points based on current trend with some variation
     const baseForecast = forecast.forecast_points;
     const lastPoint = baseForecast[baseForecast.length - 1];
     const baseValue = lastPoint.predicted;
     
     let hoursToAdd = timeRange === '8h' ? 4 : 8; // 4h for 8h total (we already have 4h), 8h for 12h total
     
     for (let i = 1; i <= hoursToAdd; i++) {
       const futureHour = parseInt(lastPoint.time.split(':')[0]) + i;
       const timeStr = `${futureHour.toString().padStart(2, '0')}:00`;
       // Add some realistic variation based on time of day (higher during peak hours)
       const hour = futureHour;
       const peakFactor = (hour >= 14 && hour <= 18) ? 1.2 : 1.0;
       const variation = 0.95 + Math.random() * 0.1; // 5-10% variation
       const predictedValue = baseValue * peakFactor * variation;
       
       extendedData.push({ 
         time: timeStr, 
         actual: 0, // Future values don't have actual data yet
         predicted: Number(predictedValue.toFixed(1)) 
       });
     }
   }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold text-gray-100">Energy Demand Forecast</h2>
        <div className="flex gap-2">
          {['4h', '8h', '12h'].map((range) => (
            <button key={range} onClick={() => setTimeRange(range)} className={`px-3 py-1 rounded-lg text-sm ${timeRange === range ? 'bg-cyan-600' : 'bg-dark-800 hover:bg-dark-700'}`}>{range}</button>
          ))}
        </div>
      </div>

      <EnergyTrendChart data={extendedData} title="Actual vs Predicted Energy Demand" height={350} />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-dark-800/50 rounded-xl border border-dark-700 p-4">
          <Clock className="w-5 h-5 text-cyan-400 mb-2" />
          <p className="text-xs text-gray-500">Next Hour Peak</p>
          <p className="text-2xl font-bold text-gray-100">{forecast.predicted_next_hour_kw.toFixed(1)} kW</p>
          <p className="text-xs text-amber-400 mt-1">+{((forecast.predicted_next_hour_kw - forecast.current_demand_kw) / forecast.current_demand_kw * 100).toFixed(1)}% vs current</p>
        </div>
        <div className="bg-dark-800/50 rounded-xl border border-dark-700 p-4">
          <AlertTriangle className="w-5 h-5 text-amber-400 mb-2" />
          <p className="text-xs text-gray-500">Peak Demand Window</p>
          <p className="text-lg font-mono font-bold text-amber-400">{forecast.peak_window}</p>
          <p className="text-xs text-gray-400">High risk of demand charges</p>
        </div>
        <div className="bg-gradient-to-r from-cyan-900/20 to-dark-800 rounded-xl border border-cyan-500/30 p-4">
          <TrendingUp className="w-5 h-5 text-cyan-400 mb-2" />
          <p className="text-xs text-gray-500">AI Recommendation</p>
          <p className="text-sm text-gray-300">Shift non-critical loads to off-peak hours between 15:00-17:00 to reduce peak demand.</p>
        </div>
      </div>
    </motion.div>
  );
};

export default Forecast;

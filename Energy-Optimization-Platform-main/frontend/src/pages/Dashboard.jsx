import React from 'react';
import { motion } from 'framer-motion';
import { Zap, TrendingUp, AlertTriangle, DollarSign, Battery } from 'lucide-react';
import { useScenario } from '../context/ScenarioContext';
import KPICard from '../components/ui/KPICard';
import MachineCard from '../components/ui/MachineCard';
import AlertCard from '../components/ui/AlertCard';
import RecommendationCard from '../components/ui/RecommendationCard';
import EnergyTrendChart from '../components/charts/EnergyTrendChart';

const Dashboard = () => {
  const { data, apiAvailable, refreshData } = useScenario();
  const { machines, alerts, recommendations, forecast } = data;
  const [loading, setLoading] = React.useState(false);

  const handleRefresh = async () => {
    setLoading(true);
    await refreshData();
    setLoading(false);
  };

  if (!machines || machines.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Loading dashboard data...</p>
        </div>
      </div>
    );
  }

  const totalPower = machines.reduce((sum, m) => sum + m.current_power_kw, 0);
  const avgEfficiency = machines.reduce((sum, m) => sum + m.efficiency_score, 0) / machines.length;
  const wasteEstimate = machines.filter((m) => m.efficiency_score < 70).reduce((sum, m) => sum + m.current_power_kw * 0.3, 0);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Total Energy" value={totalPower.toFixed(1)} unit="kW" change={5.2} changeType="up" icon={<Zap className="w-5 h-5 text-cyan-400" />} color="cyan" />
        <KPICard title="Predicted Demand" value={forecast.predicted_next_hour_kw.toFixed(1)} unit="kW" change={8.7} changeType="up" icon={<TrendingUp className="w-5 h-5 text-amber-400" />} color="amber" />
        <KPICard title="Active Alerts" value={alerts.length} unit="" change={2} changeType="up" icon={<AlertTriangle className="w-5 h-5 text-rose-400" />} color="rose" />
        <KPICard title="Waste Estimate" value={wasteEstimate.toFixed(1)} unit="kW" change={12.3} changeType="up" icon={<DollarSign className="w-5 h-5 text-emerald-400" />} color="emerald" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <EnergyTrendChart data={forecast.forecast_points} title="Plant Energy: Actual vs Forecast" height={320} />
        </div>
        <div className="space-y-4">
          <div className="bg-dark-800/50 rounded-xl border border-dark-700 p-4">
            <h3 className="text-sm font-medium text-gray-300 mb-3">Quick Stats</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Avg Efficiency</span>
                <span className="text-2xl font-mono font-bold text-cyan-400">{avgEfficiency.toFixed(0)}%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Peak Window</span>
                <span className="text-sm font-mono text-amber-400">{forecast.peak_window}</span>
              </div>
       <div className="flex justify-between items-center">
                 <span className="text-gray-400">Projected Savings</span>
                 <span className="text-sm font-mono text-emerald-400">{wasteEstimate.toFixed(0)} kWh</span>
               </div>
            </div>
          </div>
          <div className="bg-gradient-to-r from-cyan-900/20 to-dark-800 rounded-xl border border-cyan-500/30 p-4">
            <div className="flex items-center gap-2">
              <Battery className="w-5 h-5 text-cyan-400" />
              <h3 className="text-sm font-medium">AI Insight</h3>
            </div>
            <p className="text-sm text-gray-300 mt-2">
             {alerts.length > 0 
               ? `Peak demand expected at ${new Date().getHours()}:00. ${alerts[0].issue_type.replace('_', ' ')} detected on ${alerts[0].machine_id}.`
               : "All systems operating normally. No immediate action required."
             }
           </p>
          </div>
        </div>
      </div>

       <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
         <div>
           <div className="flex justify-between items-center mb-3">
             <h3 className="font-medium text-gray-200">Top Machines</h3>
             <button className="text-xs text-cyan-400 hover:text-cyan-300" onClick={() => alert('Showing all machines')}>View All →</button>
           </div>
           <div className="space-y-3">
             {machines.slice(0, 3).map((machine) => <MachineCard key={machine.machine_id} machine={machine} />)}
           </div>
         </div>
         <div>
           <div className="flex justify-between items-center mb-3">
             <h3 className="font-medium text-gray-200">Recent Alerts</h3>
             <button className="text-xs text-cyan-400 hover:text-cyan-300" onClick={() => alert('Showing all alerts')}>View All →</button>
           </div>
           <div className="space-y-3">
             {alerts.slice(0, 3).map((alert) => <AlertCard key={alert.alert_id} alert={alert} />)}
           </div>
         </div>
       </div>

       <div>
         <div className="flex justify-between items-center mb-3">
           <h3 className="font-medium text-gray-200">Top Recommendations</h3>
           <button className="text-xs text-cyan-400 hover:text-cyan-300" onClick={() => alert('Showing all recommendations')}>View All →</button>
         </div>
         <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
           {recommendations.slice(0, 2).map((rec) => <RecommendationCard key={rec.recommendation_id} recommendation={rec} />)}
         </div>
       </div>
    </motion.div>
  );
};

export default Dashboard;

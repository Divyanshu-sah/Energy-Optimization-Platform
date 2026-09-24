import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useScenario } from '../context/ScenarioContext';
import AlertCard from '../components/ui/AlertCard';
import { Filter, AlertTriangle, CheckCircle } from 'lucide-react';

const Alerts = () => {
  const { data, addEventLog } = useScenario();
  const [filter, setFilter] = useState('all');
  const [alerts, setAlerts] = useState(data.alerts);
  const [acknowledging, setAcknowledging] = useState(null);

  useEffect(() => {
    setAlerts(data.alerts);
  }, [data.alerts]);

  const handleAcknowledge = (alertId) => {
    setAcknowledging(alertId);
    setAlerts((prev) => prev.map((a) => a.alert_id === alertId ? { ...a, status: 'acknowledged' } : a));
    addEventLog(`Alert ${alertId} acknowledged`);
    setAcknowledging(null);
  };

  const filteredAlerts = alerts.filter((a) => {
    if (filter === 'all') return true;
    if (filter === 'critical') return a.severity === 'critical';
    if (filter === 'warning') return a.severity === 'warning';
    if (filter === 'acknowledged') return a.status === 'acknowledged';
    if (filter === 'new') return a.status === 'new';
    return true;
  });

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div className="flex flex-wrap justify-between items-center gap-4">
        <div className="flex gap-2">
          {['all', 'critical', 'warning', 'new', 'acknowledged'].map((f) => (
            <button key={f} onClick={() => setFilter(f)} className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${filter === f ? 'bg-cyan-600 text-white' : 'bg-dark-800 text-gray-400 hover:bg-dark-700'}`}>
              {f === 'all' ? <Filter className="w-3 h-3 inline mr-1" /> : null}
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
        <div className="flex gap-2 text-sm">
          <span className="flex items-center gap-1"><AlertTriangle className="w-4 h-4 text-rose-400" /> {alerts.filter((a) => a.severity === 'critical').length} Critical</span>
          <span className="flex items-center gap-1"><CheckCircle className="w-4 h-4 text-emerald-400" /> {alerts.filter((a) => a.status === 'acknowledged').length} Acknowledged</span>
        </div>
      </div>

      <div className="space-y-3">
        {filteredAlerts.length === 0 ? (
          <div className="text-center py-12 text-gray-500">No alerts found</div>
        ) : (
          filteredAlerts.map((alert) => (
            <AlertCard 
              key={alert.alert_id} 
              alert={alert} 
              onAcknowledge={handleAcknowledge}
              isAcknowledging={acknowledging === alert.alert_id}
            />
          ))
        )}
      </div>
    </motion.div>
  );
};

export default Alerts;

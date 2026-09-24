import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, CheckCircle, Clock, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import StatusBadge from './StatusBadge';

const AlertCard = ({ alert, onAcknowledge, isAcknowledging }) => {
  const [expanded, setExpanded] = useState(false);
  const severityColors = {
    critical: 'border-l-rose-500 bg-rose-500/5',
    warning: 'border-l-amber-500 bg-amber-500/5',
    info: 'border-l-cyan-500 bg-cyan-500/5',
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className={`rounded-lg border border-dark-700 ${severityColors[alert.severity] || severityColors.info} p-4 hover:border-dark-600 transition-all`}
    >
      <div className="flex justify-between items-start">
        <div className="flex gap-3 flex-1">
          <AlertTriangle className={`w-5 h-5 mt-0.5 ${alert.severity === 'critical' ? 'text-rose-400' : 'text-amber-400'}`} />
          <div className="flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h4 className="font-medium text-gray-100">{alert.issue_type.replace('_', ' ').toUpperCase()}</h4>
              <StatusBadge status={alert.severity} size="sm" />
              <span className="text-xs text-gray-500 font-mono">{alert.machine_id}</span>
            </div>
            <p className="text-sm text-gray-300 mt-1">{alert.message}</p>
            <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
              <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{new Date(alert.timestamp).toLocaleTimeString()}</span>
              <button onClick={() => setExpanded(!expanded)} className="flex items-center gap-1 hover:text-cyan-400 transition-colors">
                {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                Details
              </button>
            </div>
            <AnimatePresence>
              {expanded && (
                <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                  <div className="mt-3 p-3 bg-dark-900/50 rounded-lg text-sm">
                    <p className="text-gray-300"><span className="text-cyan-400">Recommended Action:</span> {alert.recommended_action}</p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
        {alert.status === 'new' && (
          <button 
            onClick={() => onAcknowledge?.(alert.alert_id)} 
            disabled={isAcknowledging}
            className="px-3 py-1 text-xs bg-cyan-600/20 hover:bg-cyan-600/40 disabled:bg-cyan-600/10 disabled:text-cyan-400/50 text-cyan-400 rounded-full transition-colors flex items-center gap-1"
          >
            {isAcknowledging ? (
              <>
                <Loader2 className="w-3 h-3 animate-spin" />
                Acknowledging...
              </>
            ) : (
              'Acknowledge'
            )}
          </button>
        )}
        {alert.status === 'acknowledged' && <CheckCircle className="w-5 h-5 text-emerald-400" />}
      </div>
    </motion.div>
  );
};

export default AlertCard;

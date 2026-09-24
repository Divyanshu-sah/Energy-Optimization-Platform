import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, Zap, Settings, Battery, ArrowRight, Check, X, Loader2 } from 'lucide-react';
import StatusBadge from './StatusBadge';

const RecommendationCard = ({ recommendation, onAction, onDismiss, isLoading }) => {
  const categoryIcons = {
    scheduling_optimization: <Settings className="w-4 h-4" />,
    idle_shutdown: <Zap className="w-4 h-4" />,
    maintenance: <Settings className="w-4 h-4" />,
    load_balancing: <Battery className="w-4 h-4" />,
    peak_adjustment: <TrendingUp className="w-4 h-4" />,
  };

  const priorityColors = {
    critical: 'border-rose-500/50 bg-rose-500/5',
    high: 'border-amber-500/50 bg-amber-500/5',
    medium: 'border-cyan-500/50 bg-cyan-500/5',
    low: 'border-gray-500/50 bg-gray-500/5',
  };

  const isApplied = recommendation.status === 'applied';
  const isDismissed = recommendation.status === 'dismissed';

  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      className={`rounded-xl border ${priorityColors[recommendation.priority]} p-4 transition-all group ${isApplied ? 'opacity-60' : ''} ${isDismissed ? 'opacity-40' : ''}`}
    >
      <div className="flex justify-between items-start">
        <div className="flex gap-3 flex-1">
          <div className="p-2 rounded-lg bg-dark-800 group-hover:bg-cyan-600/20 transition-colors">
            {categoryIcons[recommendation.category] || <TrendingUp className="w-4 h-4 text-cyan-400" />}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h4 className="font-medium text-gray-100">{recommendation.title}</h4>
              <StatusBadge status={recommendation.priority} size="sm" />
              {isApplied && <StatusBadge status="applied" size="sm" />}
              {isDismissed && <StatusBadge status="dismissed" size="sm" />}
              <span className="text-xs text-gray-500">{recommendation.machine_id}</span>
            </div>
            <p className="text-sm text-gray-400 mt-1">{recommendation.reason}</p>
            <div className="flex items-center gap-4 mt-2">
              <span className="text-xs text-emerald-400 flex items-center gap-1"><TrendingUp className="w-3 h-3" />Save {recommendation.estimated_savings_percent}%</span>
              {!isApplied && !isDismissed && (
                <div className="flex items-center gap-2">
                  <button 
                    className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition-colors disabled:opacity-50" 
                    onClick={onAction}
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <><Loader2 className="w-3 h-3 animate-spin" /> Applying...</>
                    ) : (
                      <><Check className="w-3 h-3" /> Apply</>
                    )}
                  </button>
                  <button 
                    className="text-xs text-gray-500 hover:text-gray-300 flex items-center gap-1 transition-colors disabled:opacity-50"
                    onClick={onDismiss}
                    disabled={isLoading}
                  >
                    {isLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <X className="w-3 h-3" />}
                  </button>
                </div>
              )}
              {isApplied && (
                <span className="text-xs text-emerald-400 flex items-center gap-1"><Check className="w-3 h-3" /> Applied</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default RecommendationCard;

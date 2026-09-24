import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useScenario } from '../context/ScenarioContext';
import RecommendationCard from '../components/ui/RecommendationCard';
import { Lightbulb, TrendingUp, Zap } from 'lucide-react';

const Optimization = () => {
  const { data } = useScenario();
  const { recommendations } = data;
  const [actionLoading, setActionLoading] = useState(null);

  const handleApply = (rec) => {
    setActionLoading(rec.recommendation_id);
    setTimeout(() => setActionLoading(null), 500);
  };

  const handleDismiss = (rec) => {
    setActionLoading(rec.recommendation_id);
    setTimeout(() => setActionLoading(null), 500);
  };

  const totalSavings = recommendations.reduce((sum, r) => sum + r.estimated_savings_percent, 0) / (recommendations.length || 1);

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <Lightbulb className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400">No recommendations available</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-dark-800/50 rounded-xl border border-dark-700 p-4 text-center">
          <Lightbulb className="w-6 h-6 text-amber-400 mx-auto mb-2" />
          <p className="text-2xl font-bold">{recommendations.length}</p>
          <p className="text-xs text-gray-400">Active Recommendations</p>
        </div>
        <div className="bg-dark-800/50 rounded-xl border border-dark-700 p-4 text-center">
          <TrendingUp className="w-6 h-6 text-emerald-400 mx-auto mb-2" />
          <p className="text-2xl font-bold">{totalSavings.toFixed(1)}%</p>
          <p className="text-xs text-gray-400">Avg. Potential Savings</p>
        </div>
        <div className="bg-dark-800/50 rounded-xl border border-dark-700 p-4 text-center">
          <Zap className="w-6 h-6 text-cyan-400 mx-auto mb-2" />
          <p className="text-2xl font-bold">
            {recommendations.reduce((sum, rec) => sum + (rec.estimated_savings_percent / 100 * 1000), 0).toFixed(0)} kWh
          </p>
          <p className="text-xs text-gray-400">Estimated Monthly Savings</p>
        </div>
      </div>

      <div>
        <h3 className="font-medium text-gray-200 mb-3">Optimization Actions</h3>
        <div className="space-y-3">
          {recommendations.map((rec) => (
            <RecommendationCard 
              key={rec.recommendation_id} 
              recommendation={rec} 
              onAction={() => handleApply(rec)}
              onDismiss={() => handleDismiss(rec)}
              isLoading={actionLoading === rec.recommendation_id}
            />
          ))}
        </div>
      </div>
    </motion.div>
  );
};

export default Optimization;

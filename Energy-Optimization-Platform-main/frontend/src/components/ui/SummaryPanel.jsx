import React from 'react';
import { motion } from 'framer-motion';
import { Brain, Sparkles, FileText } from 'lucide-react';

const SummaryPanel = ({ summary, title }) => {
  const isAI = summary.source === 'sarvam';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-xl border ${isAI ? 'border-cyan-500/30 bg-gradient-to-br from-cyan-900/20 to-dark-800' : 'border-amber-500/30 bg-gradient-to-br from-amber-900/10 to-dark-800'} p-5`}
    >
      <div className="flex items-center gap-2 mb-3">
        {isAI ? <Brain className="w-5 h-5 text-cyan-400" /> : <Sparkles className="w-5 h-5 text-amber-400" />}
        <h3 className="font-semibold text-gray-100">{title || summary.title}</h3>
        {isAI ? (
          <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-600/20 text-cyan-400">Sarvam AI</span>
        ) : (
          <span className="text-xs px-2 py-0.5 rounded-full bg-amber-600/20 text-amber-400">Fallback</span>
        )}
      </div>
      <p className="text-gray-300 leading-relaxed">{summary.summary}</p>
       <div className="mt-4 pt-3 border-t border-dark-700 flex justify-between items-center">
         <button className="text-sm text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition-colors" onClick={() => alert('Generating full report...')}>
           <FileText className="w-4 h-4" /> Full Report
         </button>
         <span className="text-xs text-gray-500">Generated just now</span>
       </div>
    </motion.div>
  );
};

export default SummaryPanel;

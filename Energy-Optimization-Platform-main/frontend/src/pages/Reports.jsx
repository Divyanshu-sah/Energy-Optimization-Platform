import React from 'react';
import { motion } from 'framer-motion';
import { useScenario } from '../context/ScenarioContext';
import SummaryPanel from '../components/ui/SummaryPanel';
import { FileText, Download, Calendar } from 'lucide-react';

const Reports = () => {
  const { data } = useScenario();
  const { summary } = data;

   const reportHistory = [
     { id: 1, date: new Date().toISOString().split('T')[0], title: 'Daily Summary', type: 'AI' },
     { id: 2, date: new Date(Date.now() - 86400000).toISOString().split('T')[0], title: 'Shift Report - Night', type: 'Fallback' },
     { id: 3, date: new Date(Date.now() - 86400000).toISOString().split('T')[0], title: 'Efficiency Analysis', type: 'AI' },
   ];

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <SummaryPanel summary={summary} title="AI-Generated Operational Summary" />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-dark-800/50 rounded-xl border border-dark-700 p-5">
          <div className="flex items-center gap-2 mb-4">
            <FileText className="w-5 h-5 text-cyan-400" />
            <h3 className="font-medium text-gray-200">Shift Energy Report</h3>
          </div>
           <div className="space-y-3">
             <div className="flex justify-between text-sm"><span className="text-gray-400">Total Consumption</span><span className="font-mono">{summary.total_power_kw.toFixed(0)} kWh</span></div>
             <div className="flex justify-between text-sm"><span className="text-gray-400">Waste Estimate</span><span className="font-mono text-amber-400">{((summary.avg_efficiency < 70) ? (summary.total_power_kw * 0.3).toFixed(0) : '0')} kWh ({summary.avg_efficiency < 70 ? ((summary.total_power_kw * 0.3) / summary.total_power_kw * 100).toFixed(1) : '0'}%)</span></div>
             <div className="flex justify-between text-sm"><span className="text-gray-400">Top Offender</span><span className="font-mono">{summary.anomalies_detected > 0 ? 'Machine with highest anomaly' : 'All machines normal'}</span></div>
             <div className="flex justify-between text-sm"><span className="text-gray-400">Savings Opportunity</span><span className="font-mono text-emerald-400">{summary.anomalies_detected > 0 ? '$' + (summary.total_power_kw * 0.1 * 0.15).toFixed(0) : '$0'}</span></div>
           </div>
          <button className="mt-4 w-full py-2 bg-cyan-600/20 hover:bg-cyan-600/40 rounded-lg text-cyan-400 text-sm flex items-center justify-center gap-2 transition-colors"><Download className="w-4 h-4" /> Export Report</button>
        </div>

        <div className="bg-dark-800/50 rounded-xl border border-dark-700 p-5">
          <div className="flex items-center gap-2 mb-4">
            <Calendar className="w-5 h-5 text-cyan-400" />
            <h3 className="font-medium text-gray-200">Recent Reports</h3>
          </div>
          <div className="space-y-2">
            {reportHistory.map((report) => (
              <div key={report.id} className="flex justify-between items-center p-2 hover:bg-dark-700 rounded-lg transition-colors">
                <div><p className="text-sm font-medium">{report.title}</p><p className="text-xs text-gray-500">{report.date}</p></div>
                <div className="flex items-center gap-2"><span className={`text-xs px-2 py-0.5 rounded-full ${report.type === 'AI' ? 'bg-cyan-600/20 text-cyan-400' : 'bg-amber-600/20 text-amber-400'}`}>{report.type}</span><Download className="w-4 h-4 text-gray-500 cursor-pointer hover:text-cyan-400" /></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default Reports;

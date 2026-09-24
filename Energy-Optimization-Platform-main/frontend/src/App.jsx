import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { LayoutDashboard, Cpu, AlertTriangle, TrendingUp, Lightbulb, FileText, Sliders, Zap } from 'lucide-react';
import { ScenarioProvider } from './context/ScenarioContext';
import Dashboard from './pages/Dashboard';
import Machines from './pages/Machines';
import Alerts from './pages/Alerts';
import Forecast from './pages/Forecast';
import Optimization from './pages/Optimization';
import Reports from './pages/Reports';
import Simulator from './pages/Simulator';

const navItems = [
  { path: '/', name: 'Dashboard', icon: <LayoutDashboard className="w-5 h-5" /> },
  { path: '/machines', name: 'Machines', icon: <Cpu className="w-5 h-5" /> },
  { path: '/alerts', name: 'Alerts', icon: <AlertTriangle className="w-5 h-5" /> },
  { path: '/forecast', name: 'Forecast', icon: <TrendingUp className="w-5 h-5" /> },
  { path: '/optimization', name: 'Optimization', icon: <Lightbulb className="w-5 h-5" /> },
  { path: '/reports', name: 'Reports', icon: <FileText className="w-5 h-5" /> },
  { path: '/simulator', name: 'Simulator', icon: <Sliders className="w-5 h-5" /> },
];

const Sidebar = () => {
  const location = useLocation();
  return (
    <aside className="fixed left-0 top-0 h-full w-64 bg-dark-900/95 backdrop-blur-sm border-r border-dark-800 z-50">
      <div className="p-5 border-b border-dark-800">
        <div className="flex items-center gap-2">
          <Zap className="w-8 h-8 text-cyan-400" />
          <span className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-cyan-600 bg-clip-text text-transparent">EnergiX</span>
        </div>
        <p className="text-xs text-gray-500 mt-1">Industrial AI Copilot</p>
      </div>
      <nav className="p-4 space-y-1">
        {navItems.map(item => (
          <Link key={item.path} to={item.path}>
            <div className={`flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all duration-200 ${location.pathname === item.path ? 'bg-cyan-600/20 text-cyan-400 border-l-2 border-cyan-400' : 'text-gray-400 hover:bg-dark-800 hover:text-gray-200'}`}>
              {item.icon}
              <span className="font-medium">{item.name}</span>
            </div>
          </Link>
        ))}
      </nav>
    </aside>
  );
};

const PageWrapper = ({ children }) => {
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }}>
      {children}
    </motion.div>
  );
};

const AppContent = () => {
  const location = useLocation();
  return (
    <div className="min-h-screen bg-dark-950">
      <Sidebar />
      <main className="ml-64 p-6">
        <AnimatePresence mode="wait">
          <Routes location={location} key={location.pathname}>
            <Route path="/" element={<PageWrapper><Dashboard /></PageWrapper>} />
            <Route path="/machines" element={<PageWrapper><Machines /></PageWrapper>} />
            <Route path="/alerts" element={<PageWrapper><Alerts /></PageWrapper>} />
            <Route path="/forecast" element={<PageWrapper><Forecast /></PageWrapper>} />
            <Route path="/optimization" element={<PageWrapper><Optimization /></PageWrapper>} />
            <Route path="/reports" element={<PageWrapper><Reports /></PageWrapper>} />
            <Route path="/simulator" element={<PageWrapper><Simulator /></PageWrapper>} />
          </Routes>
        </AnimatePresence>
      </main>
    </div>
  );
};

function App() {
  return (
    <Router>
      <ScenarioProvider>
        <AppContent />
      </ScenarioProvider>
    </Router>
  );
}

export default App;

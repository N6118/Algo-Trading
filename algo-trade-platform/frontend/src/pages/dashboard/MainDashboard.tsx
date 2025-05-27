import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  AlertTriangle, 
  ArrowRight, 
  BarChart2, 
  Check, 
  ChevronRight, 
  Clock, 
  Cpu, 
  TrendingDown, 
  TrendingUp 
} from 'lucide-react';

import DashboardCard from '../../components/common/DashboardCard';
import { PerformanceChart } from '../../components/charts/PerformanceChart';
import { ActiveTradesTable } from '../../components/trade/ActiveTradesTable';
import { StrategyStatusList } from '../../components/strategy/StrategyStatusList';
import { useTradingData } from '../../context/TradingDataContext';
import { formatCurrency } from '../../utils/formatters';

const MainDashboard = () => {
  const { 
    dailyPnL, 
    weeklyPnL, 
    monthlyPnL, 
    allTimePnL, 
    activeTrades, 
    activeStrategies 
  } = useTradingData();
  
  const [timeRange, setTimeRange] = useState<'1d' | '1w' | '1m' | '3m' | '1y'>('1w');
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-500 dark:text-gray-400">Last updated:</span>
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {new Date().toLocaleTimeString()}
          </span>
          <button className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-500">
            Refresh
          </button>
        </div>
      </div>
      
      {/* Performance Summary Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <DashboardCard
          title="Daily P&L"
          value={formatCurrency(dailyPnL)}
          change={dailyPnL >= 0 ? '+2.5%' : '-2.5%'}
          trend={dailyPnL >= 0 ? 'up' : 'down'}
          icon={<BarChart2 size={20} className="text-blue-500" />}
        />
        <DashboardCard
          title="Weekly P&L"
          value={formatCurrency(weeklyPnL)}
          change={weeklyPnL >= 0 ? '+4.2%' : '-4.2%'}
          trend={weeklyPnL >= 0 ? 'up' : 'down'}
          icon={<BarChart2 size={20} className="text-blue-500" />}
        />
        <DashboardCard
          title="Monthly P&L"
          value={formatCurrency(monthlyPnL)}
          change={monthlyPnL >= 0 ? '+12.8%' : '-12.8%'}
          trend={monthlyPnL >= 0 ? 'up' : 'down'}
          icon={<BarChart2 size={20} className="text-blue-500" />}
        />
        <DashboardCard
          title="All-Time P&L"
          value={formatCurrency(allTimePnL)}
          change={allTimePnL >= 0 ? '+42.3%' : '-42.3%'}
          trend={allTimePnL >= 0 ? 'up' : 'down'}
          icon={<BarChart2 size={20} className="text-blue-500" />}
        />
      </div>
      
      {/* Performance Chart */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white">Performance Chart</h2>
          <div className="flex items-center space-x-2">
            <button 
              onClick={() => setTimeRange('1d')} 
              className={`px-2 py-1 text-xs rounded-md ${timeRange === '1d' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'}`}
            >
              1D
            </button>
            <button 
              onClick={() => setTimeRange('1w')} 
              className={`px-2 py-1 text-xs rounded-md ${timeRange === '1w' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'}`}
            >
              1W
            </button>
            <button 
              onClick={() => setTimeRange('1m')} 
              className={`px-2 py-1 text-xs rounded-md ${timeRange === '1m' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'}`}
            >
              1M
            </button>
            <button 
              onClick={() => setTimeRange('3m')} 
              className={`px-2 py-1 text-xs rounded-md ${timeRange === '3m' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'}`}
            >
              3M
            </button>
            <button 
              onClick={() => setTimeRange('1y')} 
              className={`px-2 py-1 text-xs rounded-md ${timeRange === '1y' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'}`}
            >
              1Y
            </button>
          </div>
        </div>
        <div className="p-4 h-80">
          <PerformanceChart timeRange={timeRange} />
        </div>
      </div>
      
      {/* Grid Layout for Trade and Strategy Data */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Trades Section */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white">Active Trades</h2>
            <Link 
              to="/trades" 
              className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-500 flex items-center"
            >
              View all <ChevronRight size={16} />
            </Link>
          </div>
          <div className="p-4">
            <ActiveTradesTable trades={activeTrades} limit={5} />
          </div>
        </div>
        
        {/* Strategy Status Section */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white">Strategy Status</h2>
            <Link 
              to="/strategy" 
              className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-500 flex items-center"
            >
              View all <ChevronRight size={16} />
            </Link>
          </div>
          <div className="p-4">
            <StrategyStatusList strategies={activeStrategies} />
          </div>
        </div>
      </div>
      
      {/* System Status Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white">System Status</h2>
        </div>
        <div className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-900">
              <div className="flex items-start">
                <div className="flex-shrink-0 bg-green-100 dark:bg-green-800 p-2 rounded-md">
                  <Check size={20} className="text-green-600 dark:text-green-400" />
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-gray-900 dark:text-white">Trade Execution</h3>
                  <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">System operational</p>
                </div>
              </div>
            </div>
            
            <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-900">
              <div className="flex items-start">
                <div className="flex-shrink-0 bg-green-100 dark:bg-green-800 p-2 rounded-md">
                  <Check size={20} className="text-green-600 dark:text-green-400" />
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-gray-900 dark:text-white">Market Data</h3>
                  <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">All feeds online</p>
                </div>
              </div>
            </div>
            
            <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-900">
              <div className="flex items-start">
                <div className="flex-shrink-0 bg-yellow-100 dark:bg-yellow-800 p-2 rounded-md">
                  <AlertTriangle size={20} className="text-yellow-600 dark:text-yellow-400" />
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-gray-900 dark:text-white">API Latency</h3>
                  <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">Above normal (124ms)</p>
                </div>
              </div>
            </div>
            
            <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-900">
              <div className="flex items-start">
                <div className="flex-shrink-0 bg-green-100 dark:bg-green-800 p-2 rounded-md">
                  <Clock size={20} className="text-green-600 dark:text-green-400" />
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-gray-900 dark:text-white">Strategy Runners</h3>
                  <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">All running (12/12)</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MainDashboard;
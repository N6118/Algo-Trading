import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  AlertTriangle, 
  BarChart2, 
  Check, 
  ChevronRight, 
  Clock, 
  RefreshCw
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
    activeStrategies,
    isLoading,
    error,
    refreshData
  } = useTradingData();
  
  const [timeRange, setTimeRange] = useState<'1d' | '1w' | '1m' | '3m' | '1y'>('1w');
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  // Update last updated time periodically
  useEffect(() => {
    const interval = setInterval(() => {
      setLastUpdated(new Date());
    }, 60000); // Update every minute
    
    return () => clearInterval(interval);
  }, []);
  
  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await refreshData();
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to refresh data:', error);
    } finally {
      setIsRefreshing(false);
    }
  };
  
  const calculatePnLChange = (current: number) => {
    // Mock calculation for percentage change
    const change = (Math.random() - 0.5) * 10; // Random change for demo
    return {
      value: `${change > 0 ? '+' : ''}${change.toFixed(1)}%`,
      trend: change > 0 ? 'up' as const : change < 0 ? 'down' as const : 'neutral' as const
    };
  };
  
  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <AlertTriangle className="mx-auto h-12 w-12 text-red-500 mb-4" />
          <h2 className="text-xl font-medium text-gray-900 dark:text-white mb-2">
            Failed to load dashboard data
          </h2>
          <p className="text-gray-500 dark:text-gray-400 mb-4">{error}</p>
          <button
            onClick={handleRefresh}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors duration-200"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
            <span>Last updated:</span>
            <span className="font-medium text-gray-700 dark:text-gray-300">
              {lastUpdated.toLocaleTimeString()}
            </span>
          </div>
          <button 
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center space-x-2 text-sm text-blue-600 dark:text-blue-400 hover:text-blue-500 disabled:opacity-50 transition-colors duration-200"
          >
            <RefreshCw size={16} className={isRefreshing ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>
      
      {/* Performance Summary Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <DashboardCard
          title="Daily P&L"
          value={formatCurrency(dailyPnL)}
          change={calculatePnLChange(dailyPnL).value}
          trend={calculatePnLChange(dailyPnL).trend}
          icon={<BarChart2 size={20} className="text-blue-500" />}
          loading={isLoading}
        />
        <DashboardCard
          title="Weekly P&L"
          value={formatCurrency(weeklyPnL)}
          change={calculatePnLChange(weeklyPnL).value}
          trend={calculatePnLChange(weeklyPnL).trend}
          icon={<BarChart2 size={20} className="text-blue-500" />}
          loading={isLoading}
        />
        <DashboardCard
          title="Monthly P&L"
          value={formatCurrency(monthlyPnL)}
          change={calculatePnLChange(monthlyPnL).value}
          trend={calculatePnLChange(monthlyPnL).trend}
          icon={<BarChart2 size={20} className="text-blue-500" />}
          loading={isLoading}
        />
        <DashboardCard
          title="All-Time P&L"
          value={formatCurrency(allTimePnL)}
          change={calculatePnLChange(allTimePnL).value}
          trend={calculatePnLChange(allTimePnL).trend}
          icon={<BarChart2 size={20} className="text-blue-500" />}
          loading={isLoading}
        />
      </div>
      
      {/* Performance Chart */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white">Performance Chart</h2>
          <div className="flex items-center space-x-2">
            {(['1d', '1w', '1m', '3m', '1y'] as const).map((range) => (
              <button 
                key={range}
                onClick={() => setTimeRange(range)} 
                className={`px-2 py-1 text-xs rounded-md transition-colors duration-200 ${
                  timeRange === range 
                    ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400' 
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                {range.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
        <div className="p-4 h-80">
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <PerformanceChart timeRange={timeRange} />
          )}
        </div>
      </div>
      
      {/* Grid Layout for Trade and Strategy Data */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Trades Section */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white">
              Active Trades
              {!isLoading && (
                <span className="ml-2 text-sm font-normal text-gray-500 dark:text-gray-400">
                  ({activeTrades.length})
                </span>
              )}
            </h2>
            <Link 
              to="/trades" 
              className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-500 flex items-center transition-colors duration-200"
            >
              View all <ChevronRight size={16} />
            </Link>
          </div>
          <div className="p-4">
            {isLoading ? (
              <div className="space-y-4">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="animate-pulse flex items-center space-x-4">
                    <div className="rounded-full bg-gray-200 dark:bg-gray-700 h-8 w-8"></div>
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                      <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <ActiveTradesTable trades={activeTrades} limit={5} />
            )}
          </div>
        </div>
        
        {/* Strategy Status Section */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white">
              Strategy Status
              {!isLoading && (
                <span className="ml-2 text-sm font-normal text-gray-500 dark:text-gray-400">
                  ({activeStrategies.length} active)
                </span>
              )}
            </h2>
            <Link 
              to="/strategy" 
              className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-500 flex items-center transition-colors duration-200"
            >
              View all <ChevronRight size={16} />
            </Link>
          </div>
          <div className="p-4">
            {isLoading ? (
              <div className="space-y-4">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="animate-pulse flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-750 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="rounded-full bg-gray-200 dark:bg-gray-700 h-5 w-5"></div>
                      <div className="space-y-2">
                        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-32"></div>
                        <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-24"></div>
                      </div>
                    </div>
                    <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-16"></div>
                  </div>
                ))}
              </div>
            ) : (
              <StrategyStatusList strategies={activeStrategies} />
            )}
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
            {[
              { name: 'Trade Execution', status: 'operational', message: 'System operational' },
              { name: 'Market Data', status: 'operational', message: 'All feeds online' },
              { name: 'API Latency', status: 'warning', message: 'Above normal (124ms)' },
              { name: 'Strategy Runners', status: 'operational', message: 'All running (12/12)' }
            ].map((item) => (
              <div 
                key={item.name}
                className={`p-4 rounded-lg border ${
                  item.status === 'operational' 
                    ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-900' 
                    : 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-900'
                }`}
              >
                <div className="flex items-start">
                  <div className={`flex-shrink-0 p-2 rounded-md ${
                    item.status === 'operational' 
                      ? 'bg-green-100 dark:bg-green-800' 
                      : 'bg-yellow-100 dark:bg-yellow-800'
                  }`}>
                    {item.status === 'operational' ? (
                      <Check size={20} className="text-green-600 dark:text-green-400" />
                    ) : (
                      <AlertTriangle size={20} className="text-yellow-600 dark:text-yellow-400" />
                    )}
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-gray-900 dark:text-white">{item.name}</h3>
                    <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">{item.message}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MainDashboard;
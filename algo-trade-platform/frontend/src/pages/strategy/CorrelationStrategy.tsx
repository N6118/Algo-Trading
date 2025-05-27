import { useState } from 'react';
import { ArrowRight, TrendingUp } from 'lucide-react';
import DashboardCard from '../../components/common/DashboardCard';

const CorrelationStrategy = () => {
  const [primarySymbol, setPrimarySymbol] = useState('');
  const [correlatedSymbol, setCorrelatedSymbol] = useState('');
  const [timeframe, setTimeframe] = useState('1d');
  const [correlationPeriod, setCorrelationPeriod] = useState(20);
  
  return (
    <div className="max-w-4xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        Correlation Strategy Builder
      </h1>
      
      <div className="space-y-6">
        {/* Symbol Selection */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Symbol Selection</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Primary Symbol
              </label>
              <input
                type="text"
                value={primarySymbol}
                onChange={(e) => setPrimarySymbol(e.target.value.toUpperCase())}
                className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                placeholder="e.g., SPY"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Correlated Symbol
              </label>
              <input
                type="text"
                value={correlatedSymbol}
                onChange={(e) => setCorrelatedSymbol(e.target.value.toUpperCase())}
                className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                placeholder="e.g., QQQ"
              />
            </div>
          </div>
        </div>
        
        {/* Correlation Parameters */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Correlation Parameters</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Timeframe
              </label>
              <select
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
              >
                <option value="1m">1 Minute</option>
                <option value="5m">5 Minutes</option>
                <option value="15m">15 Minutes</option>
                <option value="1h">1 Hour</option>
                <option value="4h">4 Hours</option>
                <option value="1d">1 Day</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Correlation Period
              </label>
              <input
                type="number"
                value={correlationPeriod}
                onChange={(e) => setCorrelationPeriod(parseInt(e.target.value))}
                className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                min="5"
                max="100"
              />
            </div>
          </div>
        </div>
        
        {/* Strategy Rules */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Strategy Rules</h2>
          
          <div className="space-y-4">
            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <h3 className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-2">Buy Signal Conditions</h3>
              <ul className="list-disc list-inside text-sm text-blue-700 dark:text-blue-300 space-y-1">
                <li>Primary symbol price &gt; SH of primary symbol</li>
                <li>Correlated symbol price &lt; SL of correlated symbol</li>
                <li>Correlation coefficient &gt; 0.7 over the selected period</li>
              </ul>
            </div>
            
            <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <h3 className="text-sm font-medium text-red-800 dark:text-red-200 mb-2">Sell Signal Conditions</h3>
              <ul className="list-disc list-inside text-sm text-red-700 dark:text-red-300 space-y-1">
                <li>Primary symbol price &lt; SL of primary symbol</li>
                <li>Correlated symbol price &gt; SH of correlated symbol</li>
                <li>Correlation coefficient &lt; 0.3 over the selected period</li>
              </ul>
            </div>
          </div>
        </div>
        
        {/* Performance Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <DashboardCard
            title="Correlation Coefficient"
            value="0.85"
            trend="up"
            icon={<TrendingUp className="w-5 h-5" />}
          />
          
          <DashboardCard
            title="Signal Accuracy"
            value="76%"
            trend="up"
            icon={<ArrowRight className="w-5 h-5" />}
          />
          
          <DashboardCard
            title="Average Return"
            value="2.4%"
            trend="up"
            icon={<TrendingUp className="w-5 h-5" />}
          />
        </div>
        
        {/* Action Buttons */}
        <div className="flex justify-end space-x-3">
          <button
            type="button"
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            Reset
          </button>
          <button
            type="button"
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
          >
            Create Strategy
          </button>
        </div>
      </div>
    </div>
  );
};

export default CorrelationStrategy;
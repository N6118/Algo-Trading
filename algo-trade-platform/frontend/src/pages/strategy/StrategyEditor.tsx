import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AlertTriangle, Save, X } from 'lucide-react';

const StrategyEditor = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditing = Boolean(id);
  
  const [form, setForm] = useState({
    name: '',
    type: 'momentum',
    symbols: '',
    description: '',
    parameters: {
      timeframe: '1d',
      lookbackPeriod: 20,
      signalThreshold: 2,
    },
    riskManagement: {
      maxPositionSize: 100000,
      stopLossPercent: 2,
      takeProfitPercent: 4,
      maxDrawdownPercent: 10,
    }
  });
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Handle form submission
    console.log('Form submitted:', form);
  };
  
  return (
    <div className="max-w-4xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {isEditing ? 'Edit Strategy' : 'Create New Strategy'}
        </h1>
        <div className="flex space-x-3">
          <button
            onClick={() => navigate(-1)}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 flex items-center"
          >
            <Save size={16} className="mr-2" />
            Save Strategy
          </button>
        </div>
      </div>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Basic Information</h2>
          <div className="grid grid-cols-1 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Strategy Name
              </label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                placeholder="Enter strategy name"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Strategy Type
              </label>
              <select
                value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
              >
                <option value="momentum">Momentum</option>
                <option value="mean_reversion">Mean Reversion</option>
                <option value="trend">Trend Following</option>
                <option value="breakout">Breakout</option>
                <option value="correlation">Correlation</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Trading Symbols
              </label>
              <input
                type="text"
                value={form.symbols}
                onChange={(e) => setForm({ ...form, symbols: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                placeholder="Enter symbols (comma-separated)"
              />
              <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                Example: AAPL, MSFT, GOOG
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Description
              </label>
              <textarea
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                rows={3}
                className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                placeholder="Describe your strategy"
              />
            </div>
          </div>
        </div>
        
        {/* Strategy Parameters */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Strategy Parameters</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Timeframe
              </label>
              <select
                value={form.parameters.timeframe}
                onChange={(e) => setForm({
                  ...form,
                  parameters: { ...form.parameters, timeframe: e.target.value }
                })}
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
                Lookback Period
              </label>
              <input
                type="number"
                value={form.parameters.lookbackPeriod}
                onChange={(e) => setForm({
                  ...form,
                  parameters: { ...form.parameters, lookbackPeriod: parseInt(e.target.value) }
                })}
                className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Signal Threshold
              </label>
              <input
                type="number"
                value={form.parameters.signalThreshold}
                onChange={(e) => setForm({
                  ...form,
                  parameters: { ...form.parameters, signalThreshold: parseFloat(e.target.value) }
                })}
                className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                step="0.1"
              />
            </div>
          </div>
        </div>
        
        {/* Risk Management */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Risk Management</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Max Position Size ($)
              </label>
              <input
                type="number"
                value={form.riskManagement.maxPositionSize}
                onChange={(e) => setForm({
                  ...form,
                  riskManagement: { ...form.riskManagement, maxPositionSize: parseInt(e.target.value) }
                })}
                className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Stop Loss (%)
              </label>
              <input
                type="number"
                value={form.riskManagement.stopLossPercent}
                onChange={(e) => setForm({
                  ...form,
                  riskManagement: { ...form.riskManagement, stopLossPercent: parseFloat(e.target.value) }
                })}
                className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                step="0.1"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Take Profit (%)
              </label>
              <input
                type="number"
                value={form.riskManagement.takeProfitPercent}
                onChange={(e) => setForm({
                  ...form,
                  riskManagement: { ...form.riskManagement, takeProfitPercent: parseFloat(e.target.value) }
                })}
                className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                step="0.1"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Max Drawdown (%)
              </label>
              <input
                type="number"
                value={form.riskManagement.maxDrawdownPercent}
                onChange={(e) => setForm({
                  ...form,
                  riskManagement: { ...form.riskManagement, maxDrawdownPercent: parseFloat(e.target.value) }
                })}
                className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                step="0.1"
              />
            </div>
          </div>
        </div>
        
        {/* Warning Message */}
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border-l-4 border-yellow-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <AlertTriangle className="h-5 w-5 text-yellow-400" aria-hidden="true" />
            </div>
            <div className="ml-3">
              <p className="text-sm text-yellow-700 dark:text-yellow-200">
                Please review all parameters carefully before saving. Strategy changes may affect ongoing trades.
              </p>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
};

export default StrategyEditor;
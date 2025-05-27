import { useState } from 'react';
import { AlertTriangle, ArrowDown, ArrowUp, Check, TrendingUp } from 'lucide-react';
import DashboardCard from '../../components/common/DashboardCard';
import { formatCurrency } from '../../utils/formatters';

const PreTradeAnalysis = () => {
  const [form, setForm] = useState({
    symbol: '',
    direction: 'long',
    quantity: '',
    entryPrice: '',
    stopLoss: '',
    takeProfit: '',
  });
  
  const [analysis, setAnalysis] = useState<{
    riskAmount: number;
    potentialProfit: number;
    riskRewardRatio: number;
    marginRequired: number;
    positionSize: number;
    maxLoss: number;
  } | null>(null);
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Calculate analysis
    const quantity = parseFloat(form.quantity);
    const entryPrice = parseFloat(form.entryPrice);
    const stopLoss = parseFloat(form.stopLoss);
    const takeProfit = parseFloat(form.takeProfit);
    
    const riskAmount = Math.abs(entryPrice - stopLoss) * quantity;
    const potentialProfit = Math.abs(takeProfit - entryPrice) * quantity;
    const riskRewardRatio = potentialProfit / riskAmount;
    const positionSize = entryPrice * quantity;
    const marginRequired = positionSize * 0.5; // Example: 50% margin requirement
    const maxLoss = riskAmount;
    
    setAnalysis({
      riskAmount,
      potentialProfit,
      riskRewardRatio,
      marginRequired,
      positionSize,
      maxLoss,
    });
  };
  
  return (
    <div className="max-w-4xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        Pre-Trade Analysis
      </h1>
      
      <div className="space-y-6">
        {/* Trade Parameters Form */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Trade Parameters</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Symbol
                </label>
                <input
                  type="text"
                  value={form.symbol}
                  onChange={(e) => setForm({ ...form, symbol: e.target.value.toUpperCase() })}
                  className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                  placeholder="e.g., AAPL"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Direction
                </label>
                <select
                  value={form.direction}
                  onChange={(e) => setForm({ ...form, direction: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                >
                  <option value="long">Long</option>
                  <option value="short">Short</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Quantity
                </label>
                <input
                  type="number"
                  value={form.quantity}
                  onChange={(e) => setForm({ ...form, quantity: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                  placeholder="Number of shares"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Entry Price
                </label>
                <input
                  type="number"
                  value={form.entryPrice}
                  onChange={(e) => setForm({ ...form, entryPrice: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                  placeholder="Price per share"
                  step="0.01"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Stop Loss
                </label>
                <input
                  type="number"
                  value={form.stopLoss}
                  onChange={(e) => setForm({ ...form, stopLoss: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                  placeholder="Stop loss price"
                  step="0.01"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Take Profit
                </label>
                <input
                  type="number"
                  value={form.takeProfit}
                  onChange={(e) => setForm({ ...form, takeProfit: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                  placeholder="Take profit price"
                  step="0.01"
                  required
                />
              </div>
            </div>
            
            <div className="flex justify-end">
              <button
                type="submit"
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
              >
                Analyze Trade
              </button>
            </div>
          </form>
        </div>
        
        {analysis && (
          <>
            {/* Analysis Results */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <DashboardCard
                title="Risk/Reward Ratio"
                value={analysis.riskRewardRatio.toFixed(2)}
                trend={analysis.riskRewardRatio >= 2 ? 'up' : 'down'}
                icon={<TrendingUp className="w-5 h-5" />}
              />
              
              <DashboardCard
                title="Position Size"
                value={formatCurrency(analysis.positionSize)}
                icon={<ArrowUp className="w-5 h-5" />}
              />
              
              <DashboardCard
                title="Margin Required"
                value={formatCurrency(analysis.marginRequired)}
                icon={<ArrowDown className="w-5 h-5" />}
              />
            </div>
            
            {/* Risk Analysis */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
              <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Risk Analysis</h2>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-500 dark:text-gray-400">Risk Amount</div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {formatCurrency(analysis.riskAmount)}
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-500 dark:text-gray-400">Potential Profit</div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {formatCurrency(analysis.potentialProfit)}
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-500 dark:text-gray-400">Maximum Loss</div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {formatCurrency(analysis.maxLoss)}
                  </div>
                </div>
              </div>
            </div>
            
            {/* Trade Checklist */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
              <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Trade Checklist</h2>
              
              <div className="space-y-3">
                <div className="flex items-center">
                  {analysis.riskRewardRatio >= 2 ? (
                    <Check size={16} className="text-green-500" />
                  ) : (
                    <AlertTriangle size={16} className="text-yellow-500" />
                  )}
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                    Risk/Reward ratio is {analysis.riskRewardRatio >= 2 ? 'acceptable' : 'below recommended 2:1'}
                  </span>
                </div>
                
                <div className="flex items-center">
                  {analysis.riskAmount <= 1000 ? (
                    <Check size={16} className="text-green-500" />
                  ) : (
                    <AlertTriangle size={16} className="text-yellow-500" />
                  )}
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                    Risk amount is {analysis.riskAmount <= 1000 ? 'within' : 'exceeds'} maximum per trade
                  </span>
                </div>
                
                <div className="flex items-center">
                  {analysis.marginRequired <= 25000 ? (
                    <Check size={16} className="text-green-500" />
                  ) : (
                    <AlertTriangle size={16} className="text-yellow-500" />
                  )}
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                    Margin requirement is {analysis.marginRequired <= 25000 ? 'within' : 'exceeds'} available funds
                  </span>
                </div>
              </div>
            </div>
            
            {/* Action Buttons */}
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Save Analysis
              </button>
              <button
                type="button"
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
              >
                Place Trade
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default PreTradeAnalysis;
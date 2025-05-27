import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { 
  ArrowDown, 
  ArrowUp, 
  Clock, 
  Edit2, 
  FileText, 
  TrendingUp, 
  X 
} from 'lucide-react';
import { useTradingData } from '../../context/TradingDataContext';
import { formatCurrency, formatDateTime } from '../../utils/formatters';
import PerformanceChart from '../../components/charts/PerformanceChart';

const TradeDetail = () => {
  const { id } = useParams();
  const { activeTrades } = useTradingData();
  const trade = activeTrades.find(t => t.id === id);
  
  const [showNoteForm, setShowNoteForm] = useState(false);
  const [note, setNote] = useState('');
  
  if (!trade) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <h2 className="text-xl font-medium text-gray-900 dark:text-white">Trade not found</h2>
          <p className="mt-2 text-gray-500 dark:text-gray-400">
            The trade you're looking for doesn't exist or has been closed.
          </p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Trade Details
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            ID: {trade.id}
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700">
            Edit Trade
          </button>
          <button className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700">
            Close Trade
          </button>
        </div>
      </div>
      
      {/* Trade Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Symbol</div>
          <div className="mt-1 flex items-center">
            <div className="text-2xl font-semibold text-gray-900 dark:text-white">{trade.symbol}</div>
            <div className={`ml-2 px-2 py-1 text-xs font-medium rounded-full ${
              trade.direction === 'long'
                ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
                : 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200'
            }`}>
              {trade.direction.toUpperCase()}
            </div>
          </div>
          <div className="mt-1 text-sm text-gray-500 dark:text-gray-400">{trade.strategyName}</div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Position Size</div>
          <div className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">
            {trade.quantity} shares
          </div>
          <div className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {formatCurrency(trade.quantity * trade.currentPrice)} total value
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Entry Price</div>
          <div className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">
            {formatCurrency(trade.entryPrice)}
          </div>
          <div className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {formatDateTime(trade.entryTime)}
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Current P&L</div>
          <div className={`mt-1 text-2xl font-semibold ${
            trade.pnl > 0 
              ? 'text-green-600 dark:text-green-400' 
              : 'text-red-600 dark:text-red-400'
          }`}>
            {formatCurrency(trade.pnl)}
          </div>
          <div className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {((trade.pnl / (trade.entryPrice * trade.quantity)) * 100).toFixed(2)}% return
          </div>
        </div>
      </div>
      
      {/* Price Chart */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="p-6">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Price Action</h2>
          <div className="h-96">
            <PerformanceChart timeRange="1d" />
          </div>
        </div>
      </div>
      
      {/* Trade Parameters */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="p-6">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Risk Management</h2>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <div className="text-sm text-gray-500 dark:text-gray-400">Stop Loss</div>
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  {formatCurrency(trade.stopLoss || 0)}
                </div>
              </div>
              <div className="flex justify-between items-center">
                <div className="text-sm text-gray-500 dark:text-gray-400">Take Profit</div>
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  {formatCurrency(trade.takeProfit || 0)}
                </div>
              </div>
              <div className="flex justify-between items-center">
                <div className="text-sm text-gray-500 dark:text-gray-400">Risk Amount</div>
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  {formatCurrency(trade.risk)}
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium text-gray-900 dark:text-white">Trade Notes</h2>
              <button
                onClick={() => setShowNoteForm(!showNoteForm)}
                className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
              >
                <Edit2 size={16} />
              </button>
            </div>
            
            {showNoteForm ? (
              <div className="space-y-4">
                <textarea
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  rows={4}
                  className="block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                  placeholder="Add a note about this trade..."
                />
                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => setShowNoteForm(false)}
                    className="px-3 py-1 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => {
                      // Handle save note
                      setShowNoteForm(false);
                    }}
                    className="px-3 py-1 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
                  >
                    Save Note
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-sm text-gray-500 dark:text-gray-400">
                No notes added yet.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TradeDetail;
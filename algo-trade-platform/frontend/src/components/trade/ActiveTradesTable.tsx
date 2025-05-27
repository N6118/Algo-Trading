import { useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  ArrowDown, 
  ArrowUp, 
  ChevronDown, 
  ChevronUp, 
  CircleOff, 
  Clock, 
  ExternalLink, 
  MoreHorizontal, 
  TrendingDown, 
  TrendingUp 
} from 'lucide-react';
import { Trade } from '../../types/trade';
import { formatCurrency, formatNumber } from '../../utils/formatters';

interface ActiveTradesTableProps {
  trades: Trade[];
  limit?: number;
}

export const ActiveTradesTable = ({ trades, limit }: ActiveTradesTableProps) => {
  const [sortField, setSortField] = useState<keyof Trade>('entryTime');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [expandedTradeId, setExpandedTradeId] = useState<string | null>(null);
  
  const displayedTrades = limit ? trades.slice(0, limit) : trades;
  
  const handleSort = (field: keyof Trade) => {
    if (field === sortField) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };
  
  const getSortedTrades = () => {
    return [...displayedTrades].sort((a, b) => {
      let aValue: any = a[sortField];
      let bValue: any = b[sortField];
      
      if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }
      
      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  };
  
  const renderSortIcon = (field: keyof Trade) => {
    if (field !== sortField) return null;
    
    return sortDirection === 'asc' ? (
      <ChevronUp size={16} className="ml-1" />
    ) : (
      <ChevronDown size={16} className="ml-1" />
    );
  };
  
  if (trades.length === 0) {
    return (
      <div className="py-8 text-center text-gray-500 dark:text-gray-400">
        No active trades found.
      </div>
    );
  }
  
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-700">
          <tr>
            <th 
              scope="col" 
              className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider cursor-pointer"
              onClick={() => handleSort('symbol')}
            >
              <div className="flex items-center">
                Symbol
                {renderSortIcon('symbol')}
              </div>
            </th>
            <th 
              scope="col" 
              className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider cursor-pointer"
              onClick={() => handleSort('direction')}
            >
              <div className="flex items-center">
                Direction
                {renderSortIcon('direction')}
              </div>
            </th>
            <th 
              scope="col" 
              className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider cursor-pointer"
              onClick={() => handleSort('quantity')}
            >
              <div className="flex items-center">
                Quantity
                {renderSortIcon('quantity')}
              </div>
            </th>
            <th 
              scope="col" 
              className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider cursor-pointer"
              onClick={() => handleSort('entryPrice')}
            >
              <div className="flex items-center">
                Entry Price
                {renderSortIcon('entryPrice')}
              </div>
            </th>
            <th 
              scope="col" 
              className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider cursor-pointer"
              onClick={() => handleSort('currentPrice')}
            >
              <div className="flex items-center">
                Current
                {renderSortIcon('currentPrice')}
              </div>
            </th>
            <th 
              scope="col" 
              className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider cursor-pointer"
              onClick={() => handleSort('pnl')}
            >
              <div className="flex items-center">
                P&L
                {renderSortIcon('pnl')}
              </div>
            </th>
            <th 
              scope="col" 
              className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider"
            >
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
          {getSortedTrades().map((trade) => (
            <>
              <tr key={trade.id} className="hover:bg-gray-50 dark:hover:bg-gray-750">
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-8 w-8 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-xs font-medium text-gray-800 dark:text-gray-200">
                      {trade.symbol.substring(0, 2)}
                    </div>
                    <div className="ml-3">
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {trade.symbol}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {trade.strategyName}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className={`flex items-center text-sm font-medium ${
                    trade.direction === 'long' 
                      ? 'text-green-600 dark:text-green-400' 
                      : 'text-red-600 dark:text-red-400'
                  }`}>
                    {trade.direction === 'long' ? (
                      <ArrowUp size={16} className="mr-1" />
                    ) : (
                      <ArrowDown size={16} className="mr-1" />
                    )}
                    {trade.direction.toUpperCase()}
                  </div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                  {formatNumber(trade.quantity)}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                  {formatCurrency(trade.entryPrice)}
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className="flex items-center">
                    <span className="text-sm text-gray-900 dark:text-white">
                      {formatCurrency(trade.currentPrice)}
                    </span>
                    <span className={`ml-2 flex items-center text-xs ${
                      trade.currentPrice > trade.entryPrice 
                        ? 'text-green-600 dark:text-green-400' 
                        : trade.currentPrice < trade.entryPrice 
                        ? 'text-red-600 dark:text-red-400' 
                        : 'text-gray-500 dark:text-gray-400'
                    }`}>
                      {trade.currentPrice > trade.entryPrice ? (
                        <TrendingUp size={12} className="mr-1" />
                      ) : trade.currentPrice < trade.entryPrice ? (
                        <TrendingDown size={12} className="mr-1" />
                      ) : null}
                      {((trade.currentPrice - trade.entryPrice) / trade.entryPrice * 100).toFixed(2)}%
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className={`text-sm font-medium ${
                    trade.pnl > 0 
                      ? 'text-green-600 dark:text-green-400' 
                      : trade.pnl < 0 
                      ? 'text-red-600 dark:text-red-400' 
                      : 'text-gray-900 dark:text-white'
                  }`}>
                    {formatCurrency(trade.pnl)}
                  </div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-medium">
                  <div className="flex items-center justify-end space-x-2">
                    <button 
                      onClick={() => setExpandedTradeId(expandedTradeId === trade.id ? null : trade.id)}
                      className="text-gray-400 hover:text-gray-500 dark:text-gray-500 dark:hover:text-gray-400"
                    >
                      {expandedTradeId === trade.id ? (
                        <ChevronUp size={18} />
                      ) : (
                        <ChevronDown size={18} />
                      )}
                    </button>
                    <Link
                      to={`/trades/${trade.id}`}
                      className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                    >
                      <ExternalLink size={16} />
                    </Link>
                    <button className="text-gray-400 hover:text-gray-500 dark:text-gray-500 dark:hover:text-gray-400">
                      <MoreHorizontal size={18} />
                    </button>
                  </div>
                </td>
              </tr>
              {expandedTradeId === trade.id && (
                <tr className="bg-gray-50 dark:bg-gray-750">
                  <td colSpan={7} className="px-4 py-3">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <div className="text-xs font-medium text-gray-500 dark:text-gray-400">
                          Entry Time
                        </div>
                        <div className="mt-1 flex items-center text-sm text-gray-900 dark:text-white">
                          <Clock size={14} className="mr-1 text-gray-400" />
                          {new Date(trade.entryTime).toLocaleString()}
                        </div>
                      </div>
                      
                      <div>
                        <div className="text-xs font-medium text-gray-500 dark:text-gray-400">
                          Stop Loss
                        </div>
                        <div className="mt-1 text-sm text-gray-900 dark:text-white">
                          {trade.stopLoss ? formatCurrency(trade.stopLoss) : 'None'}
                        </div>
                      </div>
                      
                      <div>
                        <div className="text-xs font-medium text-gray-500 dark:text-gray-400">
                          Take Profit
                        </div>
                        <div className="mt-1 text-sm text-gray-900 dark:text-white">
                          {trade.takeProfit ? formatCurrency(trade.takeProfit) : 'None'}
                        </div>
                      </div>
                      
                      <div>
                        <div className="text-xs font-medium text-gray-500 dark:text-gray-400">
                          Risk
                        </div>
                        <div className="mt-1 text-sm text-gray-900 dark:text-white">
                          {formatCurrency(trade.risk)}
                        </div>
                      </div>
                    </div>
                    
                    <div className="mt-3 flex justify-end space-x-3">
                      <button className="px-3 py-1 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md">
                        Edit Trade
                      </button>
                      <button className="px-3 py-1 text-xs font-medium text-white bg-red-600 hover:bg-red-700 rounded-md">
                        Close Trade
                      </button>
                    </div>
                  </td>
                </tr>
              )}
            </>
          ))}
        </tbody>
      </table>
    </div>
  );
};
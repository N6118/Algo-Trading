import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Filter, Search, Download, RefreshCw } from 'lucide-react';
import { ActiveTradesTable } from '../../components/trade/ActiveTradesTable';
import { useTradingData } from '../../context/TradingDataContext';
import { Trade } from '../../types/trade';
import toast from 'react-hot-toast';

interface TradeFilters {
  strategy: string;
  symbol: string;
  direction: string;
  status: string;
  dateRange: string;
}

interface TradeSummary {
  totalTrades: number;
  totalPnL: number;
  totalRisk: number;
  avgPnL: number;
}

const ActiveTrades = () => {
  const { activeTrades, refreshData } = useTradingData();
  const [filteredTrades, setFilteredTrades] = useState<Trade[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<TradeFilters>({
    strategy: '',
    symbol: '',
    direction: '',
    status: '',
    dateRange: ''
  });
  const [showFilters, setShowFilters] = useState(false);
  const [tradeSummary, setTradeSummary] = useState<TradeSummary>({
    totalTrades: 0,
    totalPnL: 0,
    totalRisk: 0,
    avgPnL: 0
  });
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [realTimePrices, setRealTimePrices] = useState<{ [symbol: string]: number }>({});

  // WebSocket connections for real-time updates
  useEffect(() => {
    // Simulate WebSocket connections for real-time trade updates
    const tradeWs = new WebSocket('ws://localhost:8080/api/ws/trades/active');
    const priceWs = new WebSocket('ws://localhost:8080/api/ws/trades/price');
    const pnlWs = new WebSocket('ws://localhost:8080/api/ws/trades/pnl');

    tradeWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      // Handle real-time trade updates
      console.log('Trade update:', data);
    };

    priceWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setRealTimePrices(prev => ({ ...prev, [data.symbol]: data.price }));
    };

    pnlWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      // Handle real-time P&L updates
      console.log('P&L update:', data);
    };

    // Cleanup on unmount
    return () => {
      tradeWs.close();
      priceWs.close();
      pnlWs.close();
    };
  }, []);

  // Filter and search trades
  useEffect(() => {
    let filtered = activeTrades;

    // Apply search query
    if (searchQuery) {
      filtered = filtered.filter(trade =>
        trade.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
        trade.strategyName.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Apply filters
    if (filters.strategy) {
      filtered = filtered.filter(trade => trade.strategyId === filters.strategy);
    }
    if (filters.symbol) {
      filtered = filtered.filter(trade => trade.symbol === filters.symbol);
    }
    if (filters.direction) {
      filtered = filtered.filter(trade => trade.direction === filters.direction);
    }
    if (filters.status) {
      filtered = filtered.filter(trade => trade.status === filters.status);
    }
    if (filters.dateRange) {
      const now = new Date();
      let cutoffDate = new Date();
      
      switch (filters.dateRange) {
        case 'today':
          cutoffDate.setHours(0, 0, 0, 0);
          break;
        case 'week':
          cutoffDate.setDate(now.getDate() - 7);
          break;
        case 'month':
          cutoffDate.setMonth(now.getMonth() - 1);
          break;
      }
      
      filtered = filtered.filter(trade => new Date(trade.entryTime) >= cutoffDate);
    }

    setFilteredTrades(filtered);

    // Calculate summary
    const summary = filtered.reduce((acc, trade) => ({
      totalTrades: acc.totalTrades + 1,
      totalPnL: acc.totalPnL + trade.pnl,
      totalRisk: acc.totalRisk + trade.risk,
      avgPnL: 0 // Will be calculated after
    }), { totalTrades: 0, totalPnL: 0, totalRisk: 0, avgPnL: 0 });

    summary.avgPnL = summary.totalTrades > 0 ? summary.totalPnL / summary.totalTrades : 0;
    setTradeSummary(summary);
  }, [activeTrades, searchQuery, filters]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await refreshData();
      toast.success('Trades refreshed successfully');
    } catch (error) {
      toast.error('Failed to refresh trades');
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleCloseTrade = async (tradeId: string) => {
    if (!confirm('Are you sure you want to close this trade?')) return;

    try {
      const response = await fetch(`/api/trades/${tradeId}/close`, {
        method: 'POST',
      });

      if (response.ok) {
        toast.success('Trade closed successfully');
        await refreshData();
      } else {
        toast.error('Failed to close trade');
      }
    } catch (error) {
      console.error('Failed to close trade:', error);
      toast.error('Failed to close trade');
    }
  };

  const handleAdjustPosition = async (tradeId: string, newSize: number) => {
    try {
      const response = await fetch(`/api/trades/${tradeId}/size`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ size: newSize }),
      });

      if (response.ok) {
        toast.success('Position size adjusted successfully');
        await refreshData();
      } else {
        toast.error('Failed to adjust position size');
      }
    } catch (error) {
      console.error('Failed to adjust position size:', error);
      toast.error('Failed to adjust position size');
    }
  };

  const handleSetStopLoss = async (tradeId: string, stopLoss: number) => {
    try {
      const response = await fetch(`/api/trades/${tradeId}/stop-loss`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stopLoss }),
      });

      if (response.ok) {
        toast.success('Stop loss updated successfully');
        await refreshData();
      } else {
        toast.error('Failed to update stop loss');
      }
    } catch (error) {
      console.error('Failed to update stop loss:', error);
      toast.error('Failed to update stop loss');
    }
  };

  const handleSetTakeProfit = async (tradeId: string, takeProfit: number) => {
    try {
      const response = await fetch(`/api/trades/${tradeId}/take-profit`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ takeProfit }),
      });

      if (response.ok) {
        toast.success('Take profit updated successfully');
        await refreshData();
      } else {
        toast.error('Failed to update take profit');
      }
    } catch (error) {
      console.error('Failed to update take profit:', error);
      toast.error('Failed to update take profit');
    }
  };

  const exportTrades = () => {
    const csvContent = [
      ['Symbol', 'Direction', 'Quantity', 'Entry Price', 'Current Price', 'P&L', 'Strategy', 'Entry Time'].join(','),
      ...filteredTrades.map(trade => [
        trade.symbol,
        trade.direction,
        trade.quantity,
        trade.entryPrice,
        trade.currentPrice,
        trade.pnl,
        trade.strategyName,
        trade.entryTime
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `active_trades_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const uniqueStrategies = [...new Set(activeTrades.map(trade => trade.strategyName))];
  const uniqueSymbols = [...new Set(activeTrades.map(trade => trade.symbol))];

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Active Trades</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Monitor and manage your active trading positions
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
          >
            <RefreshCw size={16} className={`mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={exportTrades}
            className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            <Download size={16} className="mr-2" />
            Export
          </button>
          <Link
            to="/trades/analysis"
            className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium"
          >
            <Plus size={16} className="mr-2" />
            New Trade Analysis
          </Link>
        </div>
      </div>

      {/* Trade Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Trades</div>
          <div className="text-2xl font-semibold text-gray-900 dark:text-white">{tradeSummary.totalTrades}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Total P&L</div>
          <div className={`text-2xl font-semibold ${
            tradeSummary.totalPnL >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
          }`}>
            {tradeSummary.totalPnL >= 0 ? '+' : ''}${tradeSummary.totalPnL.toFixed(2)}
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Risk</div>
          <div className="text-2xl font-semibold text-gray-900 dark:text-white">${tradeSummary.totalRisk.toFixed(2)}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Avg P&L</div>
          <div className={`text-2xl font-semibold ${
            tradeSummary.avgPnL >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
          }`}>
            {tradeSummary.avgPnL >= 0 ? '+' : ''}${tradeSummary.avgPnL.toFixed(2)}
          </div>
        </div>
      </div>

      {/* Search and Filter Bar */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search size={18} className="text-gray-400" />
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search trades by symbol or strategy..."
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white text-sm"
            />
          </div>
          
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
          >
            <Filter size={16} className="mr-2" />
            Filters
          </button>
        </div>
        
        {showFilters && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-5 gap-4">
            <div>
              <label htmlFor="strategy-filter" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Strategy
              </label>
              <select
                id="strategy-filter"
                value={filters.strategy}
                onChange={(e) => setFilters({ ...filters, strategy: e.target.value })}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white text-sm"
              >
                <option value="">All Strategies</option>
                {uniqueStrategies.map((strategy) => (
                  <option key={strategy} value={strategy}>{strategy}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label htmlFor="symbol-filter" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Symbol
              </label>
              <select
                id="symbol-filter"
                value={filters.symbol}
                onChange={(e) => setFilters({ ...filters, symbol: e.target.value })}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white text-sm"
              >
                <option value="">All Symbols</option>
                {uniqueSymbols.map((symbol) => (
                  <option key={symbol} value={symbol}>{symbol}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label htmlFor="direction-filter" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Direction
              </label>
              <select
                id="direction-filter"
                value={filters.direction}
                onChange={(e) => setFilters({ ...filters, direction: e.target.value })}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white text-sm"
              >
                <option value="">All Directions</option>
                <option value="long">Long</option>
                <option value="short">Short</option>
              </select>
            </div>
            
            <div>
              <label htmlFor="status-filter" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Status
              </label>
              <select
                id="status-filter"
                value={filters.status}
                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white text-sm"
              >
                <option value="">All Status</option>
                <option value="open">Open</option>
                <option value="pending">Pending</option>
              </select>
            </div>
            
            <div>
              <label htmlFor="date-filter" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Date Range
              </label>
              <select
                id="date-filter"
                value={filters.dateRange}
                onChange={(e) => setFilters({ ...filters, dateRange: e.target.value })}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white text-sm"
              >
                <option value="">All Time</option>
                <option value="today">Today</option>
                <option value="week">This Week</option>
                <option value="month">This Month</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Trades Table */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
        <div className="p-6">
          <ActiveTradesTable 
            trades={filteredTrades}
            onCloseTrade={handleCloseTrade}
            onAdjustPosition={handleAdjustPosition}
            onSetStopLoss={handleSetStopLoss}
            onSetTakeProfit={handleSetTakeProfit}
            realTimePrices={realTimePrices}
          />
        </div>
      </div>
    </div>
  );
};

export default ActiveTrades;
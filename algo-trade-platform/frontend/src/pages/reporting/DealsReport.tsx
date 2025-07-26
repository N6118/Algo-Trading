import { useState, useEffect } from 'react';
import { 
  Download, 
  Filter, 
  Search, 
  Calendar,
  BarChart3,
  TrendingUp,
  TrendingDown,
  FileText,
  Eye,
  RefreshCw,
  ChevronDown,
  X
} from 'lucide-react';
import { formatCurrency, formatDateTime, formatPercentage } from '../../utils/formatters';
import { TradeHistory, PerformanceMetrics } from '../../types/report';
import toast from 'react-hot-toast';

interface TradeFilters {
  strategy: string;
  symbol: string;
  status: string;
  dateRange: string;
  customStartDate: string;
  customEndDate: string;
  minPnL: string;
  maxPnL: string;
  ssType: string;
  signalType: string;
}

interface ExportOptions {
  format: 'csv' | 'excel' | 'pdf';
  includeCharts: boolean;
  includeMetrics: boolean;
  dateRange: string;
}

const DealsReport = () => {
  const [deals, setDeals] = useState<TradeHistory[]>([]);
  const [filteredDeals, setFilteredDeals] = useState<TradeHistory[]>([]);
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  const [filters, setFilters] = useState<TradeFilters>({
    strategy: '',
    symbol: '',
    status: '',
    dateRange: '',
    customStartDate: '',
    customEndDate: '',
    minPnL: '',
    maxPnL: '',
    ssType: '',
    signalType: ''
  });

  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    format: 'csv',
    includeCharts: false,
    includeMetrics: true,
    dateRange: 'all'
  });

  const [availableFilters, setAvailableFilters] = useState({
    strategies: [] as string[],
    symbols: [] as string[],
    ssTypes: [] as string[],
    signalTypes: [] as string[]
  });

  useEffect(() => {
    fetchDealsData();
    fetchAvailableFilters();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [deals, searchQuery, filters]);

  const fetchDealsData = async () => {
    try {
      setIsLoading(true);
      
      // Fetch trade history
      const historyResponse = await fetch('/api/trades/history');
      if (historyResponse.ok) {
        const historyData = await historyResponse.json();
        setDeals(historyData);
      }

      // Fetch performance metrics
      const metricsResponse = await fetch('/api/trades/performance/metrics');
      if (metricsResponse.ok) {
        const metricsData = await metricsResponse.json();
        setPerformanceMetrics(metricsData);
      }
    } catch (err) {
      console.error('Failed to fetch deals data:', err);
      // Set mock data
      const mockDeals: TradeHistory[] = [
        {
          id: '1',
          strategyName: 'AAPL Momentum',
          ssType: 'Momentum',
          ssSignalType: 'Price Action',
          symbol: 'AAPL',
          entryQty: 100,
          exitQty: 100,
          entryPrice: 175.50,
          exitPrice: 180.25,
          pnl: 475,
          charges: 10,
          netPnl: 465,
          netPnlPercent: 2.71,
          entryDate: '2024-02-15T10:30:00Z',
          exitDate: '2024-02-16T14:45:00Z',
          status: 'Closed',
          comments: 'Strong momentum trade'
        },
        {
          id: '2',
          strategyName: 'SPY Mean Reversion',
          ssType: 'Mean Reversion',
          ssSignalType: 'RSI Oversold',
          symbol: 'SPY',
          entryQty: 50,
          exitQty: 50,
          entryPrice: 437.82,
          exitPrice: 442.15,
          pnl: 216.50,
          charges: 7.95,
          netPnl: 208.55,
          netPnlPercent: 0.95,
          entryDate: '2024-02-14T09:45:00Z',
          exitDate: '2024-02-15T11:20:00Z',
          status: 'Closed',
          comments: 'Quick reversal play'
        },
        {
          id: '3',
          strategyName: 'TSLA Breakout',
          ssType: 'Breakout',
          ssSignalType: 'Volume Breakout',
          symbol: 'TSLA',
          entryQty: 25,
          exitQty: 25,
          entryPrice: 185.30,
          exitPrice: 178.90,
          pnl: -160,
          charges: 8.50,
          netPnl: -168.50,
          netPnlPercent: -3.64,
          entryDate: '2024-02-13T14:15:00Z',
          exitDate: '2024-02-14T10:30:00Z',
          status: 'Closed',
          comments: 'False breakout, stopped out'
        }
      ];
      setDeals(mockDeals);

      const mockMetrics: PerformanceMetrics = {
        totalTrades: 156,
        winRate: 68.5,
        profitFactor: 2.1,
        averageWin: 285.50,
        averageLoss: -135.75,
        largestWin: 1250.00,
        largestLoss: -485.25,
        sharpeRatio: 1.42,
        maxDrawdown: -8.7,
        recoveryFactor: 1.8
      };
      setPerformanceMetrics(mockMetrics);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const fetchAvailableFilters = async () => {
    try {
      const response = await fetch('/api/trades/filters');
      if (response.ok) {
        const data = await response.json();
        setAvailableFilters(data);
      }
    } catch (err) {
      console.error('Failed to fetch available filters:', err);
      // Set mock filter options
      setAvailableFilters({
        strategies: ['AAPL Momentum', 'SPY Mean Reversion', 'TSLA Breakout', 'QQQ Correlation'],
        symbols: ['AAPL', 'SPY', 'TSLA', 'QQQ', 'MSFT', 'GOOGL'],
        ssTypes: ['Momentum', 'Mean Reversion', 'Breakout', 'Correlation'],
        signalTypes: ['Price Action', 'RSI Oversold', 'Volume Breakout', 'MACD Cross']
      });
    }
  };

  const applyFilters = () => {
    let filtered = deals;

    // Apply search query
    if (searchQuery) {
      filtered = filtered.filter(deal =>
        deal.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
        deal.strategyName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        deal.comments.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Apply filters
    if (filters.strategy) {
      filtered = filtered.filter(deal => deal.strategyName === filters.strategy);
    }
    if (filters.symbol) {
      filtered = filtered.filter(deal => deal.symbol === filters.symbol);
    }
    if (filters.status) {
      filtered = filtered.filter(deal => deal.status === filters.status);
    }
    if (filters.ssType) {
      filtered = filtered.filter(deal => deal.ssType === filters.ssType);
    }
    if (filters.signalType) {
      filtered = filtered.filter(deal => deal.ssSignalType === filters.signalType);
    }

    // Date range filtering
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
        case 'quarter':
          cutoffDate.setMonth(now.getMonth() - 3);
          break;
        case 'year':
          cutoffDate.setFullYear(now.getFullYear() - 1);
          break;
        case 'custom':
          if (filters.customStartDate && filters.customEndDate) {
            const startDate = new Date(filters.customStartDate);
            const endDate = new Date(filters.customEndDate);
            filtered = filtered.filter(deal => {
              const dealDate = new Date(deal.entryDate);
              return dealDate >= startDate && dealDate <= endDate;
            });
          }
          break;
      }
      
      if (filters.dateRange !== 'custom') {
        filtered = filtered.filter(deal => new Date(deal.entryDate) >= cutoffDate);
      }
    }

    // P&L filtering
    if (filters.minPnL) {
      filtered = filtered.filter(deal => deal.netPnl >= parseFloat(filters.minPnL));
    }
    if (filters.maxPnL) {
      filtered = filtered.filter(deal => deal.netPnl <= parseFloat(filters.maxPnL));
    }

    setFilteredDeals(filtered);
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchDealsData();
    toast.success('Deals data refreshed');
  };

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const response = await fetch('/api/trades/history/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          format: exportOptions.format,
          filters,
          includeCharts: exportOptions.includeCharts,
          includeMetrics: exportOptions.includeMetrics,
          deals: filteredDeals
        }),
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `deals_report_${new Date().toISOString().split('T')[0]}.${exportOptions.format}`;
        a.click();
        window.URL.revokeObjectURL(url);
        toast.success('Report exported successfully');
      } else {
        toast.error('Failed to export report');
      }
    } catch (err) {
      console.error('Export failed:', err);
      // Fallback to CSV export
      const csvContent = [
        ['Strategy', 'Symbol', 'SS Type', 'Signal Type', 'Entry Qty', 'Exit Qty', 'Entry Price', 'Exit Price', 'P&L', 'Charges', 'Net P&L', 'Net P&L%', 'Entry Date', 'Exit Date', 'Status', 'Comments'].join(','),
        ...filteredDeals.map(deal => [
          deal.strategyName,
          deal.symbol,
          deal.ssType,
          deal.ssSignalType,
          deal.entryQty,
          deal.exitQty,
          deal.entryPrice,
          deal.exitPrice,
          deal.pnl,
          deal.charges,
          deal.netPnl,
          deal.netPnlPercent,
          deal.entryDate,
          deal.exitDate,
          deal.status,
          deal.comments
        ].join(','))
      ].join('\n');

      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `deals_report_${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success('CSV report exported successfully');
    } finally {
      setIsExporting(false);
      setShowExportModal(false);
    }
  };

  const clearFilters = () => {
    setFilters({
      strategy: '',
      symbol: '',
      status: '',
      dateRange: '',
      customStartDate: '',
      customEndDate: '',
      minPnL: '',
      maxPnL: '',
      ssType: '',
      signalType: ''
    });
    setSearchQuery('');
  };

  const calculateSummaryMetrics = () => {
    const totalPnL = filteredDeals.reduce((sum, deal) => sum + deal.netPnl, 0);
    const totalCharges = filteredDeals.reduce((sum, deal) => sum + deal.charges, 0);
    const winningTrades = filteredDeals.filter(deal => deal.netPnl > 0).length;
    const winRate = filteredDeals.length > 0 ? (winningTrades / filteredDeals.length) * 100 : 0;

    return {
      totalTrades: filteredDeals.length,
      totalPnL,
      totalCharges,
      winRate,
      avgPnL: filteredDeals.length > 0 ? totalPnL / filteredDeals.length : 0
    };
  };

  const summaryMetrics = calculateSummaryMetrics();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Deals Report</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Comprehensive trade history and performance analysis
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
            onClick={() => setShowExportModal(true)}
            className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
          >
            <Download size={16} className="mr-2" />
            Export Report
          </button>
        </div>
      </div>

      {/* Summary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Trades</div>
          <div className="text-2xl font-semibold text-gray-900 dark:text-white">{summaryMetrics.totalTrades}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Total P&L</div>
          <div className={`text-2xl font-semibold ${
            summaryMetrics.totalPnL >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
          }`}>
            {formatCurrency(summaryMetrics.totalPnL)}
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Win Rate</div>
          <div className="text-2xl font-semibold text-gray-900 dark:text-white">{summaryMetrics.winRate.toFixed(1)}%</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Avg P&L</div>
          <div className={`text-2xl font-semibold ${
            summaryMetrics.avgPnL >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
          }`}>
            {formatCurrency(summaryMetrics.avgPnL)}
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Charges</div>
          <div className="text-2xl font-semibold text-gray-900 dark:text-white">{formatCurrency(summaryMetrics.totalCharges)}</div>
        </div>
      </div>

      {/* Performance Metrics */}
      {performanceMetrics && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white flex items-center">
              <BarChart3 className="w-5 h-5 mr-2 text-blue-500" />
              Performance Metrics
            </h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">Profit Factor</p>
                <p className="text-xl font-semibold text-gray-900 dark:text-white">
                  {performanceMetrics.profitFactor.toFixed(2)}
                </p>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">Sharpe Ratio</p>
                <p className="text-xl font-semibold text-gray-900 dark:text-white">
                  {performanceMetrics.sharpeRatio.toFixed(2)}
                </p>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">Max Drawdown</p>
                <p className="text-xl font-semibold text-red-600 dark:text-red-400">
                  {performanceMetrics.maxDrawdown.toFixed(1)}%
                </p>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">Avg Win</p>
                <p className="text-xl font-semibold text-green-600 dark:text-green-400">
                  {formatCurrency(performanceMetrics.averageWin)}
                </p>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">Avg Loss</p>
                <p className="text-xl font-semibold text-red-600 dark:text-red-400">
                  {formatCurrency(performanceMetrics.averageLoss)}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

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
              placeholder="Search by symbol, strategy, or comments..."
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white text-sm"
            />
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
            >
              <Filter size={16} className="mr-2" />
              Filters
              <ChevronDown size={16} className="ml-2" />
            </button>
            
            {(Object.values(filters).some(v => v) || searchQuery) && (
              <button
                onClick={clearFilters}
                className="flex items-center px-3 py-2 text-sm font-medium text-red-600 hover:text-red-700 dark:text-red-400"
              >
                <X size={16} className="mr-1" />
                Clear
              </button>
            )}
          </div>
        </div>
        
        {showFilters && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Strategy
              </label>
              <select
                value={filters.strategy}
                onChange={(e) => setFilters({ ...filters, strategy: e.target.value })}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white text-sm"
              >
                <option value="">All Strategies</option>
                {availableFilters.strategies.map((strategy) => (
                  <option key={strategy} value={strategy}>{strategy}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Symbol
              </label>
              <select
                value={filters.symbol}
                onChange={(e) => setFilters({ ...filters, symbol: e.target.value })}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white text-sm"
              >
                <option value="">All Symbols</option>
                {availableFilters.symbols.map((symbol) => (
                  <option key={symbol} value={symbol}>{symbol}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                SS Type
              </label>
              <select
                value={filters.ssType}
                onChange={(e) => setFilters({ ...filters, ssType: e.target.value })}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white text-sm"
              >
                <option value="">All SS Types</option>
                {availableFilters.ssTypes.map((type) => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Date Range
              </label>
              <select
                value={filters.dateRange}
                onChange={(e) => setFilters({ ...filters, dateRange: e.target.value })}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white text-sm"
              >
                <option value="">All Time</option>
                <option value="today">Today</option>
                <option value="week">This Week</option>
                <option value="month">This Month</option>
                <option value="quarter">This Quarter</option>
                <option value="year">This Year</option>
                <option value="custom">Custom Range</option>
              </select>
            </div>
            
            {filters.dateRange === 'custom' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={filters.customStartDate}
                    onChange={(e) => setFilters({ ...filters, customStartDate: e.target.value })}
                    className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    End Date
                  </label>
                  <input
                    type="date"
                    value={filters.customEndDate}
                    onChange={(e) => setFilters({ ...filters, customEndDate: e.target.value })}
                    className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white text-sm"
                  />
                </div>
              </>
            )}
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Min P&L
              </label>
              <input
                type="number"
                value={filters.minPnL}
                onChange={(e) => setFilters({ ...filters, minPnL: e.target.value })}
                placeholder="Minimum P&L"
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white text-sm"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Max P&L
              </label>
              <input
                type="number"
                value={filters.maxPnL}
                onChange={(e) => setFilters({ ...filters, maxPnL: e.target.value })}
                placeholder="Maximum P&L"
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white text-sm"
              />
            </div>
          </div>
        )}
      </div>

      {/* Deals Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Strategy
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Symbol
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Entry
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Exit
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  P&L
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Status
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {filteredDeals.map((deal) => (
                <tr key={deal.id} className="hover:bg-gray-50 dark:hover:bg-gray-750">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {deal.strategyName}
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {deal.ssType} - {deal.ssSignalType}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900 dark:text-white">{deal.symbol}</div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      Qty: {deal.entryQty} → {deal.exitQty}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900 dark:text-white">
                      {formatCurrency(deal.entryPrice)}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {formatDateTime(deal.entryDate)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900 dark:text-white">
                      {formatCurrency(deal.exitPrice)}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {formatDateTime(deal.exitDate)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className={`text-sm font-medium ${
                      deal.netPnl >= 0 
                        ? 'text-green-600 dark:text-green-400' 
                        : 'text-red-600 dark:text-red-400'
                    }`}>
                      {formatCurrency(deal.netPnl)}
                      <span className="text-xs ml-1">
                        ({deal.netPnlPercent > 0 ? '+' : ''}{deal.netPnlPercent.toFixed(2)}%)
                      </span>
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      Fees: {formatCurrency(deal.charges)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      deal.status === 'Closed'
                        ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
                        : 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200'
                    }`}>
                      {deal.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300">
                      <Eye size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {filteredDeals.length === 0 && (
          <div className="text-center py-12">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No trades found</h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Try adjusting your search criteria or filters.
            </p>
          </div>
        )}
      </div>

      {/* Export Modal */}
      {showExportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Export Report</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Export Format
                </label>
                <select
                  value={exportOptions.format}
                  onChange={(e) => setExportOptions({ ...exportOptions, format: e.target.value as 'csv' | 'excel' | 'pdf' })}
                  className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  <option value="csv">CSV</option>
                  <option value="excel">Excel</option>
                  <option value="pdf">PDF</option>
                </select>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={exportOptions.includeMetrics}
                    onChange={(e) => setExportOptions({ ...exportOptions, includeMetrics: e.target.checked })}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                    Include Performance Metrics
                  </label>
                </div>
                
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={exportOptions.includeCharts}
                    onChange={(e) => setExportOptions({ ...exportOptions, includeCharts: e.target.checked })}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    disabled={exportOptions.format === 'csv'}
                  />
                  <label className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                    Include Charts (PDF/Excel only)
                  </label>
                </div>
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowExportModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Cancel
              </button>
              <button
                onClick={handleExport}
                disabled={isExporting}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center"
              >
                {isExporting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Exporting...
                  </>
                ) : (
                  <>
                    <Download size={16} className="mr-2" />
                    Export
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DealsReport;
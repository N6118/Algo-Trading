import { useState, useEffect } from 'react';
import { 
  Calendar,
  Download,
  Filter,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  DollarSign,
  BarChart3,
  PieChart,
  Activity,
  ChevronDown,
  X
} from 'lucide-react';
import DashboardCard from '../../components/common/DashboardCard';
import { formatCurrency, formatPercentage } from '../../utils/formatters';
import { PnLData } from '../../types/report';
import toast from 'react-hot-toast';

interface PnLSummary {
  totalGrossPnL: number;
  totalNetPnL: number;
  totalFees: number;
  totalCommissions: number;
  totalTrades: number;
  profitableDays: number;
  totalDays: number;
  bestDay: number;
  worstDay: number;
  averageDailyPnL: number;
  winRate: number;
}

interface PnLBreakdown {
  byStrategy: Array<{
    strategyName: string;
    grossPnL: number;
    netPnL: number;
    fees: number;
    trades: number;
    winRate: number;
  }>;
  bySymbol: Array<{
    symbol: string;
    grossPnL: number;
    netPnL: number;
    fees: number;
    trades: number;
    volume: number;
  }>;
  byTimeOfDay: Array<{
    hour: number;
    grossPnL: number;
    netPnL: number;
    trades: number;
  }>;
  byDayOfWeek: Array<{
    day: string;
    grossPnL: number;
    netPnL: number;
    trades: number;
  }>;
}

interface PnLFilters {
  timeGranularity: 'daily' | 'weekly' | 'monthly' | 'yearly';
  dateRange: string;
  customStartDate: string;
  customEndDate: string;
  strategy: string;
  symbol: string;
  minPnL: string;
  maxPnL: string;
}

const PnLReport = () => {
  const [pnlData, setPnlData] = useState<PnLData[]>([]);
  const [pnlSummary, setPnlSummary] = useState<PnLSummary | null>(null);
  const [pnlBreakdown, setPnlBreakdown] = useState<PnLBreakdown | null>(null);
  const [filteredData, setFilteredData] = useState<PnLData[]>([]);
  const [showFilters, setShowFilters] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const [filters, setFilters] = useState<PnLFilters>({
    timeGranularity: 'daily',
    dateRange: '3M',
    customStartDate: '',
    customEndDate: '',
    strategy: '',
    symbol: '',
    minPnL: '',
    maxPnL: ''
  });

  const [availableOptions, setAvailableOptions] = useState({
    strategies: [] as string[],
    symbols: [] as string[]
  });

  useEffect(() => {
    fetchPnLData();
    fetchAvailableOptions();
  }, [filters.timeGranularity, filters.dateRange]);

  useEffect(() => {
    applyFilters();
  }, [pnlData, filters]);

  const fetchPnLData = async () => {
    try {
      setIsLoading(true);

      // Fetch P&L summary
      const summaryResponse = await fetch(`/api/pnl/summary?granularity=${filters.timeGranularity}&range=${filters.dateRange}`);
      if (summaryResponse.ok) {
        const summaryData = await summaryResponse.json();
        setPnlSummary(summaryData);
      }

      // Fetch P&L data based on granularity
      const dataResponse = await fetch(`/api/pnl/${filters.timeGranularity}?range=${filters.dateRange}`);
      if (dataResponse.ok) {
        const data = await dataResponse.json();
        setPnlData(data);
      }

      // Fetch P&L breakdown
      const breakdownResponse = await fetch(`/api/pnl/breakdown?granularity=${filters.timeGranularity}&range=${filters.dateRange}`);
      if (breakdownResponse.ok) {
        const breakdownData = await breakdownResponse.json();
        setPnlBreakdown(breakdownData);
      }
    } catch (err) {
      console.error('Failed to fetch P&L data:', err);
      // Set mock data
      generateMockData();
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const generateMockData = () => {
    // Generate mock P&L data
    const mockPnLData: PnLData[] = Array.from({ length: 90 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (89 - i));
      
      const trades = Math.floor(Math.random() * 10) + 1;
      const grossPnL = (Math.random() - 0.4) * 1000; // Slight positive bias
      const fees = trades * 7.95;
      const commissions = trades * 2.50;
      const netPnL = grossPnL - fees - commissions;
      
      return {
        date: date.toISOString().split('T')[0],
        grossPnL,
        netPnL,
        fees,
        commissions,
        trades
      };
    });
    setPnlData(mockPnLData);

    // Generate mock summary
    const totalGrossPnL = mockPnLData.reduce((sum, day) => sum + day.grossPnL, 0);
    const totalNetPnL = mockPnLData.reduce((sum, day) => sum + day.netPnL, 0);
    const totalFees = mockPnLData.reduce((sum, day) => sum + day.fees, 0);
    const totalCommissions = mockPnLData.reduce((sum, day) => sum + day.commissions, 0);
    const totalTrades = mockPnLData.reduce((sum, day) => sum + day.trades, 0);
    const profitableDays = mockPnLData.filter(day => day.netPnL > 0).length;
    const bestDay = Math.max(...mockPnLData.map(day => day.netPnL));
    const worstDay = Math.min(...mockPnLData.map(day => day.netPnL));

    setPnlSummary({
      totalGrossPnL,
      totalNetPnL,
      totalFees,
      totalCommissions,
      totalTrades,
      profitableDays,
      totalDays: mockPnLData.length,
      bestDay,
      worstDay,
      averageDailyPnL: totalNetPnL / mockPnLData.length,
      winRate: (profitableDays / mockPnLData.length) * 100
    });

    // Generate mock breakdown
    setPnlBreakdown({
      byStrategy: [
        { strategyName: 'AAPL Momentum', grossPnL: 5420.75, netPnL: 5180.25, fees: 240.50, trades: 25, winRate: 72.0 },
        { strategyName: 'SPY-QQQ Correlation', grossPnL: 3250.50, netPnL: 3095.75, fees: 154.75, trades: 18, winRate: 66.7 },
        { strategyName: 'Tech Sector Breakout', grossPnL: 6749.50, netPnL: 6485.25, fees: 264.25, trades: 32, winRate: 65.6 }
      ],
      bySymbol: [
        { symbol: 'AAPL', grossPnL: 4250.75, netPnL: 4085.50, fees: 165.25, trades: 15, volume: 450000 },
        { symbol: 'SPY', grossPnL: 2180.25, netPnL: 2075.50, fees: 104.75, trades: 12, volume: 380000 },
        { symbol: 'QQQ', grossPnL: 3890.50, netPnL: 3745.25, fees: 145.25, trades: 18, volume: 520000 }
      ],
      byTimeOfDay: [
        { hour: 9, grossPnL: 1250.75, netPnL: 1185.50, trades: 45 },
        { hour: 10, grossPnL: 2180.25, netPnL: 2095.75, trades: 68 },
        { hour: 11, grossPnL: 1890.50, netPnL: 1825.25, trades: 52 },
        { hour: 14, grossPnL: 1420.75, netPnL: 1365.50, trades: 38 },
        { hour: 15, grossPnL: 980.25, netPnL: 945.75, trades: 28 }
      ],
      byDayOfWeek: [
        { day: 'Monday', grossPnL: 2450.75, netPnL: 2365.50, trades: 58 },
        { day: 'Tuesday', grossPnL: 3180.25, netPnL: 3085.75, trades: 72 },
        { day: 'Wednesday', grossPnL: 2890.50, netPnL: 2795.25, trades: 65 },
        { day: 'Thursday', grossPnL: 3250.75, netPnL: 3145.50, trades: 78 },
        { day: 'Friday', grossPnL: 1950.25, netPnL: 1875.75, trades: 48 }
      ]
    });
  };

  const fetchAvailableOptions = async () => {
    try {
      const response = await fetch('/api/pnl/filters');
      if (response.ok) {
        const data = await response.json();
        setAvailableOptions(data);
      }
    } catch (err) {
      console.error('Failed to fetch available options:', err);
      setAvailableOptions({
        strategies: ['AAPL Momentum', 'SPY-QQQ Correlation', 'Tech Sector Breakout'],
        symbols: ['AAPL', 'SPY', 'QQQ', 'MSFT', 'GOOGL', 'TSLA']
      });
    }
  };

  const applyFilters = () => {
    let filtered = pnlData;

    // Apply strategy filter
    if (filters.strategy) {
      // This would need to be implemented based on how strategy data is linked to P&L data
      // For now, we'll keep all data
    }

    // Apply symbol filter
    if (filters.symbol) {
      // This would need to be implemented based on how symbol data is linked to P&L data
      // For now, we'll keep all data
    }

    // Apply P&L range filters
    if (filters.minPnL) {
      filtered = filtered.filter(item => item.netPnL >= parseFloat(filters.minPnL));
    }
    if (filters.maxPnL) {
      filtered = filtered.filter(item => item.netPnL <= parseFloat(filters.maxPnL));
    }

    // Apply custom date range
    if (filters.dateRange === 'custom' && filters.customStartDate && filters.customEndDate) {
      const startDate = new Date(filters.customStartDate);
      const endDate = new Date(filters.customEndDate);
      filtered = filtered.filter(item => {
        const itemDate = new Date(item.date);
        return itemDate >= startDate && itemDate <= endDate;
      });
    }

    setFilteredData(filtered);
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchPnLData();
    toast.success('P&L data refreshed');
  };

  const handleExport = async (format: 'csv' | 'excel' | 'pdf') => {
    setIsExporting(true);
    try {
      const response = await fetch(`/api/pnl/export/${format}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filters,
          data: filteredData,
          summary: pnlSummary,
          breakdown: pnlBreakdown
        }),
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `pnl_report_${filters.timeGranularity}_${new Date().toISOString().split('T')[0]}.${format}`;
        a.click();
        window.URL.revokeObjectURL(url);
        toast.success(`P&L report exported as ${format.toUpperCase()}`);
      } else {
        toast.error('Failed to export report');
      }
    } catch (err) {
      console.error('Export failed:', err);
      toast.error('Failed to export report');
    } finally {
      setIsExporting(false);
    }
  };

  const clearFilters = () => {
    setFilters({
      timeGranularity: 'daily',
      dateRange: '3M',
      customStartDate: '',
      customEndDate: '',
      strategy: '',
      symbol: '',
      minPnL: '',
      maxPnL: ''
    });
  };

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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">P&L Reporting</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Detailed profit and loss analysis with breakdowns and trends
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            {(['daily', 'weekly', 'monthly', 'yearly'] as const).map((granularity) => (
              <button 
                key={granularity}
                onClick={() => setFilters({ ...filters, timeGranularity: granularity })} 
                className={`px-3 py-1 text-sm rounded-md transition-colors duration-200 capitalize ${
                  filters.timeGranularity === granularity 
                    ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400' 
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                {granularity}
              </button>
            ))}
          </div>
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
          >
            <RefreshCw size={16} className={`mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <div className="relative">
            <button
              onClick={() => document.getElementById('export-menu')?.classList.toggle('hidden')}
              className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
            >
              <Download size={16} className="mr-2" />
              Export
              <ChevronDown size={16} className="ml-1" />
            </button>
            <div id="export-menu" className="hidden absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-md shadow-lg py-1 z-10 border border-gray-200 dark:border-gray-700">
              <button
                onClick={() => handleExport('csv')}
                className="block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                Export as CSV
              </button>
              <button
                onClick={() => handleExport('excel')}
                className="block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                Export as Excel
              </button>
              <button
                onClick={() => handleExport('pdf')}
                className="block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                Export as PDF
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* P&L Summary */}
      {pnlSummary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <DashboardCard
            title="Total Net P&L"
            value={formatCurrency(pnlSummary.totalNetPnL)}
            change={`Gross: ${formatCurrency(pnlSummary.totalGrossPnL)}`}
            trend={pnlSummary.totalNetPnL > 0 ? 'up' : 'down'}
            icon={<DollarSign className="text-green-500" size={20} />}
          />
          <DashboardCard
            title="Win Rate"
            value={`${pnlSummary.winRate.toFixed(1)}%`}
            change={`${pnlSummary.profitableDays}/${pnlSummary.totalDays} days`}
            trend={pnlSummary.winRate > 60 ? 'up' : 'down'}
            icon={<TrendingUp className="text-blue-500" size={20} />}
          />
          <DashboardCard
            title="Best Day"
            value={formatCurrency(pnlSummary.bestDay)}
            change={`Worst: ${formatCurrency(pnlSummary.worstDay)}`}
            trend="up"
            icon={<BarChart3 className="text-purple-500" size={20} />}
          />
          <DashboardCard
            title="Total Fees"
            value={formatCurrency(pnlSummary.totalFees + pnlSummary.totalCommissions)}
            change={`${pnlSummary.totalTrades} trades`}
            trend="neutral"
            icon={<Activity className="text-orange-500" size={20} />}
          />
        </div>
      )}

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <select
              value={filters.dateRange}
              onChange={(e) => setFilters({ ...filters, dateRange: e.target.value })}
              className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white text-sm"
            >
              <option value="1M">Last Month</option>
              <option value="3M">Last 3 Months</option>
              <option value="6M">Last 6 Months</option>
              <option value="1Y">Last Year</option>
              <option value="ALL">All Time</option>
              <option value="custom">Custom Range</option>
            </select>
          </div>
          
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
          >
            <Filter size={16} className="mr-2" />
            Advanced Filters
            <ChevronDown size={16} className="ml-2" />
          </button>
          
          {(Object.values(filters).some(v => v && v !== 'daily' && v !== '3M')) && (
            <button
              onClick={clearFilters}
              className="flex items-center px-3 py-2 text-sm font-medium text-red-600 hover:text-red-700 dark:text-red-400"
            >
              <X size={16} className="mr-1" />
              Clear
            </button>
          )}
        </div>
        
        {showFilters && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
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
                Strategy
              </label>
              <select
                value={filters.strategy}
                onChange={(e) => setFilters({ ...filters, strategy: e.target.value })}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white text-sm"
              >
                <option value="">All Strategies</option>
                {availableOptions.strategies.map((strategy) => (
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
                {availableOptions.symbols.map((symbol) => (
                  <option key={symbol} value={symbol}>{symbol}</option>
                ))}
              </select>
            </div>
            
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

      {/* P&L Chart */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white">P&L Trend</h2>
        </div>
        <div className="p-4 h-80">
          <div className="w-full h-full bg-gray-50 dark:bg-gray-700 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <BarChart3 className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <p className="text-gray-500 dark:text-gray-400">P&L trend visualization</p>
              <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
                Showing {filters.timeGranularity} P&L over {filters.dateRange}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* P&L Breakdown */}
      {pnlBreakdown && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* By Strategy */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-medium text-gray-900 dark:text-white flex items-center">
                <PieChart className="w-5 h-5 mr-2 text-blue-500" />
                P&L by Strategy
              </h2>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {pnlBreakdown.byStrategy.map((strategy, index) => (
                  <div key={index} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">{strategy.strategyName}</div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {strategy.trades} trades • {strategy.winRate.toFixed(1)}% win rate
                      </div>
                      <div className="text-xs text-gray-400 dark:text-gray-500">
                        Fees: {formatCurrency(strategy.fees)}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`font-medium ${
                        strategy.netPnL >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                      }`}>
                        {formatCurrency(strategy.netPnL)}
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        Gross: {formatCurrency(strategy.grossPnL)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* By Symbol */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-medium text-gray-900 dark:text-white flex items-center">
                <Activity className="w-5 h-5 mr-2 text-green-500" />
                P&L by Symbol
              </h2>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {pnlBreakdown.bySymbol.map((symbol, index) => (
                  <div key={index} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">{symbol.symbol}</div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {symbol.trades} trades • Volume: {(symbol.volume / 1000).toFixed(0)}K
                      </div>
                      <div className="text-xs text-gray-400 dark:text-gray-500">
                        Fees: {formatCurrency(symbol.fees)}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`font-medium ${
                        symbol.netPnL >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                      }`}>
                        {formatCurrency(symbol.netPnL)}
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        Gross: {formatCurrency(symbol.grossPnL)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* By Time of Day */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-medium text-gray-900 dark:text-white flex items-center">
                <Calendar className="w-5 h-5 mr-2 text-purple-500" />
                P&L by Time of Day
              </h2>
            </div>
            <div className="p-6">
              <div className="space-y-3">
                {pnlBreakdown.byTimeOfDay.map((timeSlot, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">
                        {timeSlot.hour}:00 - {timeSlot.hour + 1}:00
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {timeSlot.trades} trades
                      </div>
                    </div>
                    <div className={`font-medium ${
                      timeSlot.netPnL >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                    }`}>
                      {formatCurrency(timeSlot.netPnL)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* By Day of Week */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-medium text-gray-900 dark:text-white flex items-center">
                <Calendar className="w-5 h-5 mr-2 text-orange-500" />
                P&L by Day of Week
              </h2>
            </div>
            <div className="p-6">
              <div className="space-y-3">
                {pnlBreakdown.byDayOfWeek.map((daySlot, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">{daySlot.day}</div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {daySlot.trades} trades
                      </div>
                    </div>
                    <div className={`font-medium ${
                      daySlot.netPnL >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                    }`}>
                      {formatCurrency(daySlot.netPnL)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Detailed P&L Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white">
            Detailed P&L ({filters.timeGranularity})
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Date
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Gross P&L
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Fees
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Net P&L
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Trades
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {filteredData.slice(0, 50).map((item, index) => (
                <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-750">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {new Date(item.date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`text-sm font-medium ${
                      item.grossPnL >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                    }`}>
                      {formatCurrency(item.grossPnL)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {formatCurrency(item.fees + item.commissions)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`text-sm font-medium ${
                      item.netPnL >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                    }`}>
                      {formatCurrency(item.netPnL)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {item.trades}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default PnLReport;
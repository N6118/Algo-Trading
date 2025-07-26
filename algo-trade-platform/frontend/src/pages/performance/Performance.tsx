import { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  BarChart3, 
  Calendar,
  Download,
  RefreshCw,
  Filter,
  Target,
  DollarSign,
  Activity,
  Zap
} from 'lucide-react';
import DashboardCard from '../../components/common/DashboardCard';
import { formatCurrency, formatPercentage } from '../../utils/formatters';
import toast from 'react-hot-toast';

interface PerformanceSummary {
  totalReturn: number;
  totalReturnPercent: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
  profitFactor: number;
  sharpeRatio: number;
  maxDrawdown: number;
  averageReturn: number;
  bestTrade: number;
  worstTrade: number;
  totalTrades: number;
  totalVolume: number;
  averageHoldingPeriod: number;
}

interface StrategyPerformance {
  strategyId: string;
  strategyName: string;
  totalReturn: number;
  returnPercent: number;
  trades: number;
  winRate: number;
  sharpeRatio: number;
  maxDrawdown: number;
  lastTradeDate: string;
  isActive: boolean;
}

interface SymbolPerformance {
  symbol: string;
  totalReturn: number;
  returnPercent: number;
  trades: number;
  winRate: number;
  averageReturn: number;
  bestTrade: number;
  worstTrade: number;
  volume: number;
}

interface TimeSeriesData {
  date: string;
  portfolioValue: number;
  dailyReturn: number;
  cumulativeReturn: number;
  drawdown: number;
  benchmark?: number;
}

interface BenchmarkData {
  name: string;
  symbol: string;
  return: number;
  returnPercent: number;
}

interface ComparisonData {
  period: string;
  portfolioReturn: number;
  benchmarkReturn: number;
  alpha: number;
  beta: number;
  correlation: number;
}

const Performance = () => {
  const [performanceSummary, setPerformanceSummary] = useState<PerformanceSummary | null>(null);
  const [strategyPerformance, setStrategyPerformance] = useState<StrategyPerformance[]>([]);
  const [symbolPerformance, setSymbolPerformance] = useState<SymbolPerformance[]>([]);
  const [timeSeriesData, setTimeSeriesData] = useState<TimeSeriesData[]>([]);
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkData[]>([]);
  const [comparisonData, setComparisonData] = useState<ComparisonData[]>([]);
  
  const [selectedTimeRange, setSelectedTimeRange] = useState<'1M' | '3M' | '6M' | '1Y' | 'ALL'>('3M');
  const [selectedMetric, setSelectedMetric] = useState<'return' | 'drawdown' | 'sharpe' | 'winrate'>('return');
  const [selectedBenchmark, setSelectedBenchmark] = useState('SPY');
  const [showComparison, setShowComparison] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    fetchPerformanceData();
  }, [selectedTimeRange, selectedBenchmark]);

  const fetchPerformanceData = async () => {
    try {
      setIsLoading(true);
      
      // Fetch performance summary
      const summaryResponse = await fetch(`/api/performance/summary?timeRange=${selectedTimeRange}`);
      if (summaryResponse.ok) {
        const summaryData = await summaryResponse.json();
        setPerformanceSummary(summaryData);
      }

      // Fetch strategy performance
      const strategiesResponse = await fetch(`/api/performance/strategies?timeRange=${selectedTimeRange}`);
      if (strategiesResponse.ok) {
        const strategiesData = await strategiesResponse.json();
        setStrategyPerformance(strategiesData);
      }

      // Fetch symbol performance
      const symbolsResponse = await fetch(`/api/performance/symbols?timeRange=${selectedTimeRange}`);
      if (symbolsResponse.ok) {
        const symbolsData = await symbolsResponse.json();
        setSymbolPerformance(symbolsData);
      }

      // Fetch time series data
      const timeSeriesResponse = await fetch(`/api/performance/time-series?timeRange=${selectedTimeRange}`);
      if (timeSeriesResponse.ok) {
        const timeSeriesData = await timeSeriesResponse.json();
        setTimeSeriesData(timeSeriesData);
      }

      // Fetch benchmark data
      const benchmarkResponse = await fetch('/api/performance/benchmarks');
      if (benchmarkResponse.ok) {
        const benchmarkData = await benchmarkResponse.json();
        setBenchmarkData(benchmarkData);
      }

      // Fetch comparison data
      const comparisonResponse = await fetch(`/api/performance/comparison?benchmark=${selectedBenchmark}&timeRange=${selectedTimeRange}`);
      if (comparisonResponse.ok) {
        const comparisonData = await comparisonResponse.json();
        setComparisonData(comparisonData);
      }
    } catch (err) {
      console.error('Failed to fetch performance data:', err);
      // Set mock data
      setPerformanceSummary({
        totalReturn: 15420.75,
        totalReturnPercent: 15.42,
        winningTrades: 68,
        losingTrades: 32,
        winRate: 68.0,
        profitFactor: 2.1,
        sharpeRatio: 1.42,
        maxDrawdown: -8.7,
        averageReturn: 154.21,
        bestTrade: 1250.00,
        worstTrade: -485.25,
        totalTrades: 100,
        totalVolume: 2500000,
        averageHoldingPeriod: 2.5
      });

      setStrategyPerformance([
        {
          strategyId: '1',
          strategyName: 'AAPL Momentum',
          totalReturn: 5420.75,
          returnPercent: 12.45,
          trades: 25,
          winRate: 72.0,
          sharpeRatio: 1.8,
          maxDrawdown: -5.2,
          lastTradeDate: '2024-03-15T14:30:00Z',
          isActive: true
        },
        {
          strategyId: '2',
          strategyName: 'SPY-QQQ Correlation',
          totalReturn: 3250.50,
          returnPercent: 8.32,
          trades: 18,
          winRate: 66.7,
          sharpeRatio: 1.2,
          maxDrawdown: -3.8,
          lastTradeDate: '2024-03-14T11:45:00Z',
          isActive: true
        },
        {
          strategyId: '3',
          strategyName: 'Tech Sector Breakout',
          totalReturn: 6749.50,
          returnPercent: 15.78,
          trades: 32,
          winRate: 65.6,
          sharpeRatio: 1.6,
          maxDrawdown: -7.1,
          lastTradeDate: '2024-03-15T16:20:00Z',
          isActive: true
        }
      ]);

      setSymbolPerformance([
        {
          symbol: 'AAPL',
          totalReturn: 4250.75,
          returnPercent: 8.5,
          trades: 15,
          winRate: 73.3,
          averageReturn: 283.38,
          bestTrade: 850.00,
          worstTrade: -125.50,
          volume: 450000
        },
        {
          symbol: 'SPY',
          totalReturn: 2180.25,
          returnPercent: 5.2,
          trades: 12,
          winRate: 66.7,
          averageReturn: 181.69,
          bestTrade: 420.00,
          worstTrade: -95.25,
          volume: 380000
        },
        {
          symbol: 'QQQ',
          totalReturn: 3890.50,
          returnPercent: 12.1,
          trades: 18,
          winRate: 72.2,
          averageReturn: 216.14,
          bestTrade: 650.00,
          worstTrade: -180.75,
          volume: 520000
        }
      ]);

      // Generate mock time series data
      const mockTimeSeriesData = Array.from({ length: 90 }, (_, i) => {
        const date = new Date();
        date.setDate(date.getDate() - (89 - i));
        
        const baseValue = 100000;
        const trend = i * 50;
        const volatility = Math.sin(i * 0.1) * 1000;
        const randomNoise = (Math.random() - 0.5) * 500;
        const portfolioValue = Math.max(baseValue + trend + volatility + randomNoise, 95000);
        
        const dailyReturn = i > 0 ? (portfolioValue - (baseValue + (i-1) * 50)) / (baseValue + (i-1) * 50) * 100 : 0;
        const cumulativeReturn = (portfolioValue - baseValue) / baseValue * 100;
        const drawdown = Math.min(0, cumulativeReturn - Math.max(...Array.from({ length: i + 1 }, (_, j) => (baseValue + j * 50 - baseValue) / baseValue * 100)));
        
        return {
          date: date.toISOString().split('T')[0],
          portfolioValue,
          dailyReturn,
          cumulativeReturn,
          drawdown,
          benchmark: baseValue + i * 30 + Math.sin(i * 0.05) * 500
        };
      });
      setTimeSeriesData(mockTimeSeriesData);

      setBenchmarkData([
        { name: 'S&P 500', symbol: 'SPY', return: 8250.00, returnPercent: 8.25 },
        { name: 'NASDAQ 100', symbol: 'QQQ', return: 12150.00, returnPercent: 12.15 },
        { name: 'Russell 2000', symbol: 'IWM', return: 6420.00, returnPercent: 6.42 }
      ]);

      setComparisonData([
        { period: '1M', portfolioReturn: 2.5, benchmarkReturn: 1.8, alpha: 0.7, beta: 1.2, correlation: 0.85 },
        { period: '3M', portfolioReturn: 8.2, benchmarkReturn: 6.1, alpha: 2.1, beta: 1.1, correlation: 0.82 },
        { period: '6M', portfolioReturn: 12.8, benchmarkReturn: 9.5, alpha: 3.3, beta: 1.15, correlation: 0.79 },
        { period: '1Y', portfolioReturn: 18.5, benchmarkReturn: 14.2, alpha: 4.3, beta: 1.08, correlation: 0.81 }
      ]);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchPerformanceData();
    toast.success('Performance data refreshed');
  };

  const handleExportReport = async () => {
    try {
      const response = await fetch('/api/performance/custom-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          timeRange: selectedTimeRange,
          metric: selectedMetric,
          benchmark: selectedBenchmark,
          includeStrategies: true,
          includeSymbols: true,
          includeComparison: showComparison
        }),
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `performance_report_${selectedTimeRange}_${new Date().toISOString().split('T')[0]}.pdf`;
        a.click();
        window.URL.revokeObjectURL(url);
        toast.success('Performance report exported');
      } else {
        toast.error('Failed to export report');
      }
    } catch (err) {
      console.error('Export failed:', err);
      toast.error('Failed to export report');
    }
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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Performance Analytics</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Comprehensive trading performance analysis and benchmarking
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            {(['1M', '3M', '6M', '1Y', 'ALL'] as const).map((range) => (
              <button 
                key={range}
                onClick={() => setSelectedTimeRange(range)} 
                className={`px-3 py-1 text-sm rounded-md transition-colors duration-200 ${
                  selectedTimeRange === range 
                    ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400' 
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                {range}
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
          <button
            onClick={handleExportReport}
            className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
          >
            <Download size={16} className="mr-2" />
            Export Report
          </button>
        </div>
      </div>

      {/* Performance Summary */}
      {performanceSummary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <DashboardCard
            title="Total Return"
            value={formatCurrency(performanceSummary.totalReturn)}
            change={`${performanceSummary.totalReturnPercent > 0 ? '+' : ''}${performanceSummary.totalReturnPercent.toFixed(2)}%`}
            trend={performanceSummary.totalReturn > 0 ? 'up' : 'down'}
            icon={<TrendingUp className="text-green-500" size={20} />}
          />
          <DashboardCard
            title="Win Rate"
            value={`${performanceSummary.winRate.toFixed(1)}%`}
            change={`${performanceSummary.winningTrades}W / ${performanceSummary.losingTrades}L`}
            trend={performanceSummary.winRate > 60 ? 'up' : 'down'}
            icon={<Target className="text-blue-500" size={20} />}
          />
          <DashboardCard
            title="Sharpe Ratio"
            value={performanceSummary.sharpeRatio.toFixed(2)}
            change={`Profit Factor: ${performanceSummary.profitFactor.toFixed(2)}`}
            trend={performanceSummary.sharpeRatio > 1 ? 'up' : 'down'}
            icon={<BarChart3 className="text-purple-500" size={20} />}
          />
          <DashboardCard
            title="Max Drawdown"
            value={`${performanceSummary.maxDrawdown.toFixed(1)}%`}
            change={`Best: ${formatCurrency(performanceSummary.bestTrade)}`}
            trend={performanceSummary.maxDrawdown > -10 ? 'up' : 'down'}
            icon={<TrendingDown className="text-red-500" size={20} />}
          />
        </div>
      )}

      {/* Performance Chart */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white">Portfolio Performance</h2>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <label className="text-sm text-gray-500 dark:text-gray-400">Metric:</label>
              <select
                value={selectedMetric}
                onChange={(e) => setSelectedMetric(e.target.value as any)}
                className="text-sm border border-gray-300 dark:border-gray-600 rounded-md px-2 py-1 dark:bg-gray-700 dark:text-white"
              >
                <option value="return">Cumulative Return</option>
                <option value="drawdown">Drawdown</option>
                <option value="sharpe">Rolling Sharpe</option>
                <option value="winrate">Rolling Win Rate</option>
              </select>
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={showComparison}
                onChange={(e) => setShowComparison(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                Show Benchmark
              </label>
            </div>
          </div>
        </div>
        <div className="p-4 h-80">
          <div className="w-full h-full bg-gray-50 dark:bg-gray-700 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <BarChart3 className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <p className="text-gray-500 dark:text-gray-400">Performance chart visualization</p>
              <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
                Showing {selectedMetric} over {selectedTimeRange}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Strategy and Symbol Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Strategy Performance */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white flex items-center">
              <Zap className="w-5 h-5 mr-2 text-yellow-500" />
              Strategy Performance
            </h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {strategyPerformance.map((strategy) => (
                <div key={strategy.strategyId} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${strategy.isActive ? 'bg-green-500' : 'bg-gray-400'}`} />
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">{strategy.strategyName}</div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {strategy.trades} trades • {strategy.winRate.toFixed(1)}% win rate
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`font-medium ${
                      strategy.totalReturn >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                    }`}>
                      {formatCurrency(strategy.totalReturn)}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {strategy.returnPercent > 0 ? '+' : ''}{strategy.returnPercent.toFixed(2)}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Symbol Performance */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white flex items-center">
              <Activity className="w-5 h-5 mr-2 text-blue-500" />
              Symbol Performance
            </h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {symbolPerformance.map((symbol) => (
                <div key={symbol.symbol} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div>
                    <div className="font-medium text-gray-900 dark:text-white">{symbol.symbol}</div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {symbol.trades} trades • {symbol.winRate.toFixed(1)}% win rate
                    </div>
                    <div className="text-xs text-gray-400 dark:text-gray-500">
                      Best: {formatCurrency(symbol.bestTrade)} • Worst: {formatCurrency(symbol.worstTrade)}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`font-medium ${
                      symbol.totalReturn >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                    }`}>
                      {formatCurrency(symbol.totalReturn)}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {symbol.returnPercent > 0 ? '+' : ''}{symbol.returnPercent.toFixed(2)}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Benchmark Comparison */}
      {showComparison && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white">Benchmark Comparison</h2>
            <select
              value={selectedBenchmark}
              onChange={(e) => setSelectedBenchmark(e.target.value)}
              className="text-sm border border-gray-300 dark:border-gray-600 rounded-md px-3 py-1 dark:bg-gray-700 dark:text-white"
            >
              {benchmarkData.map((benchmark) => (
                <option key={benchmark.symbol} value={benchmark.symbol}>
                  {benchmark.name} ({benchmark.symbol})
                </option>
              ))}
            </select>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              {comparisonData.map((comparison) => (
                <div key={comparison.period} className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="text-sm font-medium text-gray-500 dark:text-gray-400">{comparison.period}</div>
                  <div className="mt-2 space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Portfolio:</span>
                      <span className={`font-medium ${
                        comparison.portfolioReturn >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {comparison.portfolioReturn > 0 ? '+' : ''}{comparison.portfolioReturn.toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Benchmark:</span>
                      <span className={`font-medium ${
                        comparison.benchmarkReturn >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {comparison.benchmarkReturn > 0 ? '+' : ''}{comparison.benchmarkReturn.toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Alpha:</span>
                      <span className="font-medium text-blue-600">{comparison.alpha.toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Beta:</span>
                      <span className="font-medium text-gray-900 dark:text-white">{comparison.beta.toFixed(2)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {benchmarkData.map((benchmark) => (
                <div key={benchmark.symbol} className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">{benchmark.name}</div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">{benchmark.symbol}</div>
                    </div>
                    <div className="text-right">
                      <div className={`font-medium ${
                        benchmark.return >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                      }`}>
                        {formatCurrency(benchmark.return)}
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {benchmark.returnPercent > 0 ? '+' : ''}{benchmark.returnPercent.toFixed(2)}%
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Detailed Metrics */}
      {performanceSummary && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white">Detailed Metrics</h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">Total Trades</p>
                <p className="text-xl font-semibold text-gray-900 dark:text-white">
                  {performanceSummary.totalTrades}
                </p>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">Average Return</p>
                <p className="text-xl font-semibold text-gray-900 dark:text-white">
                  {formatCurrency(performanceSummary.averageReturn)}
                </p>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">Total Volume</p>
                <p className="text-xl font-semibold text-gray-900 dark:text-white">
                  {(performanceSummary.totalVolume / 1000000).toFixed(1)}M
                </p>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">Avg Holding Period</p>
                <p className="text-xl font-semibold text-gray-900 dark:text-white">
                  {performanceSummary.averageHoldingPeriod.toFixed(1)} days
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Performance;
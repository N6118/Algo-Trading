import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  Activity, 
  AlertTriangle, 
  BarChart2, 
  Clock, 
  Edit, 
  Pause, 
  Play, 
  Settings, 
  TrendingDown, 
  TrendingUp,
  Zap,
  Target,
  DollarSign
} from 'lucide-react';
import DashboardCard from '../../components/common/DashboardCard';
import { PerformanceChart } from '../../components/charts/PerformanceChart';
import { ActiveTradesTable } from '../../components/trade/ActiveTradesTable';
import { useTradingData } from '../../context/TradingDataContext';
import { formatCurrency, formatDateTime } from '../../utils/formatters';

interface StrategyDetails {
  id: string;
  name: string;
  type: string;
  symbols: string[];
  isActive: boolean;
  performance: number;
  signalCount: number;
  createdAt: string;
  lastUpdated: string;
  description?: string;
  parameters?: any;
  riskManagement?: any;
}

interface StrategyMetrics {
  totalTrades: number;
  winRate: number;
  profitFactor: number;
  sharpeRatio: number;
  maxDrawdown: number;
  averageWin: number;
  averageLoss: number;
  totalPnL: number;
  dailyPnL: number;
  weeklyPnL: number;
  monthlyPnL: number;
}

interface Signal {
  id: string;
  timestamp: string;
  symbol: string;
  type: 'BUY' | 'SELL';
  price: number;
  confidence: number;
  status: 'pending' | 'executed' | 'cancelled';
}

const StrategyDashboard = () => {
  const { id } = useParams();
  const { strategies, activeTrades } = useTradingData();
  
  const [strategy, setStrategy] = useState<StrategyDetails | null>(null);
  const [metrics, setMetrics] = useState<StrategyMetrics | null>(null);
  const [strategyTrades, setStrategyTrades] = useState([]);
  const [recentSignals, setRecentSignals] = useState<Signal[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showParametersModal, setShowParametersModal] = useState(false);

  useEffect(() => {
    if (id) {
      fetchStrategyData();
    }
  }, [id]);

  const fetchStrategyData = async () => {
    try {
      setIsLoading(true);
      
      // Get strategy details
      const strategyResponse = await fetch(`/api/strategies/${id}`);
      if (strategyResponse.ok) {
        const strategyData = await strategyResponse.json();
        setStrategy(strategyData);
      }

      // Get strategy metrics
      const metricsResponse = await fetch(`/api/strategies/${id}/metrics`);
      if (metricsResponse.ok) {
        const metricsData = await metricsResponse.json();
        setMetrics(metricsData);
      }

      // Get active trades for this strategy
      const tradesResponse = await fetch(`/api/strategies/${id}/trades/active`);
      if (tradesResponse.ok) {
        const tradesData = await tradesResponse.json();
        setStrategyTrades(tradesData);
      }

      // Get recent signals
      const signalsResponse = await fetch(`/api/strategies/${id}/signals`);
      if (signalsResponse.ok) {
        const signalsData = await signalsResponse.json();
        setRecentSignals(signalsData);
      }
    } catch (err) {
      console.error('Failed to fetch strategy data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStrategyToggle = async () => {
    if (!strategy) return;

    try {
      const endpoint = strategy.isActive ? 'stop' : 'start';
      const response = await fetch(`/api/strategies/${id}/${endpoint}`, {
        method: 'POST',
      });

      if (response.ok) {
        setStrategy({ ...strategy, isActive: !strategy.isActive });
      }
    } catch (err) {
      console.error('Failed to toggle strategy:', err);
    }
  };

  // Fallback to mock data if API fails
  const mockStrategy = strategies.find(s => s.id === id);
  const mockStrategyTrades = activeTrades.filter(trade => trade.strategyId === id);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const displayStrategy = strategy || mockStrategy;
  const displayTrades = strategyTrades.length > 0 ? strategyTrades : mockStrategyTrades;

  if (!displayStrategy) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <h2 className="text-xl font-medium text-gray-900 dark:text-white">Strategy not found</h2>
          <p className="mt-2 text-gray-500 dark:text-gray-400">
            The strategy you're looking for doesn't exist.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {displayStrategy.name}
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {displayStrategy.type.charAt(0).toUpperCase() + displayStrategy.type.slice(1)} Strategy • 
            Symbols: {displayStrategy.symbols.join(', ')}
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowParametersModal(true)}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center"
          >
            <Settings size={16} className="mr-2" />
            Parameters
          </button>
          
          <Link
            to={`/strategy/edit/${id}`}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center"
          >
            <Edit size={16} className="mr-2" />
            Edit
          </Link>
          
          <button
            onClick={handleStrategyToggle}
            className={`px-4 py-2 text-sm font-medium text-white rounded-md flex items-center ${
              displayStrategy.isActive 
                ? 'bg-red-600 hover:bg-red-700' 
                : 'bg-green-600 hover:bg-green-700'
            }`}
          >
            {displayStrategy.isActive ? (
              <>
                <Pause size={16} className="mr-2" />
                Stop Strategy
              </>
            ) : (
              <>
                <Play size={16} className="mr-2" />
                Start Strategy
              </>
            )}
          </button>
        </div>
      </div>

      {/* Status Banner */}
      <div className={`p-4 rounded-lg border-l-4 ${
        displayStrategy.isActive 
          ? 'bg-green-50 dark:bg-green-900/20 border-green-400' 
          : 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-400'
      }`}>
        <div className="flex items-center">
          <div className={`flex-shrink-0 ${
            displayStrategy.isActive ? 'text-green-400' : 'text-yellow-400'
          }`}>
            {displayStrategy.isActive ? <Activity size={20} /> : <Pause size={20} />}
          </div>
          <div className="ml-3">
            <p className={`text-sm font-medium ${
              displayStrategy.isActive 
                ? 'text-green-800 dark:text-green-200' 
                : 'text-yellow-800 dark:text-yellow-200'
            }`}>
              Strategy is {displayStrategy.isActive ? 'Active' : 'Inactive'}
            </p>
            <p className={`text-sm ${
              displayStrategy.isActive 
                ? 'text-green-700 dark:text-green-300' 
                : 'text-yellow-700 dark:text-yellow-300'
            }`}>
              Last updated: {formatDateTime(displayStrategy.lastUpdated)}
            </p>
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <DashboardCard
          title="Total Returns"
          value={`${displayStrategy.performance > 0 ? '+' : ''}${displayStrategy.performance.toFixed(2)}%`}
          change={metrics?.dailyPnL ? `${metrics.dailyPnL > 0 ? '+' : ''}${metrics.dailyPnL.toFixed(2)}%` : '+2.1%'}
          trend={displayStrategy.performance > 0 ? 'up' : 'down'}
          icon={<TrendingUp className="text-blue-500" size={20} />}
        />
        
        <DashboardCard
          title="Win Rate"
          value={metrics?.winRate ? `${metrics.winRate.toFixed(1)}%` : '68%'}
          change={'+5%'}
          trend="up"
          icon={<Target className="text-green-500" size={20} />}
        />
        
        <DashboardCard
          title="Active Positions"
          value={displayTrades.length.toString()}
          icon={<BarChart2 className="text-purple-500" size={20} />}
        />
        
        <DashboardCard
          title="Signals Today"
          value={displayStrategy.signalCount.toString()}
          icon={<Zap className="text-yellow-500" size={20} />}
        />
      </div>

      {/* Performance Chart */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="p-6">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Performance History</h2>
          <div className="h-96">
            <PerformanceChart timeRange="1m" />
          </div>
        </div>
      </div>

      {/* Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Trades */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Active Trades</h2>
            {displayTrades.length > 0 ? (
              <ActiveTradesTable trades={displayTrades} limit={5} />
            ) : (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                No active trades for this strategy
              </div>
            )}
          </div>
        </div>

        {/* Recent Signals */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Recent Signals</h2>
            <div className="space-y-3">
              {recentSignals.length > 0 ? (
                recentSignals.slice(0, 5).map((signal) => (
                  <div key={signal.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div className="flex items-center">
                      <div className={`w-2 h-2 rounded-full mr-3 ${
                        signal.type === 'BUY' ? 'bg-green-500' : 'bg-red-500'
                      }`} />
                      <div>
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {signal.type} {signal.symbol}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          {formatDateTime(signal.timestamp)}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {formatCurrency(signal.price)}
                      </div>
                      <div className={`text-xs px-2 py-1 rounded-full ${
                        signal.status === 'executed' 
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
                          : signal.status === 'pending'
                          ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200'
                          : 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200'
                      }`}>
                        {signal.status}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  No recent signals
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Strategy Statistics */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="p-6">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Strategy Statistics</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-sm text-gray-500 dark:text-gray-400">Sharpe Ratio</p>
              <p className="text-xl font-semibold text-gray-900 dark:text-white">
                {metrics?.sharpeRatio?.toFixed(2) || '1.8'}
              </p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-sm text-gray-500 dark:text-gray-400">Max Drawdown</p>
              <p className="text-xl font-semibold text-gray-900 dark:text-white">
                {metrics?.maxDrawdown ? `${metrics.maxDrawdown.toFixed(1)}%` : '-12.3%'}
              </p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-sm text-gray-500 dark:text-gray-400">Profit Factor</p>
              <p className="text-xl font-semibold text-gray-900 dark:text-white">
                {metrics?.profitFactor?.toFixed(2) || '2.1'}
              </p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-sm text-gray-500 dark:text-gray-400">Total Trades</p>
              <p className="text-xl font-semibold text-gray-900 dark:text-white">
                {metrics?.totalTrades || '156'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Parameters Modal */}
      {showParametersModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">Strategy Parameters</h3>
              <button
                onClick={() => setShowParametersModal(false)}
                className="text-gray-400 hover:text-gray-500 dark:text-gray-500 dark:hover:text-gray-400"
              >
                ×
              </button>
            </div>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Timeframe
                  </label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white">
                    {displayStrategy.parameters?.timeframe || '1d'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Lookback Period
                  </label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white">
                    {displayStrategy.parameters?.lookbackPeriod || '20'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Signal Threshold
                  </label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white">
                    {displayStrategy.parameters?.signalThreshold || '2.0'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Max Position Size
                  </label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white">
                    {formatCurrency(displayStrategy.riskManagement?.maxPositionSize || 100000)}
                  </p>
                </div>
              </div>
              
              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">Risk Management</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      Stop Loss
                    </label>
                    <p className="mt-1 text-sm text-gray-900 dark:text-white">
                      {displayStrategy.riskManagement?.stopLossPercent || '2'}%
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      Take Profit
                    </label>
                    <p className="mt-1 text-sm text-gray-900 dark:text-white">
                      {displayStrategy.riskManagement?.takeProfitPercent || '4'}%
                    </p>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="flex justify-end mt-6">
              <button
                onClick={() => setShowParametersModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StrategyDashboard;
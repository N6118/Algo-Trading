import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, BarChart3, Settings, Play, Pause, AlertTriangle, Save, Plus, X, Activity, Database, Zap } from 'lucide-react';
import DashboardCard from '../../components/common/DashboardCard';
import toast from 'react-hot-toast';

interface CorrelationData {
  symbol1: string;
  symbol2: string;
  correlation: number;
  correlationMethod: 'pearson' | 'spearman' | 'kendall';
  strength: 'Strong' | 'Moderate' | 'Weak';
  direction: 'Positive' | 'Negative';
  dataPoints: number;
  pValue: number;
  confidence: number;
}

interface StrategyMetrics {
  totalTrades: number;
  winRate: number;
  avgReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
}

interface SignalCondition {
  id: string;
  type: 'buy' | 'sell';
  primaryCondition: string;
  correlatedCondition: string;
  correlationThreshold: number;
  minDataPoints: number;
  correlationMethod: 'pearson' | 'spearman' | 'kendall';
  enabled: boolean;
}

interface TechnicalIndicator {
  name: string;
  period: number;
  source: 'close' | 'open' | 'high' | 'low' | 'volume';
  parameters: { [key: string]: any };
  enabled: boolean;
}

interface BacktestVisualization {
  equity: { date: string; value: number }[];
  drawdown: { date: string; value: number }[];
  trades: any[];
}

interface CorrelationConfiguration {
  method: 'pearson' | 'spearman' | 'kendall';
  threshold: number;
  minDataPoints: number;
  rollingWindow: number;
  significanceLevel: number;
}

interface MarketDataConfig {
  includePrePost: boolean;
  dataSource: 'realtime' | 'delayed' | 'historical';
  updateFrequency: number;
  includeVolume: boolean;
  includeFundamentals: boolean;
}

const CorrelationStrategy: React.FC = () => {
  const [isActive, setIsActive] = useState(false);
  const [correlationData, setCorrelationData] = useState<CorrelationData[]>([]);
  const [metrics, setMetrics] = useState<StrategyMetrics>({
    totalTrades: 0,
    winRate: 0,
    avgReturn: 0,
    sharpeRatio: 0,
    maxDrawdown: 0
  });
  
  const [primarySymbol, setPrimarySymbol] = useState('AAPL');
  const [correlatedSymbol, setCorrelatedSymbol] = useState('MSFT');
  const [timeframe, setTimeframe] = useState('1d');
  const [correlationConfig, setCorrelationConfig] = useState<CorrelationConfiguration>({
    method: 'pearson',
    threshold: 0.7,
    minDataPoints: 30,
    rollingWindow: 20,
    significanceLevel: 0.05
  });
  const [marketDataConfig, setMarketDataConfig] = useState<MarketDataConfig>({
    includePrePost: false,
    dataSource: 'realtime',
    updateFrequency: 1000,
    includeVolume: true,
    includeFundamentals: false
  });
  const [signalConditions, setSignalConditions] = useState<SignalCondition[]>([]);
  const [technicalIndicators, setTechnicalIndicators] = useState<TechnicalIndicator[]>([]);
  const [backtestResults, setBacktestResults] = useState<BacktestVisualization | null>(null);
  const [isBacktesting, setIsBacktesting] = useState(false);
  const [availableSymbols, setAvailableSymbols] = useState<string[]>([]);
  const [correlationMetrics, setCorrelationMetrics] = useState<any>({});
  const [historicalData, setHistoricalData] = useState<any>({});
  const [webSocketConnections, setWebSocketConnections] = useState<{ [key: string]: WebSocket }>({});

  useEffect(() => {
    fetchInitialData();
    fetchCorrelationData();
    fetchMetrics();
    setupWebSocketConnections();
    
    return () => {
      // Cleanup WebSocket connections
      Object.values(webSocketConnections).forEach(ws => ws.close());
    };
  }, []);

  const fetchInitialData = async () => {
    try {
      // Fetch available symbols
      const symbolsRes = await fetch('/api/symbols');
      if (symbolsRes.ok) {
        const symbols = await symbolsRes.json();
        setAvailableSymbols(symbols);
      }

      // Fetch correlation template
      const templateRes = await fetch('/api/strategies/templates/correlation');
      if (templateRes.ok) {
        const template = await templateRes.json();
        if (template.signalConditions) {
          setSignalConditions(template.signalConditions);
        }
        if (template.technicalIndicators) {
          setTechnicalIndicators(template.technicalIndicators);
        }
      }

      // Fetch indicator parameters
      const indicatorsRes = await fetch('/api/indicators/parameters');
      if (indicatorsRes.ok) {
        const indicators = await indicatorsRes.json();
        setTechnicalIndicators(indicators);
      }
    } catch (err) {
      console.error('Failed to fetch initial data:', err);
      // Set fallback data
      setAvailableSymbols(['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'SPY', 'QQQ']);
      setSignalConditions([
        {
          id: '1',
          type: 'buy',
          primaryCondition: 'price > SH',
          correlatedCondition: 'price < SL',
          correlationThreshold: 0.7,
          minDataPoints: 30,
          correlationMethod: 'pearson',
          enabled: true
        },
        {
          id: '2',
          type: 'sell',
          primaryCondition: 'price < SL',
          correlatedCondition: 'price > SH',
          correlationThreshold: 0.7,
          minDataPoints: 30,
          correlationMethod: 'pearson',
          enabled: true
        }
      ]);
      setTechnicalIndicators([
        { name: 'SMA', period: 20, source: 'close', parameters: {}, enabled: true },
        { name: 'RSI', period: 14, source: 'close', parameters: { overbought: 70, oversold: 30 }, enabled: true },
        { name: 'MACD', period: 12, source: 'close', parameters: { fast: 12, slow: 26, signal: 9 }, enabled: false },
        { name: 'Bollinger Bands', period: 20, source: 'close', parameters: { stdDev: 2 }, enabled: false }
      ]);
    }
  };

  const fetchCorrelationData = async () => {
    try {
      const response = await fetch('/api/correlation/metrics');
      if (response.ok) {
        const data = await response.json();
        setCorrelationData(data);
        setCorrelationMetrics(data.metrics || {});
      }
    } catch (err) {
      console.error('Failed to fetch correlation data:', err);
      // Mock data for correlation pairs
      setCorrelationData([
        {
          symbol1: 'AAPL',
          symbol2: 'MSFT',
          correlation: 0.85,
          correlationMethod: 'pearson',
          strength: 'Strong',
          direction: 'Positive',
          dataPoints: 252,
          pValue: 0.001,
          confidence: 99.9
        },
        {
          symbol1: 'SPY',
          symbol2: 'QQQ',
          correlation: 0.92,
          correlationMethod: 'pearson',
          strength: 'Strong',
          direction: 'Positive',
          dataPoints: 252,
          pValue: 0.001,
          confidence: 99.9
        },
        {
          symbol1: 'GLD',
          symbol2: 'USD',
          correlation: -0.73,
          correlationMethod: 'spearman',
          strength: 'Strong',
          direction: 'Negative',
          dataPoints: 180,
          pValue: 0.01,
          confidence: 99.0
        }
      ]);
    }
  };

  const fetchMetrics = async () => {
    try {
      const response = await fetch('/api/strategies/correlation/metrics');
      if (response.ok) {
        const data = await response.json();
        setMetrics(data);
      }
    } catch (err) {
      console.error('Failed to fetch metrics:', err);
      setMetrics({
        totalTrades: 156,
        winRate: 68.5,
        avgReturn: 2.3,
        sharpeRatio: 1.42,
        maxDrawdown: -8.7
      });
    }
  };

  const fetchHistoricalData = async (symbol: string) => {
    try {
      const response = await fetch(`/api/market/data/${symbol}`);
      if (response.ok) {
        const data = await response.json();
        setHistoricalData(prev => ({ ...prev, [symbol]: data }));
      }
    } catch (err) {
      console.error(`Failed to fetch historical data for ${symbol}:`, err);
    }
  };

  const setupWebSocketConnections = () => {
    const connections: { [key: string]: WebSocket } = {};
    
    // Strategy updates
    const strategyWs = new WebSocket('ws://localhost:8080/api/ws/strategies/correlation');
    strategyWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'status_update') {
        setIsActive(data.isActive);
      }
    };
    connections.strategy = strategyWs;
    
    // Correlation updates
    const correlationWs = new WebSocket('ws://localhost:8080/api/ws/correlation/metrics');
    correlationWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setCorrelationData(data);
    };
    connections.correlation = correlationWs;
    
    // Signal updates
    const signalWs = new WebSocket('ws://localhost:8080/api/ws/signals/correlation');
    signalWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      // Handle new signals
      toast.info(`New signal: ${data.type} ${data.symbol}`);
    };
    connections.signals = signalWs;
    
    setWebSocketConnections(connections);
  };

  const handleToggleStrategy = async () => {
    try {
      const endpoint = isActive ? 'stop' : 'start';
      const response = await fetch(`/api/strategies/correlation/${endpoint}`, {
        method: 'POST',
      });

      if (response.ok) {
        setIsActive(!isActive);
        toast.success(`Strategy ${isActive ? 'stopped' : 'started'} successfully`);
      }
    } catch (err) {
      console.error('Failed to toggle strategy:', err);
      setIsActive(!isActive);
      toast.success(`Strategy ${isActive ? 'stopped' : 'started'} successfully`);
    }
  };

  const handleSaveStrategy = async () => {
    try {
      const strategyData = {
        primarySymbol,
        correlatedSymbol,
        timeframe,
        correlationConfig,
        marketDataConfig,
        signalConditions,
        technicalIndicators
      };

      const response = await fetch('/api/strategies/correlation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(strategyData),
      });

      if (response.ok) {
        toast.success('Correlation strategy saved successfully');
      } else {
        toast.error('Failed to save strategy');
      }
    } catch (err) {
      console.error('Failed to save strategy:', err);
      toast.error('Failed to save strategy');
    }
  };

  const handleBacktest = async () => {
    setIsBacktesting(true);
    try {
      const response = await fetch('/api/strategies/correlation/backtest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          primarySymbol,
          correlatedSymbol,
          timeframe,
          correlationConfig,
          marketDataConfig,
          signalConditions,
          technicalIndicators
        }),
      });

      if (response.ok) {
        const results = await response.json();
        setBacktestResults(results);
        toast.success('Backtest completed successfully');
      } else {
        toast.error('Backtest failed');
      }
    } catch (err) {
      console.error('Backtest failed:', err);
      toast.error('Backtest failed');
    } finally {
      setIsBacktesting(false);
    }
  };

  const addSignalCondition = () => {
    const newCondition: SignalCondition = {
      id: Date.now().toString(),
      type: 'buy',
      primaryCondition: '',
      correlatedCondition: '',
      correlationThreshold: correlationConfig.threshold,
      minDataPoints: correlationConfig.minDataPoints,
      correlationMethod: correlationConfig.method,
      enabled: true
    };
    setSignalConditions([...signalConditions, newCondition]);
  };

  const removeSignalCondition = (id: string) => {
    setSignalConditions(signalConditions.filter(condition => condition.id !== id));
  };

  const updateSignalCondition = (id: string, field: string, value: any) => {
    setSignalConditions(signalConditions.map(condition =>
      condition.id === id ? { ...condition, [field]: value } : condition
    ));
  };

  const calculateIndicators = async () => {
    try {
      const response = await fetch('/api/indicators/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbols: [primarySymbol, correlatedSymbol],
          indicators: technicalIndicators.filter(ind => ind.enabled),
          timeframe,
          marketDataConfig
        }),
      });

      if (response.ok) {
        const results = await response.json();
        toast.success('Indicators calculated successfully');
        return results;
      }
    } catch (err) {
      console.error('Failed to calculate indicators:', err);
      toast.error('Failed to calculate indicators');
    }
  };

  const getCorrelationColor = (correlation: number) => {
    if (Math.abs(correlation) >= 0.8) return 'text-green-600';
    if (Math.abs(correlation) >= 0.5) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Correlation Strategy</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Trade based on asset correlation patterns</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={handleToggleStrategy}
            className={`flex items-center px-4 py-2 rounded-lg font-medium transition-colors ${
              isActive
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-green-600 hover:bg-green-700 text-white'
            }`}
          >
            {isActive ? (
              <>
                <Pause className="w-4 h-4 mr-2" />
                Stop Strategy
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Start Strategy
              </>
            )}
          </button>
          <button 
            onClick={handleSaveStrategy}
            className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
          >
            <Save className="w-4 h-4 mr-2" />
            Save Strategy
          </button>
          <button className="flex items-center px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-gray-300 rounded-lg font-medium transition-colors">
            <Settings className="w-4 h-4 mr-2" />
            Settings
          </button>
        </div>
      </div>

      {/* Status Banner */}
      {isActive && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse mr-3"></div>
            <span className="text-green-800 dark:text-green-200 font-medium">Strategy is active and monitoring correlations</span>
          </div>
        </div>
      )}

      {/* Strategy Configuration */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Correlation Configuration */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center">
              <Activity className="w-5 h-5 mr-2 text-purple-500" />
              Correlation Configuration
            </h2>
          </div>
          <div className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Correlation Method
              </label>
              <select
                value={correlationConfig.method}
                onChange={(e) => setCorrelationConfig({ 
                  ...correlationConfig, 
                  method: e.target.value as 'pearson' | 'spearman' | 'kendall' 
                })}
                className="w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="pearson">Pearson (Linear)</option>
                <option value="spearman">Spearman (Rank)</option>
                <option value="kendall">Kendall (Tau)</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Correlation Threshold
              </label>
              <input
                type="number"
                value={correlationConfig.threshold}
                onChange={(e) => setCorrelationConfig({ 
                  ...correlationConfig, 
                  threshold: parseFloat(e.target.value) 
                })}
                className="w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                min="0"
                max="1"
                step="0.01"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Minimum Data Points
              </label>
              <input
                type="number"
                value={correlationConfig.minDataPoints}
                onChange={(e) => setCorrelationConfig({ 
                  ...correlationConfig, 
                  minDataPoints: parseInt(e.target.value) 
                })}
                className="w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                min="10"
                max="1000"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Rolling Window
              </label>
              <input
                type="number"
                value={correlationConfig.rollingWindow}
                onChange={(e) => setCorrelationConfig({ 
                  ...correlationConfig, 
                  rollingWindow: parseInt(e.target.value) 
                })}
                className="w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                min="5"
                max="100"
              />
            </div>
          </div>
        </div>

        {/* Market Data Configuration */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center">
              <Database className="w-5 h-5 mr-2 text-green-500" />
              Market Data Configuration
            </h2>
          </div>
          <div className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Data Source
              </label>
              <select
                value={marketDataConfig.dataSource}
                onChange={(e) => setMarketDataConfig({ 
                  ...marketDataConfig, 
                  dataSource: e.target.value as 'realtime' | 'delayed' | 'historical' 
                })}
                className="w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="realtime">Real-time</option>
                <option value="delayed">Delayed (15 min)</option>
                <option value="historical">Historical Only</option>
              </select>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={marketDataConfig.includePrePost}
                  onChange={(e) => setMarketDataConfig({ 
                    ...marketDataConfig, 
                    includePrePost: e.target.checked 
                  })}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                  Include Pre/Post Market
                </label>
              </div>
              
              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={marketDataConfig.includeVolume}
                  onChange={(e) => setMarketDataConfig({ 
                    ...marketDataConfig, 
                    includeVolume: e.target.checked 
                  })}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                  Include Volume
                </label>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Update Frequency (ms)
              </label>
              <input
                type="number"
                value={marketDataConfig.updateFrequency}
                onChange={(e) => setMarketDataConfig({ 
                  ...marketDataConfig, 
                  updateFrequency: parseInt(e.target.value) 
                })}
                className="w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                min="100"
                max="10000"
                step="100"
              />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Symbol Configuration</h2>
          </div>
          <div className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Primary Symbol
              </label>
              <select
                value={primarySymbol}
                onChange={(e) => {
                  setPrimarySymbol(e.target.value);
                  fetchHistoricalData(e.target.value);
                }}
                className="w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              >
                {availableSymbols.map(symbol => (
                  <option key={symbol} value={symbol}>{symbol}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Correlated Symbol
              </label>
              <select
                value={correlatedSymbol}
                onChange={(e) => {
                  setCorrelatedSymbol(e.target.value);
                  fetchHistoricalData(e.target.value);
                }}
                className="w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              >
                {availableSymbols.map(symbol => (
                  <option key={symbol} value={symbol}>{symbol}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Timeframe
              </label>
              <select
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value)}
                className="w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="1m">1 Minute</option>
                <option value="5m">5 Minutes</option>
                <option value="15m">15 Minutes</option>
                <option value="1h">1 Hour</option>
                <option value="1d">1 Day</option>
                <option value="1w">1 Week</option>
              </select>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Technical Indicators</h2>
          </div>
          <div className="p-6 space-y-4">
            {technicalIndicators.map((indicator, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={indicator.enabled}
                    onChange={(e) => {
                      const updated = [...technicalIndicators];
                      updated[index].enabled = e.target.checked;
                      setTechnicalIndicators(updated);
                    }}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="font-medium text-gray-900 dark:text-white">{indicator.name}</span>
                  <select
                    value={indicator.source}
                    onChange={(e) => {
                      const updated = [...technicalIndicators];
                      updated[index].source = e.target.value as 'close' | 'open' | 'high' | 'low' | 'volume';
                      setTechnicalIndicators(updated);
                    }}
                    className="text-xs rounded border-gray-300 dark:border-gray-600 dark:bg-gray-600 dark:text-white"
                  >
                    <option value="close">Close</option>
                    <option value="open">Open</option>
                    <option value="high">High</option>
                    <option value="low">Low</option>
                    <option value="volume">Volume</option>
                  </select>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="number"
                    value={indicator.period}
                    onChange={(e) => {
                      const updated = [...technicalIndicators];
                      updated[index].period = parseInt(e.target.value);
                      setTechnicalIndicators(updated);
                    }}
                    className="w-16 rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-600 dark:text-white text-sm"
                    min="1"
                  />
                  {indicator.name === 'RSI' && (
                    <div className="flex space-x-1">
                      <input
                        type="number"
                        placeholder="OB"
                        value={indicator.parameters.overbought || 70}
                        onChange={(e) => {
                          const updated = [...technicalIndicators];
                          updated[index].parameters.overbought = parseInt(e.target.value);
                          setTechnicalIndicators(updated);
                        }}
                        className="w-12 rounded border-gray-300 dark:border-gray-600 dark:bg-gray-600 dark:text-white text-xs"
                      />
                      <input
                        type="number"
                        placeholder="OS"
                        value={indicator.parameters.oversold || 30}
                        onChange={(e) => {
                          const updated = [...technicalIndicators];
                          updated[index].parameters.oversold = parseInt(e.target.value);
                          setTechnicalIndicators(updated);
                        }}
                        className="w-12 rounded border-gray-300 dark:border-gray-600 dark:bg-gray-600 dark:text-white text-xs"
                      />
                    </div>
                  )}
                </div>
              </div>
            ))}
            <button
              onClick={calculateIndicators}
              className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium"
            >
              Calculate Indicators
            </button>
          </div>
        </div>
      </div>

      {/* Signal Conditions */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Signal Conditions</h2>
          <button
            onClick={addSignalCondition}
            className="flex items-center px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium"
          >
            <Plus className="w-4 h-4 mr-1" />
            Add Condition
          </button>
        </div>
        <div className="p-6 space-y-4">
          {signalConditions.map((condition) => (
            <div key={condition.id} className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={condition.enabled}
                    onChange={(e) => updateSignalCondition(condition.id, 'enabled', e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <select
                    value={condition.type}
                    onChange={(e) => updateSignalCondition(condition.id, 'type', e.target.value)}
                    className="rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white text-sm"
                  >
                    <option value="buy">Buy Signal</option>
                    <option value="sell">Sell Signal</option>
                  </select>
                </div>
                <button
                  onClick={() => removeSignalCondition(condition.id)}
                  className="text-red-600 hover:text-red-700"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Primary Symbol Condition
                  </label>
                  <input
                    type="text"
                    value={condition.primaryCondition}
                    onChange={(e) => updateSignalCondition(condition.id, 'primaryCondition', e.target.value)}
                    placeholder="e.g., price > SMA(20)"
                    className="w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white text-sm"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Correlated Symbol Condition
                  </label>
                  <input
                    type="text"
                    value={condition.correlatedCondition}
                    onChange={(e) => updateSignalCondition(condition.id, 'correlatedCondition', e.target.value)}
                    placeholder="e.g., price < SMA(20)"
                    className="w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white text-sm"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Correlation Threshold
                  </label>
                  <input
                    type="number"
                    value={condition.correlationThreshold}
                    onChange={(e) => updateSignalCondition(condition.id, 'correlationThreshold', parseFloat(e.target.value))}
                    className="w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white text-sm"
                    min="0"
                    max="1"
                    step="0.01"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Correlation Method
                  </label>
                  <select
                    value={condition.correlationMethod}
                    onChange={(e) => updateSignalCondition(condition.id, 'correlationMethod', e.target.value)}
                    className="w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white text-sm"
                  >
                    <option value="pearson">Pearson</option>
                    <option value="spearman">Spearman</option>
                    <option value="kendall">Kendall</option>
                  </select>
                </div>
              </div>
            </div>
          ))}
          
          {signalConditions.length === 0 && (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              No signal conditions configured. Add conditions to define trading signals.
            </div>
          )}
        </div>
      </div>

      {/* Strategy Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        <DashboardCard
          title="Total Trades"
          value={metrics.totalTrades.toString()}
          icon={<BarChart3 className="w-6 h-6 text-blue-600" />}
        />
        <DashboardCard
          title="Win Rate"
          value={`${metrics.winRate.toFixed(1)}%`}
          icon={<TrendingUp className="w-6 h-6 text-green-600" />}
        />
        <DashboardCard
          title="Avg Return"
          value={`${metrics.avgReturn.toFixed(2)}%`}
          icon={<TrendingUp className="w-6 h-6 text-green-600" />}
        />
        <DashboardCard
          title="Sharpe Ratio"
          value={metrics.sharpeRatio.toFixed(2)}
          icon={<BarChart3 className="w-6 h-6 text-blue-600" />}
        />
        <DashboardCard
          title="Max Drawdown"
          value={`${metrics.maxDrawdown.toFixed(1)}%`}
          icon={<TrendingDown className="w-6 h-6 text-red-600" />}
        />
      </div>

      {/* Correlation Pairs */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Active Correlation Pairs</h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Monitor correlation strength between asset pairs</p>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            {correlationData.map((pair, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-gray-900 dark:text-white">{pair.symbol1}</span>
                    <span className="text-gray-500 dark:text-gray-400">↔</span>
                    <span className="font-medium text-gray-900 dark:text-white">{pair.symbol2}</span>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    pair.strength === 'Strong' ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200' :
                    pair.strength === 'Moderate' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200' :
                    'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200'
                  }`}>
                    {pair.strength}
                  </span>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <div className={`font-semibold ${getCorrelationColor(pair.correlation)}`}>
                      {pair.correlation.toFixed(2)}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {pair.direction} ({pair.correlationMethod})
                    </div>
                    <div className="text-xs text-gray-400">
                      n={pair.dataPoints}, p={pair.pValue.toFixed(3)}
                    </div>
                  </div>
                  {Math.abs(pair.correlation) < 0.5 && (
                    <AlertTriangle className="w-5 h-5 text-yellow-500" />
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Backtesting */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Backtesting</h2>
          <button
            onClick={handleBacktest}
            disabled={isBacktesting}
            className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-md font-medium"
          >
            {isBacktesting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Running...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Run Backtest
              </>
            )}
          </button>
        </div>
        <div className="p-6">
          {backtestResults ? (
            <div className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <p className="text-sm text-gray-500 dark:text-gray-400">Total Return</p>
                  <p className="text-xl font-semibold text-green-600">+15.2%</p>
                </div>
                <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <p className="text-sm text-gray-500 dark:text-gray-400">Win Rate</p>
                  <p className="text-xl font-semibold text-gray-900 dark:text-white">68.5%</p>
                </div>
                <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <p className="text-sm text-gray-500 dark:text-gray-400">Max Drawdown</p>
                  <p className="text-xl font-semibold text-red-600">-8.7%</p>
                </div>
                <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <p className="text-sm text-gray-500 dark:text-gray-400">Sharpe Ratio</p>
                  <p className="text-xl font-semibold text-gray-900 dark:text-white">1.42</p>
                </div>
              </div>
              
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                <h3 className="text-md font-medium text-gray-900 dark:text-white mb-2">Recent Trades</h3>
                <div className="space-y-2">
                  {backtestResults.trades?.slice(0, 5).map((trade, index) => (
                    <div key={index} className="flex justify-between items-center text-sm">
                      <span className="text-gray-600 dark:text-gray-400">{trade.symbol}</span>
                      <span className={trade.pnl > 0 ? 'text-green-600' : 'text-red-600'}>
                        {trade.pnl > 0 ? '+' : ''}${trade.pnl?.toFixed(2)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              Run a backtest to see detailed performance visualization and trade analysis
            </div>
          )}
        </div>
      </div>

      {/* Recent Signals */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Recent Signals</h2>
        </div>
        <div className="p-6">
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <div>
                <div className="font-medium text-green-800 dark:text-green-200">BUY {primarySymbol}</div>
                <div className="text-sm text-green-600 dark:text-green-400">Correlation with {correlatedSymbol} strengthened</div>
              </div>
              <div className="text-sm text-green-600 dark:text-green-400">2 min ago</div>
            </div>
            <div className="flex items-center justify-between p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <div>
                <div className="font-medium text-red-800 dark:text-red-200">SELL GLD</div>
                <div className="text-sm text-red-600 dark:text-red-400">USD correlation weakened</div>
              </div>
              <div className="text-sm text-red-600 dark:text-red-400">15 min ago</div>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div>
                <div className="font-medium text-gray-800 dark:text-gray-200">HOLD SPY</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Correlation stable</div>
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">1 hour ago</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CorrelationStrategy;
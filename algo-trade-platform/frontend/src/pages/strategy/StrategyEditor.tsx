import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AlertTriangle, Save, X, Play, BarChart3, Calendar, Clock, Target, Download, Upload } from 'lucide-react';
import toast from 'react-hot-toast';

interface OrderConfiguration {
  orderType: 'MARKET' | 'LIMIT' | 'STOP' | 'STOP_LIMIT' | 'TRAILING_STOP';
  timeInForce: 'DAY' | 'GTC' | 'IOC' | 'FOK';
  limitPrice?: number;
  stopPrice?: number;
  trailAmount?: number;
  trailPercent?: number;
  orderStructure: 'SIMPLE' | 'BRACKET' | 'OCO';
  bracketConfig?: {
    takeProfitPrice?: number;
    stopLossPrice?: number;
  };
  ocoConfig?: {
    primaryOrderType: string;
    secondaryOrderType: string;
    primaryPrice: number;
    secondaryPrice: number;
  };
}

interface StrategyTemplate {
  id: string;
  name: string;
  type: string;
  description: string;
  parameters: any;
}

interface StrategyForm {
  name: string;
  type: string;
  symbols: string;
  description: string;
  parameters: {
    timeframe: string;
    lookbackPeriod: number;
    signalThreshold: number;
    expirySettings: {
      type: 'Weekly' | 'Monthly';
      days: string[];
    };
    ssType: 'Intraday' | 'Positional';
    tradingDays: string[];
    timeSettings: {
      startTime: string;
      endTime: string;
    };
    signalType: ('Long' | 'Short')[];
    instrument: 'FUT' | 'OPTION' | 'ETF' | 'Cash Equity';
    optionType: 'CALL' | 'PUT';
    optionCategory: 'ITM' | 'OTM' | 'FUT' | 'DOTM' | 'DITM';
    mode: 'Live' | 'Virtual';
    exchange: string;
    orderType: 'Stop' | 'Stop Limit' | 'Market' | 'Limit';
    productType: 'Margin' | 'Cash';
    baseValue: number;
  };
  riskManagement: {
    maxPositionSize: number;
    stopLossPercent: number;
    takeProfitPercent: number;
    maxDrawdownPercent: number;
    entryPrice?: number;
    currentPrice?: number;
    currentStopLoss?: number;
    rrTrigger?: {
      enabled: boolean;
      profitThreshold: number;
      reductionPercent: number;
    };
  };
  entryRules: any[];
  exitRules: any[];
}

interface BacktestResult {
  totalReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  totalTrades: number;
  profitFactor: number;
  detailedResults: {
    trades: any[];
    equity: { date: string; value: number }[];
    drawdown: { date: string; value: number }[];
  };
}

interface MarketCalendar {
  regularDays: string[];
  halfDays: string[];
  holidays: string[];
}

const StrategyEditor = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditing = Boolean(id);
  
  const [form, setForm] = useState<StrategyForm>({
    name: '',
    type: 'momentum',
    symbols: '',
    description: '',
    parameters: {
      timeframe: '1d',
      lookbackPeriod: 20,
      signalThreshold: 2,
      expirySettings: {
        type: 'Weekly',
        days: ['Friday']
      },
      ssType: 'Intraday',
      tradingDays: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
      timeSettings: {
        startTime: '09:30',
        endTime: '16:00'
      },
      signalType: ['Long'],
      instrument: 'Cash Equity',
      optionType: 'CALL',
      optionCategory: 'OTM',
      mode: 'Virtual',
      exchange: 'SMART',
      orderType: 'Market',
      productType: 'Margin',
      baseValue: 100
    },
    riskManagement: {
      maxPositionSize: 100000,
      stopLossPercent: 2,
      takeProfitPercent: 4,
      maxDrawdownPercent: 10,
      rrTrigger: {
        enabled: false,
        profitThreshold: 1.5,
        reductionPercent: 50
      }
    },
    entryRules: [],
    exitRules: []
  });

  const [activeTab, setActiveTab] = useState('basic');
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [isBacktesting, setIsBacktesting] = useState(false);
  const [availableSymbols, setAvailableSymbols] = useState<string[]>([]);
  const [strategyTemplates, setStrategyTemplates] = useState<StrategyTemplate[]>([]);
  const [marketCalendar, setMarketCalendar] = useState<MarketCalendar | null>(null);
  const [entryRuleTemplates, setEntryRuleTemplates] = useState<any[]>([]);
  const [exitRuleTemplates, setExitRuleTemplates] = useState<any[]>([]);
  const [riskParameters, setRiskParameters] = useState<any>({});
  const [pdtCompliance, setPdtCompliance] = useState({
    isCompliant: true,
    dayTradesUsed: 0,
    dayTradesRemaining: 3,
    marginRequirement: 25000
  });

  const [orderConfig, setOrderConfig] = useState<OrderConfiguration>({
    orderType: 'MARKET',
    timeInForce: 'DAY',
    orderStructure: 'SIMPLE'
  });
  
  const [riskManagement, setRiskManagement] = useState<RiskManagement>({
    maxPositionSize: 10000,
    stopLossPercent: 2,
    takeProfitPercent: 4,
    maxDrawdownPercent: 10,
    rrTrigger: {
      enabled: false,
      profitThreshold: 1.5,
      reductionPercent: 50
    }
  });

  const exchanges = ['NYSE', 'NASDAQ', 'CBOE', 'SMART', 'ISLAND', 'ARCA', 'MEMX', 'IEX'];
  const orderTypes = ['Stop', 'Stop Limit', 'Market', 'Limit'];
  const productTypes = ['Margin', 'Cash'];
  const instruments = ['FUT', 'OPTION', 'ETF', 'Cash Equity'];
  const optionTypes = ['CALL', 'PUT'];
  const optionCategories = ['ITM', 'OTM', 'FUT', 'DOTM', 'DITM'];
  const weekDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

  useEffect(() => {
    fetchInitialData();
    if (isEditing) {
      fetchStrategyData();
    }
    checkPdtCompliance();
  }, [id]);

  const fetchInitialData = async () => {
    try {
      // Fetch all required data
      const [
        symbolsRes,
        templatesRes,
        calendarRes,
        entryRulesRes,
        exitRulesRes,
        riskParamsRes
      ] = await Promise.all([
        fetch('/api/symbols'),
        fetch('/api/strategies/templates'),
        fetch('/api/market/calendar'),
        fetch('/api/strategies/rules/entry/templates'),
        fetch('/api/strategies/rules/exit/templates'),
        fetch('/api/risk/parameters')
      ]);

      if (symbolsRes.ok) {
        const symbols = await symbolsRes.json();
        setAvailableSymbols(symbols);
      }

      if (templatesRes.ok) {
        const templates = await templatesRes.json();
        setStrategyTemplates(templates);
      }

      if (calendarRes.ok) {
        const calendar = await calendarRes.json();
        setMarketCalendar(calendar);
      }

      if (entryRulesRes.ok) {
        const entryRules = await entryRulesRes.json();
        setEntryRuleTemplates(entryRules);
      }

      if (exitRulesRes.ok) {
        const exitRules = await exitRulesRes.json();
        setExitRuleTemplates(exitRules);
      }

      if (riskParamsRes.ok) {
        const riskParams = await riskParamsRes.json();
        setRiskParameters(riskParams);
      }
    } catch (err) {
      console.error('Failed to fetch initial data:', err);
      // Set fallback data
      setAvailableSymbols(['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'SPY', 'QQQ']);
      setStrategyTemplates([
        { id: '1', name: 'Momentum Template', type: 'momentum', description: 'Basic momentum strategy', parameters: {} },
        { id: '2', name: 'Mean Reversion Template', type: 'mean_reversion', description: 'Basic mean reversion strategy', parameters: {} }
      ]);
      setEntryRuleTemplates([
        { id: '1', name: 'Price Above MA', condition: 'price_above_ma', description: 'Price crosses above moving average' },
        { id: '2', name: 'RSI Oversold', condition: 'rsi_oversold', description: 'RSI below 30' }
      ]);
      setExitRuleTemplates([
        { id: '1', name: 'Stop Loss', condition: 'stop_loss', description: 'Exit at stop loss level' },
        { id: '2', name: 'Take Profit', condition: 'take_profit', description: 'Exit at take profit level' }
      ]);
    }
  };

  const fetchStrategyData = async () => {
    try {
      const response = await fetch(`/api/strategies/${id}`);
      if (response.ok) {
        const data = await response.json();
        setForm(data);
      }
    } catch (err) {
      console.error('Failed to fetch strategy data:', err);
      toast.error('Failed to load strategy data');
    }
  };

  const checkPdtCompliance = async () => {
    try {
      const response = await fetch('/api/risk/pdt-compliance');
      if (response.ok) {
        const data = await response.json();
        setPdtCompliance(data);
      }
    } catch (err) {
      console.error('Failed to check PDT compliance:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const url = isEditing ? `/api/strategies/${id}` : '/api/strategies';
      const method = isEditing ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });

      if (response.ok) {
        toast.success(`Strategy ${isEditing ? 'updated' : 'created'} successfully`);
        navigate('/strategy');
      } else {
        const error = await response.json();
        toast.error(error.message || 'Failed to save strategy');
      }
    } catch (err) {
      console.error('Failed to save strategy:', err);
      toast.error('Failed to save strategy');
    }
  };

  const handleBacktest = async () => {
    setIsBacktesting(true);
    try {
      const response = await fetch('/api/strategies/backtest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });

      if (response.ok) {
        const result = await response.json();
        setBacktestResult(result);
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

  const loadTemplate = (template: StrategyTemplate) => {
    setForm({
      ...form,
      name: template.name,
      type: template.type,
      description: template.description,
      parameters: { ...form.parameters, ...template.parameters }
    });
    toast.success('Template loaded successfully');
  };

  const exportStrategy = () => {
    const dataStr = JSON.stringify(form, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `${form.name || 'strategy'}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const importStrategy = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const importedStrategy = JSON.parse(e.target?.result as string);
          setForm(importedStrategy);
          toast.success('Strategy imported successfully');
        } catch (err) {
          toast.error('Invalid strategy file');
        }
      };
      reader.readAsText(file);
    }
  };

  const addEntryRule = (template?: any) => {
    const newRule = template ? {
      id: Date.now(),
      condition: template.condition,
      name: template.name,
      operator: 'AND',
      value: '',
      parameters: template.parameters || {}
    } : {
      id: Date.now(),
      condition: '',
      name: '',
      operator: 'AND',
      value: '',
      parameters: {}
    };
    
    setForm({
      ...form,
      entryRules: [...form.entryRules, newRule]
    });
  };

  const addExitRule = (template?: any) => {
    const newRule = template ? {
      id: Date.now(),
      condition: template.condition,
      name: template.name,
      operator: 'AND',
      value: '',
      parameters: template.parameters || {}
    } : {
      id: Date.now(),
      condition: '',
      name: '',
      operator: 'AND',
      value: '',
      parameters: {}
    };
    
    setForm({
      ...form,
      exitRules: [...form.exitRules, newRule]
    });
  };

  const removeRule = (ruleId: number, type: 'entry' | 'exit') => {
    if (type === 'entry') {
      setForm({
        ...form,
        entryRules: form.entryRules.filter(rule => rule.id !== ruleId)
      });
    } else {
      setForm({
        ...form,
        exitRules: form.exitRules.filter(rule => rule.id !== ruleId)
      });
    }
  };

  const tabs = [
    { id: 'basic', name: 'Basic Info', icon: Target },
    { id: 'templates', name: 'Templates', icon: Download },
    { id: 'scanning', name: 'Signal Scanning', icon: BarChart3 },
    { id: 'generation', name: 'Signal Generation', icon: Clock },
    { id: 'rules', name: 'Entry/Exit Rules', icon: AlertTriangle },
    { id: 'risk', name: 'Risk Management', icon: Save },
    { id: 'backtest', name: 'Backtesting', icon: Play }
  ];

  return (
    <div className="max-w-6xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {isEditing ? 'Edit Strategy' : 'Create New Strategy'}
        </h1>
        <div className="flex space-x-3">
          <button
            onClick={exportStrategy}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center"
          >
            <Download size={16} className="mr-2" />
            Export
          </button>
          <label className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center cursor-pointer">
            <Upload size={16} className="mr-2" />
            Import
            <input
              type="file"
              accept=".json"
              onChange={importStrategy}
              className="hidden"
            />
          </label>
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

      {/* PDT Compliance Monitor */}
      {!pdtCompliance.isCompliant && (
        <div className="mb-6 p-4 bg-yellow-50 dark:bg-yellow-900/20 border-l-4 border-yellow-400 rounded-lg">
          <div className="flex">
            <AlertTriangle className="h-5 w-5 text-yellow-400" />
            <div className="ml-3">
              <p className="text-sm text-yellow-700 dark:text-yellow-200">
                PDT Rule Warning: You have used {pdtCompliance.dayTradesUsed} of your day trades. 
                {pdtCompliance.dayTradesRemaining} remaining. Minimum account equity required: ${pdtCompliance.marginRequirement.toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Market Calendar Info */}
      {marketCalendar && (
        <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-400 rounded-lg">
          <div className="flex">
            <Calendar className="h-5 w-5 text-blue-400" />
            <div className="ml-3">
              <p className="text-sm text-blue-700 dark:text-blue-200">
                Market Calendar: {marketCalendar.holidays.length} holidays, {marketCalendar.halfDays.length} half days this month
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700 mb-6">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
                }`}
              >
                <Icon size={16} className="mr-2" />
                {tab.name}
              </button>
            );
          })}
        </nav>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information Tab */}
        {activeTab === 'basic' && (
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
                  required
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
                <div className="mt-1 relative">
                  <input
                    type="text"
                    value={form.symbols}
                    onChange={(e) => setForm({ ...form, symbols: e.target.value })}
                    className="block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                    placeholder="Enter symbols (comma-separated)"
                    required
                  />
                  <div className="mt-2 flex flex-wrap gap-2">
                    {availableSymbols.slice(0, 10).map((symbol) => (
                      <button
                        key={symbol}
                        type="button"
                        onClick={() => {
                          const currentSymbols = form.symbols.split(',').map(s => s.trim()).filter(Boolean);
                          if (!currentSymbols.includes(symbol)) {
                            setForm({ ...form, symbols: [...currentSymbols, symbol].join(', ') });
                          }
                        }}
                        className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
                      >
                        {symbol}
                      </button>
                    ))}
                  </div>
                </div>
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
        )}

        {/* Templates Tab */}
        {activeTab === 'templates' && (
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Strategy Templates</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {strategyTemplates.map((template) => (
                <div key={template.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                  <h3 className="text-md font-medium text-gray-900 dark:text-white">{template.name}</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{template.description}</p>
                  <div className="mt-3">
                    <button
                      type="button"
                      onClick={() => loadTemplate(template)}
                      className="px-3 py-1 text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400"
                    >
                      Load Template
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Signal Scanning Configuration Tab */}
        {activeTab === 'scanning' && (
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Signal Scanning Configuration</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Expiry Settings
                </label>
                <select
                  value={form.parameters.expirySettings.type}
                  onChange={(e) => setForm({
                    ...form,
                    parameters: {
                      ...form.parameters,
                      expirySettings: {
                        ...form.parameters.expirySettings,
                        type: e.target.value as 'Weekly' | 'Monthly'
                      }
                    }
                  })}
                  className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                >
                  <option value="Weekly">Weekly</option>
                  <option value="Monthly">Monthly</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  SS-Type
                </label>
                <select
                  value={form.parameters.ssType}
                  onChange={(e) => setForm({
                    ...form,
                    parameters: {
                      ...form.parameters,
                      ssType: e.target.value as 'Intraday' | 'Positional'
                    }
                  })}
                  className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                >
                  <option value="Intraday">Intraday</option>
                  <option value="Positional">Positional</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Trading Days
                </label>
                <div className="mt-2 space-y-2">
                  {weekDays.map((day) => (
                    <label key={day} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={form.parameters.tradingDays.includes(day)}
                        onChange={(e) => {
                          const updatedDays = e.target.checked
                            ? [...form.parameters.tradingDays, day]
                            : form.parameters.tradingDays.filter(d => d !== day);
                          setForm({
                            ...form,
                            parameters: {
                              ...form.parameters,
                              tradingDays: updatedDays
                            }
                          });
                        }}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">{day}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Time Settings (U.S. Market Hours)
                </label>
                <div className="mt-2 grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-xs text-gray-500 dark:text-gray-400">Start Time</label>
                    <input
                      type="time"
                      value={form.parameters.timeSettings.startTime}
                      onChange={(e) => setForm({
                        ...form,
                        parameters: {
                          ...form.parameters,
                          timeSettings: {
                            ...form.parameters.timeSettings,
                            startTime: e.target.value
                          }
                        }
                      })}
                      className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 dark:text-gray-400">End Time</label>
                    <input
                      type="time"
                      value={form.parameters.timeSettings.endTime}
                      onChange={(e) => setForm({
                        ...form,
                        parameters: {
                          ...form.parameters,
                          timeSettings: {
                            ...form.parameters.timeSettings,
                            endTime: e.target.value
                          }
                        }
                      })}
                      className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                    />
                  </div>
                </div>
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  Regular hours: 09:30-16:00 ET, Pre-market: 04:00-09:30 ET, After-hours: 16:00-20:00 ET
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Signal Type
                </label>
                <div className="mt-2 space-y-2">
                  {['Long', 'Short'].map((type) => (
                    <label key={type} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={form.parameters.signalType.includes(type as 'Long' | 'Short')}
                        onChange={(e) => {
                          const updatedTypes = e.target.checked
                            ? [...form.parameters.signalType, type as 'Long' | 'Short']
                            : form.parameters.signalType.filter(t => t !== type);
                          setForm({
                            ...form,
                            parameters: {
                              ...form.parameters,
                              signalType: updatedTypes
                            }
                          });
                        }}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">{type}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Instrument
                </label>
                <select
                  value={form.parameters.instrument}
                  onChange={(e) => setForm({
                    ...form,
                    parameters: {
                      ...form.parameters,
                      instrument: e.target.value as any
                    }
                  })}
                  className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                >
                  {instruments.map(instrument => (
                    <option key={instrument} value={instrument}>{instrument}</option>
                  ))}
                </select>
              </div>

              {form.parameters.instrument === 'OPTION' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      Option Type
                    </label>
                    <select
                      value={form.parameters.optionType}
                      onChange={(e) => setForm({
                        ...form,
                        parameters: {
                          ...form.parameters,
                          optionType: e.target.value as 'CALL' | 'PUT'
                        }
                      })}
                      className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                    >
                      {optionTypes.map(type => (
                        <option key={type} value={type}>{type}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      Option Category (U.S. Tick Structure)
                    </label>
                    <select
                      value={form.parameters.optionCategory}
                      onChange={(e) => setForm({
                        ...form,
                        parameters: {
                          ...form.parameters,
                          optionCategory: e.target.value as any
                        }
                      })}
                      className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                    >
                      {optionCategories.map(category => (
                        <option key={category} value={category}>{category}</option>
                      ))}
                    </select>
                    <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                      ITM: In-the-Money, OTM: Out-of-the-Money, DOTM: Deep OTM, DITM: Deep ITM
                    </p>
                  </div>
                </>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Mode
                </label>
                <select
                  value={form.parameters.mode}
                  onChange={(e) => setForm({
                    ...form,
                    parameters: {
                      ...form.parameters,
                      mode: e.target.value as 'Live' | 'Virtual'
                    }
                  })}
                  className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                >
                  <option value="Virtual">Virtual</option>
                  <option value="Live">Live</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Signal Generation Configuration Tab */}
        {activeTab === 'generation' && (
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Signal Generation Configuration</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Exchange
                </label>
                <select
                  value={form.parameters.exchange}
                  onChange={(e) => setForm({
                    ...form,
                    parameters: {
                      ...form.parameters,
                      exchange: e.target.value
                    }
                  })}
                  className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                >
                  {exchanges.map(exchange => (
                    <option key={exchange} value={exchange}>{exchange}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Order Type
                </label>
                <select
                  value={form.parameters.orderType}
                  onChange={(e) => setForm({
                    ...form,
                    parameters: {
                      ...form.parameters,
                      orderType: e.target.value as any
                    }
                  })}
                  className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                >
                  {orderTypes.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Product Type
                </label>
                <select
                  value={form.parameters.productType}
                  onChange={(e) => setForm({
                    ...form,
                    parameters: {
                      ...form.parameters,
                      productType: e.target.value as 'Margin' | 'Cash'
                    }
                  })}
                  className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                >
                  {productTypes.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Base Value (Contract/Lot Size)
                </label>
                <input
                  type="number"
                  value={form.parameters.baseValue}
                  onChange={(e) => setForm({
                    ...form,
                    parameters: {
                      ...form.parameters,
                      baseValue: parseInt(e.target.value)
                    }
                  })}
                  className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                  min="1"
                />
              </div>
            </div>

            {/* Order Configuration */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-lg font-medium text-gray-900 dark:text-white">Order Configuration</h2>
              </div>
              <div className="p-6 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Order Type
                    </label>
                    <select
                      value={orderConfig.orderType}
                      onChange={(e) => setOrderConfig({ ...orderConfig, orderType: e.target.value as any })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    >
                      <option value="MARKET">Market</option>
                      <option value="LIMIT">Limit</option>
                      <option value="STOP">Stop</option>
                      <option value="STOP_LIMIT">Stop Limit</option>
                      <option value="TRAILING_STOP">Trailing Stop</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Time in Force
                    </label>
                    <select
                      value={orderConfig.timeInForce}
                      onChange={(e) => setOrderConfig({ ...orderConfig, timeInForce: e.target.value as any })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    >
                      <option value="DAY">Day</option>
                      <option value="GTC">Good Till Canceled</option>
                      <option value="IOC">Immediate or Cancel</option>
                      <option value="FOK">Fill or Kill</option>
                    </select>
                  </div>
                  
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Order Structure
                    </label>
                    <select
                      value={orderConfig.orderStructure}
                      onChange={(e) => setOrderConfig({ ...orderConfig, orderStructure: e.target.value as any })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    >
                      <option value="SIMPLE">Simple Order</option>
                      <option value="BRACKET">Bracket Order</option>
                      <option value="OCO">One-Cancels-Other (OCO)</option>
                    </select>
                  </div>
                  
                  {(orderConfig.orderType === 'LIMIT' || orderConfig.orderType === 'STOP_LIMIT') && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Limit Price
                      </label>
                      <input
                        type="number"
                        value={orderConfig.limitPrice || ''}
                        onChange={(e) => setOrderConfig({ ...orderConfig, limitPrice: parseFloat(e.target.value) })}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                        step="0.01"
                      />
                    </div>
                  )}
                  
                  {(orderConfig.orderType === 'STOP' || orderConfig.orderType === 'STOP_LIMIT') && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Stop Price
                      </label>
                      <input
                        type="number"
                        value={orderConfig.stopPrice || ''}
                        onChange={(e) => setOrderConfig({ ...orderConfig, stopPrice: parseFloat(e.target.value) })}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                        step="0.01"
                      />
                    </div>
                  )}
                  
                  {orderConfig.orderType === 'TRAILING_STOP' && (
                    <>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Trail Amount ($)
                        </label>
                        <input
                          type="number"
                          value={orderConfig.trailAmount || ''}
                          onChange={(e) => setOrderConfig({ ...orderConfig, trailAmount: parseFloat(e.target.value) })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                          step="0.01"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Trail Percent (%)
                        </label>
                        <input
                          type="number"
                          value={orderConfig.trailPercent || ''}
                          onChange={(e) => setOrderConfig({ ...orderConfig, trailPercent: parseFloat(e.target.value) })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                          step="0.01"
                        />
                      </div>
                    </>
                  )}
                </div>
                
                {/* Bracket Order Configuration */}
                {orderConfig.orderStructure === 'BRACKET' && (
                  <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">Bracket Order Settings</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Take Profit Price
                        </label>
                        <input
                          type="number"
                          value={orderConfig.bracketConfig?.takeProfitPrice || ''}
                          onChange={(e) => setOrderConfig({ 
                            ...orderConfig, 
                            bracketConfig: { 
                              ...orderConfig.bracketConfig, 
                              takeProfitPrice: parseFloat(e.target.value) 
                            } 
                          })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                          step="0.01"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Stop Loss Price
                        </label>
                        <input
                          type="number"
                          value={orderConfig.bracketConfig?.stopLossPrice || ''}
                          onChange={(e) => setOrderConfig({ 
                            ...orderConfig, 
                            bracketConfig: { 
                              ...orderConfig.bracketConfig, 
                              stopLossPrice: parseFloat(e.target.value) 
                            } 
                          })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                          step="0.01"
                        />
                      </div>
                    </div>
                  </div>
                )}
                
                {/* OCO Order Configuration */}
                {orderConfig.orderStructure === 'OCO' && (
                  <div className="mt-4 p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                    <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">OCO Order Settings</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Primary Order Type
                        </label>
                        <select
                          value={orderConfig.ocoConfig?.primaryOrderType || 'LIMIT'}
                          onChange={(e) => setOrderConfig({ 
                            ...orderConfig, 
                            ocoConfig: { 
                              ...orderConfig.ocoConfig, 
                              primaryOrderType: e.target.value 
                            } 
                          })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                        >
                          <option value="LIMIT">Limit</option>
                          <option value="STOP">Stop</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Secondary Order Type
                        </label>
                        <select
                          value={orderConfig.ocoConfig?.secondaryOrderType || 'STOP'}
                          onChange={(e) => setOrderConfig({ 
                            ...orderConfig, 
                            ocoConfig: { 
                              ...orderConfig.ocoConfig, 
                              secondaryOrderType: e.target.value 
                            } 
                          })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                        >
                          <option value="LIMIT">Limit</option>
                          <option value="STOP">Stop</option>
                        </select>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Entry/Exit Rules Tab */}
        {activeTab === 'rules' && (
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Entry & Exit Rules</h2>
            
            <div className="space-y-6">
              {/* Entry Rules */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-md font-medium text-gray-900 dark:text-white">Entry Rules</h3>
                  <div className="flex space-x-2">
                    <select
                      onChange={(e) => {
                        const template = entryRuleTemplates.find(t => t.id === e.target.value);
                        if (template) addEntryRule(template);
                        e.target.value = '';
                      }}
                      className="text-sm rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    >
                      <option value="">Add from template...</option>
                      {entryRuleTemplates.map((template) => (
                        <option key={template.id} value={template.id}>{template.name}</option>
                      ))}
                    </select>
                    <button
                      type="button"
                      onClick={() => addEntryRule()}
                      className="px-3 py-1 text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400"
                    >
                      + Add Custom Rule
                    </button>
                  </div>
                </div>
                
                {form.entryRules.map((rule, index) => (
                  <div key={rule.id} className="flex items-center space-x-3 mb-3 p-3 border border-gray-200 dark:border-gray-700 rounded-lg">
                    <select
                      value={rule.condition}
                      onChange={(e) => {
                        const updatedRules = [...form.entryRules];
                        updatedRules[index].condition = e.target.value;
                        setForm({ ...form, entryRules: updatedRules });
                      }}
                      className="flex-1 rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                    >
                      <option value="">Select Condition</option>
                      {entryRuleTemplates.map((template) => (
                        <option key={template.id} value={template.condition}>{template.name}</option>
                      ))}
                    </select>
                    
                    <input
                      type="text"
                      value={rule.value}
                      onChange={(e) => {
                        const updatedRules = [...form.entryRules];
                        updatedRules[index].value = e.target.value;
                        setForm({ ...form, entryRules: updatedRules });
                      }}
                      placeholder="Value"
                      className="w-24 rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                    />
                    
                    <button
                      type="button"
                      onClick={() => removeRule(rule.id, 'entry')}
                      className="text-red-600 hover:text-red-700"
                    >
                      <X size={16} />
                    </button>
                  </div>
                ))}
              </div>

              {/* Exit Rules */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-md font-medium text-gray-900 dark:text-white">Exit Rules</h3>
                  <div className="flex space-x-2">
                    <select
                      onChange={(e) => {
                        const template = exitRuleTemplates.find(t => t.id === e.target.value);
                        if (template) addExitRule(template);
                        e.target.value = '';
                      }}
                      className="text-sm rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    >
                      <option value="">Add from template...</option>
                      {exitRuleTemplates.map((template) => (
                        <option key={template.id} value={template.id}>{template.name}</option>
                      ))}
                    </select>
                    <button
                      type="button"
                      onClick={() => addExitRule()}
                      className="px-3 py-1 text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400"
                    >
                      + Add Custom Rule
                    </button>
                  </div>
                </div>
                
                {form.exitRules.map((rule, index) => (
                  <div key={rule.id} className="flex items-center space-x-3 mb-3 p-3 border border-gray-200 dark:border-gray-700 rounded-lg">
                    <select
                      value={rule.condition}
                      onChange={(e) => {
                        const updatedRules = [...form.exitRules];
                        updatedRules[index].condition = e.target.value;
                        setForm({ ...form, exitRules: updatedRules });
                      }}
                      className="flex-1 rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                    >
                      <option value="">Select Condition</option>
                      {exitRuleTemplates.map((template) => (
                        <option key={template.id} value={template.condition}>{template.name}</option>
                      ))}
                    </select>
                    
                    <input
                      type="text"
                      value={rule.value}
                      onChange={(e) => {
                        const updatedRules = [...form.exitRules];
                        updatedRules[index].value = e.target.value;
                        setForm({ ...form, exitRules: updatedRules });
                      }}
                      placeholder="Value"
                      className="w-24 rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                    />
                    
                    <button
                      type="button"
                      onClick={() => removeRule(rule.id, 'exit')}
                      className="text-red-600 hover:text-red-700"
                    >
                      <X size={16} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Risk Management Tab */}
        {activeTab === 'risk' && (
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
                {riskParameters.maxPositionSizeRecommended && (
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    Recommended: ${riskParameters.maxPositionSizeRecommended.toLocaleString()}
                  </p>
                )}
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
              
              {/* RR-Trigger Configuration */}
              <div className="md:col-span-2 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <div className="flex items-center mb-3">
                  <input
                    type="checkbox"
                    checked={form.riskManagement.rrTrigger?.enabled || false}
                    onChange={(e) => setForm({ 
                      ...form, 
                      riskManagement: {
                        ...form.riskManagement,
                        rrTrigger: { 
                          ...form.riskManagement.rrTrigger, 
                          enabled: e.target.checked,
                          profitThreshold: form.riskManagement.rrTrigger?.profitThreshold || 1.5,
                          reductionPercent: form.riskManagement.rrTrigger?.reductionPercent || 50
                        }
                      }
                    })}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label className="ml-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                    Enable RR-Trigger (Risk Reduction for Profitable Trades)
                  </label>
                </div>
                
                {form.riskManagement.rrTrigger?.enabled && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Profit Threshold (R multiple)
                      </label>
                      <input
                        type="number"
                        value={form.riskManagement.rrTrigger?.profitThreshold || 1.5}
                        onChange={(e) => setForm({ 
                          ...form, 
                          riskManagement: {
                            ...form.riskManagement,
                            rrTrigger: { 
                              ...form.riskManagement.rrTrigger, 
                              profitThreshold: parseFloat(e.target.value) 
                            }
                          }
                        })}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                        step="0.1"
                        min="1"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Position Reduction (%)
                      </label>
                      <input
                        type="number"
                        value={form.riskManagement.rrTrigger?.reductionPercent || 50}
                        onChange={(e) => setForm({ 
                          ...form, 
                          riskManagement: {
                            ...form.riskManagement,
                            rrTrigger: { 
                              ...form.riskManagement.rrTrigger, 
                              reductionPercent: parseFloat(e.target.value) 
                            }
                          }
                        })}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                        step="1"
                        min="1"
                        max="100"
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Margin Utilization Display */}
            <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-2">Margin Utilization</h3>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-gray-500 dark:text-gray-400">Available Margin:</span>
                  <span className="ml-2 font-medium text-gray-900 dark:text-white">$75,000</span>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">Used Margin:</span>
                  <span className="ml-2 font-medium text-gray-900 dark:text-white">$25,000</span>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">Utilization:</span>
                  <span className="ml-2 font-medium text-gray-900 dark:text-white">33%</span>
                </div>
              </div>
              <div className="mt-2 w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                <div className="bg-blue-600 h-2 rounded-full" style={{ width: '33%' }}></div>
              </div>
            </div>
          </div>
        )}

        {/* Backtesting Tab */}
        {activeTab === 'backtest' && (
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium text-gray-900 dark:text-white">Backtesting</h2>
              <button
                type="button"
                onClick={handleBacktest}
                disabled={isBacktesting}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center"
              >
                {isBacktesting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Running...
                  </>
                ) : (
                  <>
                    <Play size={16} className="mr-2" />
                    Run Backtest
                  </>
                )}
              </button>
            </div>

            {backtestResult && (
              <div className="space-y-6">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <p className="text-sm text-gray-500 dark:text-gray-400">Total Return</p>
                    <p className={`text-xl font-semibold ${
                      backtestResult.totalReturn > 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {backtestResult.totalReturn > 0 ? '+' : ''}{backtestResult.totalReturn.toFixed(2)}%
                    </p>
                  </div>
                  
                  <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <p className="text-sm text-gray-500 dark:text-gray-400">Sharpe Ratio</p>
                    <p className="text-xl font-semibold text-gray-900 dark:text-white">
                      {backtestResult.sharpeRatio.toFixed(2)}
                    </p>
                  </div>
                  
                  <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <p className="text-sm text-gray-500 dark:text-gray-400">Max Drawdown</p>
                    <p className="text-xl font-semibold text-red-600">
                      -{backtestResult.maxDrawdown.toFixed(2)}%
                    </p>
                  </div>
                  
                  <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <p className="text-sm text-gray-500 dark:text-gray-400">Win Rate</p>
                    <p className="text-xl font-semibold text-gray-900 dark:text-white">
                      {backtestResult.winRate.toFixed(1)}%
                    </p>
                  </div>
                  
                  <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <p className="text-sm text-gray-500 dark:text-gray-400">Total Trades</p>
                    <p className="text-xl font-semibold text-gray-900 dark:text-white">
                      {backtestResult.totalTrades}
                    </p>
                  </div>
                  
                  <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <p className="text-sm text-gray-500 dark:text-gray-400">Profit Factor</p>
                    <p className="text-xl font-semibold text-gray-900 dark:text-white">
                      {backtestResult.profitFactor.toFixed(2)}
                    </p>
                  </div>
                </div>

                {/* Detailed Results */}
                {backtestResult.detailedResults && (
                  <div className="space-y-4">
                    <h3 className="text-md font-medium text-gray-900 dark:text-white">Detailed Results</h3>
                    
                    {/* Trade List */}
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">Recent Trades</h4>
                      <div className="max-h-40 overflow-y-auto">
                        {backtestResult.detailedResults.trades.slice(0, 10).map((trade, index) => (
                          <div key={index} className="flex justify-between items-center py-1 text-sm">
                            <span className="text-gray-600 dark:text-gray-400">{trade.symbol}</span>
                            <span className={trade.pnl > 0 ? 'text-green-600' : 'text-red-600'}>
                              {trade.pnl > 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {!backtestResult && !isBacktesting && (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                Run a backtest to see historical performance metrics and detailed results
              </div>
            )}
          </div>
        )}

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
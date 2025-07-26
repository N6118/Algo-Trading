import { useState, useEffect } from 'react';
import { Shield, Save, RotateCcw, AlertTriangle, TrendingUp, BarChart3, Settings } from 'lucide-react';
import toast from 'react-hot-toast';

interface RiskSettings {
  maxStopLossPerTrade: number;
  maxStopLossTotal: number;
  maxPositionSize: number;
  maxLeverage: number;
  marginBuffer: number;
  riskReductionThreshold: number;
  autoHedgeEnabled: boolean;
  trailingStopEnabled: boolean;
  trailingStopPercent: number;
  correlationThreshold: number;
  concentrationLimit: number;
  volatilityLimit: number;
  drawdownLimit: number;
  dailyLossLimit: number;
  portfolioHeatLimit: number;
}

interface RiskTemplate {
  id: string;
  name: string;
  description: string;
  settings: Partial<RiskSettings>;
  riskLevel: 'conservative' | 'moderate' | 'aggressive';
}

interface AccountInfo {
  accountValue: number;
  buyingPower: number;
  dayTradingBuyingPower: number;
  maintenanceMargin: number;
  availableFunds: number;
}

interface HistoricalRiskData {
  date: string;
  maxDrawdown: number;
  volatility: number;
  sharpeRatio: number;
  var95: number;
}

const RiskSettings = () => {
  const [settings, setSettings] = useState<RiskSettings>({
    maxStopLossPerTrade: 2.0,
    maxStopLossTotal: 10.0,
    maxPositionSize: 25.0,
    maxLeverage: 2.0,
    marginBuffer: 20.0,
    riskReductionThreshold: 15.0,
    autoHedgeEnabled: false,
    trailingStopEnabled: true,
    trailingStopPercent: 3.0,
    correlationThreshold: 0.7,
    concentrationLimit: 30.0,
    volatilityLimit: 25.0,
    drawdownLimit: 20.0,
    dailyLossLimit: 5.0,
    portfolioHeatLimit: 80.0
  });

  const [originalSettings, setOriginalSettings] = useState<RiskSettings>(settings);
  const [templates, setTemplates] = useState<RiskTemplate[]>([]);
  const [accountInfo, setAccountInfo] = useState<AccountInfo | null>(null);
  const [historicalData, setHistoricalData] = useState<HistoricalRiskData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');

  useEffect(() => {
    fetchRiskSettings();
    fetchTemplates();
    fetchAccountInfo();
    fetchHistoricalData();
  }, []);

  useEffect(() => {
    const changed = JSON.stringify(settings) !== JSON.stringify(originalSettings);
    setHasChanges(changed);
  }, [settings, originalSettings]);

  const fetchRiskSettings = async () => {
    try {
      const response = await fetch('/api/risk/settings');
      if (response.ok) {
        const data = await response.json();
        setSettings(data);
        setOriginalSettings(data);
      }
    } catch (err) {
      console.error('Failed to fetch risk settings:', err);
      toast.error('Failed to load risk settings');
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await fetch('/api/risk/settings/templates');
      if (response.ok) {
        const data = await response.json();
        setTemplates(data);
      }
    } catch (err) {
      console.error('Failed to fetch templates:', err);
      // Set mock templates
      setTemplates([
        {
          id: 'conservative',
          name: 'Conservative',
          description: 'Low risk, capital preservation focused',
          riskLevel: 'conservative',
          settings: {
            maxStopLossPerTrade: 1.0,
            maxStopLossTotal: 5.0,
            maxPositionSize: 10.0,
            maxLeverage: 1.5,
            marginBuffer: 30.0,
            riskReductionThreshold: 10.0
          }
        },
        {
          id: 'moderate',
          name: 'Moderate',
          description: 'Balanced risk and return approach',
          riskLevel: 'moderate',
          settings: {
            maxStopLossPerTrade: 2.0,
            maxStopLossTotal: 10.0,
            maxPositionSize: 25.0,
            maxLeverage: 2.0,
            marginBuffer: 20.0,
            riskReductionThreshold: 15.0
          }
        },
        {
          id: 'aggressive',
          name: 'Aggressive',
          description: 'Higher risk for potentially higher returns',
          riskLevel: 'aggressive',
          settings: {
            maxStopLossPerTrade: 5.0,
            maxStopLossTotal: 20.0,
            maxPositionSize: 50.0,
            maxLeverage: 4.0,
            marginBuffer: 10.0,
            riskReductionThreshold: 25.0
          }
        }
      ]);
    }
  };

  const fetchAccountInfo = async () => {
    try {
      const response = await fetch('/api/account/info');
      if (response.ok) {
        const data = await response.json();
        setAccountInfo(data);
      }
    } catch (err) {
      console.error('Failed to fetch account info:', err);
      // Set mock account info
      setAccountInfo({
        accountValue: 150000,
        buyingPower: 300000,
        dayTradingBuyingPower: 600000,
        maintenanceMargin: 45000,
        availableFunds: 105000
      });
    }
  };

  const fetchHistoricalData = async () => {
    try {
      const response = await fetch('/api/risk/historical/analysis');
      if (response.ok) {
        const data = await response.json();
        setHistoricalData(data);
      }
    } catch (err) {
      console.error('Failed to fetch historical data:', err);
      // Set mock historical data
      const mockData = Array.from({ length: 30 }, (_, i) => ({
        date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        maxDrawdown: Math.random() * -20,
        volatility: 15 + Math.random() * 10,
        sharpeRatio: 0.5 + Math.random() * 1.5,
        var95: Math.random() * -10
      }));
      setHistoricalData(mockData);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const response = await fetch('/api/risk/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });

      if (response.ok) {
        setOriginalSettings(settings);
        toast.success('Risk settings saved successfully');
      } else {
        toast.error('Failed to save risk settings');
      }
    } catch (err) {
      console.error('Failed to save settings:', err);
      toast.error('Failed to save risk settings');
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    setSettings(originalSettings);
    setSelectedTemplate('');
    toast.info('Settings reset to last saved values');
  };

  const handleApplyTemplate = async (templateId: string) => {
    try {
      const response = await fetch(`/api/risk/settings/apply-template/${templateId}`, {
        method: 'POST',
      });

      if (response.ok) {
        const template = templates.find(t => t.id === templateId);
        if (template) {
          setSettings(prev => ({ ...prev, ...template.settings }));
          setSelectedTemplate(templateId);
          toast.success(`Applied ${template.name} template`);
        }
      }
    } catch (err) {
      console.error('Failed to apply template:', err);
      toast.error('Failed to apply template');
    }
  };

  const handleInputChange = (field: keyof RiskSettings, value: number | boolean) => {
    setSettings(prev => ({ ...prev, [field]: value }));
  };

  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case 'conservative': return 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200';
      case 'moderate': return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200';
      case 'aggressive': return 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200';
      default: return 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200';
    }
  };

  const calculateRiskMetrics = () => {
    if (!accountInfo) return null;

    const maxTradeRisk = (accountInfo.accountValue * settings.maxStopLossPerTrade) / 100;
    const maxTotalRisk = (accountInfo.accountValue * settings.maxStopLossTotal) / 100;
    const maxPositionValue = (accountInfo.accountValue * settings.maxPositionSize) / 100;

    return {
      maxTradeRisk,
      maxTotalRisk,
      maxPositionValue,
      leverageCapacity: accountInfo.buyingPower * settings.maxLeverage
    };
  };

  const riskMetrics = calculateRiskMetrics();

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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center">
            <Shield className="w-6 h-6 mr-2 text-blue-600" />
            Risk Management Settings
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Configure risk parameters and limits for your trading account
          </p>
        </div>
        <div className="flex items-center space-x-3">
          {hasChanges && (
            <button
              onClick={handleReset}
              className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              <RotateCcw size={16} className="mr-2" />
              Reset
            </button>
          )}
          <button
            onClick={handleSave}
            disabled={!hasChanges || isSaving}
            className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Save size={16} className="mr-2" />
            {isSaving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>

      {/* Risk Templates */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white">Risk Templates</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Quick setup with pre-configured risk parameters
          </p>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {templates.map((template) => (
              <div
                key={template.id}
                className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                  selectedTemplate === template.id
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
                onClick={() => handleApplyTemplate(template.id)}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium text-gray-900 dark:text-white">{template.name}</h3>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getRiskLevelColor(template.riskLevel)}`}>
                    {template.riskLevel}
                  </span>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">{template.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Account Information */}
      {accountInfo && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white">Account Information</h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">Account Value</p>
                <p className="text-xl font-semibold text-gray-900 dark:text-white">
                  ${accountInfo.accountValue.toLocaleString()}
                </p>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">Buying Power</p>
                <p className="text-xl font-semibold text-gray-900 dark:text-white">
                  ${accountInfo.buyingPower.toLocaleString()}
                </p>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">Day Trading BP</p>
                <p className="text-xl font-semibold text-gray-900 dark:text-white">
                  ${accountInfo.dayTradingBuyingPower.toLocaleString()}
                </p>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">Maintenance Margin</p>
                <p className="text-xl font-semibold text-gray-900 dark:text-white">
                  ${accountInfo.maintenanceMargin.toLocaleString()}
                </p>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">Available Funds</p>
                <p className="text-xl font-semibold text-gray-900 dark:text-white">
                  ${accountInfo.availableFunds.toLocaleString()}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Risk Parameters */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Position Size Limits */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white">Position Size Limits</h2>
          </div>
          <div className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Maximum Position Size (% of Portfolio)
              </label>
              <input
                type="number"
                value={settings.maxPositionSize}
                onChange={(e) => handleInputChange('maxPositionSize', parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                min="1"
                max="100"
                step="0.1"
              />
              {riskMetrics && (
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Max position value: ${riskMetrics.maxPositionValue.toLocaleString()}
                </p>
              )}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Maximum Leverage
              </label>
              <input
                type="number"
                value={settings.maxLeverage}
                onChange={(e) => handleInputChange('maxLeverage', parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                min="1"
                max="10"
                step="0.1"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Concentration Limit (% of Portfolio)
              </label>
              <input
                type="number"
                value={settings.concentrationLimit}
                onChange={(e) => handleInputChange('concentrationLimit', parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                min="1"
                max="100"
                step="0.1"
              />
            </div>
          </div>
        </div>

        {/* Stop Loss Parameters */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white">Stop Loss Parameters</h2>
          </div>
          <div className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Maximum Stop Loss Per Trade (%)
              </label>
              <input
                type="number"
                value={settings.maxStopLossPerTrade}
                onChange={(e) => handleInputChange('maxStopLossPerTrade', parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                min="0.1"
                max="20"
                step="0.1"
              />
              {riskMetrics && (
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Max risk per trade: ${riskMetrics.maxTradeRisk.toLocaleString()}
                </p>
              )}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Maximum Total Stop Loss (%)
              </label>
              <input
                type="number"
                value={settings.maxStopLossTotal}
                onChange={(e) => handleInputChange('maxStopLossTotal', parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                min="0.1"
                max="50"
                step="0.1"
              />
              {riskMetrics && (
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Max total risk: ${riskMetrics.maxTotalRisk.toLocaleString()}
                </p>
              )}
            </div>
            
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={settings.trailingStopEnabled}
                onChange={(e) => handleInputChange('trailingStopEnabled', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label className="ml-2 block text-sm text-gray-700 dark:text-gray-300">
                Enable Trailing Stop Loss
              </label>
            </div>
            
            {settings.trailingStopEnabled && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Trailing Stop Percentage (%)
                </label>
                <input
                  type="number"
                  value={settings.trailingStopPercent}
                  onChange={(e) => handleInputChange('trailingStopPercent', parseFloat(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  min="0.1"
                  max="10"
                  step="0.1"
                />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Advanced Risk Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Metrics */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white">Risk Metrics</h2>
          </div>
          <div className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Maximum Drawdown Limit (%)
              </label>
              <input
                type="number"
                value={settings.drawdownLimit}
                onChange={(e) => handleInputChange('drawdownLimit', parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                min="1"
                max="50"
                step="0.1"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Daily Loss Limit (%)
              </label>
              <input
                type="number"
                value={settings.dailyLossLimit}
                onChange={(e) => handleInputChange('dailyLossLimit', parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                min="0.1"
                max="20"
                step="0.1"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Volatility Limit (%)
              </label>
              <input
                type="number"
                value={settings.volatilityLimit}
                onChange={(e) => handleInputChange('volatilityLimit', parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                min="1"
                max="100"
                step="0.1"
              />
            </div>
          </div>
        </div>

        {/* Correlation Settings */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white">Correlation Settings</h2>
          </div>
          <div className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Maximum Correlation Threshold
              </label>
              <input
                type="number"
                value={settings.correlationThreshold}
                onChange={(e) => handleInputChange('correlationThreshold', parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                min="0"
                max="1"
                step="0.01"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Margin Buffer (%)
              </label>
              <input
                type="number"
                value={settings.marginBuffer}
                onChange={(e) => handleInputChange('marginBuffer', parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                min="0"
                max="50"
                step="0.1"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Portfolio Heat Limit (%)
              </label>
              <input
                type="number"
                value={settings.portfolioHeatLimit}
                onChange={(e) => handleInputChange('portfolioHeatLimit', parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                min="1"
                max="100"
                step="0.1"
              />
            </div>
            
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={settings.autoHedgeEnabled}
                onChange={(e) => handleInputChange('autoHedgeEnabled', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label className="ml-2 block text-sm text-gray-700 dark:text-gray-300">
                Enable Auto-Hedging
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* Historical Risk Analysis */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white flex items-center">
            <BarChart3 className="w-5 h-5 mr-2 text-blue-500" />
            Historical Risk Analysis
          </h2>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-sm text-gray-500 dark:text-gray-400">Avg Max Drawdown</p>
              <p className="text-xl font-semibold text-red-600">
                {historicalData.length > 0 
                  ? `${(historicalData.reduce((sum, d) => sum + d.maxDrawdown, 0) / historicalData.length).toFixed(1)}%`
                  : 'N/A'
                }
              </p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-sm text-gray-500 dark:text-gray-400">Avg Volatility</p>
              <p className="text-xl font-semibold text-yellow-600">
                {historicalData.length > 0 
                  ? `${(historicalData.reduce((sum, d) => sum + d.volatility, 0) / historicalData.length).toFixed(1)}%`
                  : 'N/A'
                }
              </p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-sm text-gray-500 dark:text-gray-400">Avg Sharpe Ratio</p>
              <p className="text-xl font-semibold text-blue-600">
                {historicalData.length > 0 
                  ? (historicalData.reduce((sum, d) => sum + d.sharpeRatio, 0) / historicalData.length).toFixed(2)
                  : 'N/A'
                }
              </p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-sm text-gray-500 dark:text-gray-400">Avg VaR (95%)</p>
              <p className="text-xl font-semibold text-purple-600">
                {historicalData.length > 0 
                  ? `${(historicalData.reduce((sum, d) => sum + d.var95, 0) / historicalData.length).toFixed(1)}%`
                  : 'N/A'
                }
              </p>
            </div>
          </div>
          
          {hasChanges && (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
              <div className="flex">
                <AlertTriangle className="h-5 w-5 text-yellow-400" />
                <div className="ml-3">
                  <p className="text-sm text-yellow-700 dark:text-yellow-200">
                    You have unsaved changes. Click "Save Settings" to apply your risk parameter modifications.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RiskSettings;
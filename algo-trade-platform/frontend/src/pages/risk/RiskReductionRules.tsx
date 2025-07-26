import { useState, useEffect } from 'react';
import { AlertTriangle, Plus, Save, Trash2, Edit2, Play, Pause, BarChart3, TrendingDown } from 'lucide-react';
import toast from 'react-hot-toast';
import { RiskReductionRule } from '../../types/risk';

interface RiskReductionTemplate {
  id: string;
  name: string;
  description: string;
  triggerType: string;
  triggerValue: number;
  action: string;
  quantity: string;
}

interface RiskReductionHistory {
  id: string;
  ruleId: string;
  ruleName: string;
  timestamp: string;
  triggerValue: number;
  actualValue: number;
  action: string;
  quantity: number;
  symbol: string;
  success: boolean;
  message: string;
}

interface QuantityCalculation {
  percentage: number;
  shares: number;
  value: number;
  remainingPosition: number;
}

const RiskReductionRules = () => {
  const [rules, setRules] = useState<RiskReductionRule[]>([]);
  const [templates, setTemplates] = useState<RiskReductionTemplate[]>([]);
  const [history, setHistory] = useState<RiskReductionHistory[]>([]);
  const [newRule, setNewRule] = useState<Partial<RiskReductionRule>>({
    name: '',
    triggerType: 'price',
    triggerValue: 0,
    action: 'reduce',
    quantity: '50%',
    enabled: true
  });
  const [editingRule, setEditingRule] = useState<RiskReductionRule | null>(null);
  const [showTemplates, setShowTemplates] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [quantityCalculation, setQuantityCalculation] = useState<QuantityCalculation | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const triggerTypes = [
    { value: 'price', label: 'Price Level', description: 'Trigger when price reaches a specific level' },
    { value: 'drawdown', label: 'Drawdown', description: 'Trigger when portfolio drawdown exceeds threshold' },
    { value: 'volatility', label: 'Volatility', description: 'Trigger when volatility exceeds threshold' },
    { value: 'time', label: 'Time-based', description: 'Trigger at specific time or duration' },
    { value: 'correlation', label: 'Correlation', description: 'Trigger when correlation changes' },
    { value: 'margin', label: 'Margin Utilization', description: 'Trigger when margin usage exceeds limit' },
    { value: 'pnl', label: 'P&L Threshold', description: 'Trigger when P&L reaches threshold' }
  ];

  const actionTypes = [
    { value: 'reduce', label: 'Reduce Position', description: 'Reduce position size by specified amount' },
    { value: 'close', label: 'Close Position', description: 'Close entire position' },
    { value: 'hedge', label: 'Add Hedge', description: 'Add hedging position' },
    { value: 'stop', label: 'Stop Strategy', description: 'Stop the strategy completely' },
    { value: 'alert', label: 'Alert Only', description: 'Send alert without taking action' }
  ];

  useEffect(() => {
    fetchRules();
    fetchTemplates();
    fetchHistory();
  }, []);

  const fetchRules = async () => {
    try {
      const response = await fetch('/api/risk/reduction/rules');
      if (response.ok) {
        const data = await response.json();
        setRules(data);
      }
    } catch (err) {
      console.error('Failed to fetch rules:', err);
      // Set mock data
      setRules([
        {
          id: '1',
          name: 'Emergency Stop Loss',
          triggerType: 'drawdown',
          triggerValue: 15,
          action: 'close',
          quantity: '100%',
          enabled: true
        },
        {
          id: '2',
          name: 'Volatility Hedge',
          triggerType: 'volatility',
          triggerValue: 30,
          action: 'hedge',
          quantity: '25%',
          enabled: true
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await fetch('/api/risk/reduction/templates');
      if (response.ok) {
        const data = await response.json();
        setTemplates(data);
      }
    } catch (err) {
      console.error('Failed to fetch templates:', err);
      // Set mock templates
      setTemplates([
        {
          id: '1',
          name: 'Conservative Stop Loss',
          description: 'Close position when drawdown exceeds 10%',
          triggerType: 'drawdown',
          triggerValue: 10,
          action: 'close',
          quantity: '100%'
        },
        {
          id: '2',
          name: 'Partial Profit Taking',
          description: 'Reduce position by 50% when profit reaches 20%',
          triggerType: 'pnl',
          triggerValue: 20,
          action: 'reduce',
          quantity: '50%'
        },
        {
          id: '3',
          name: 'Volatility Protection',
          description: 'Add hedge when volatility exceeds 25%',
          triggerType: 'volatility',
          triggerValue: 25,
          action: 'hedge',
          quantity: '30%'
        }
      ]);
    }
  };

  const fetchHistory = async () => {
    try {
      const response = await fetch('/api/risk/reduction/history');
      if (response.ok) {
        const data = await response.json();
        setHistory(data);
      }
    } catch (err) {
      console.error('Failed to fetch history:', err);
      // Set mock history
      setHistory([
        {
          id: '1',
          ruleId: '1',
          ruleName: 'Emergency Stop Loss',
          timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          triggerValue: 15,
          actualValue: 16.2,
          action: 'close',
          quantity: 100,
          symbol: 'AAPL',
          success: true,
          message: 'Position closed successfully'
        },
        {
          id: '2',
          ruleId: '2',
          ruleName: 'Volatility Hedge',
          timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
          triggerValue: 30,
          actualValue: 32.1,
          action: 'hedge',
          quantity: 25,
          symbol: 'SPY',
          success: true,
          message: 'Hedge position added'
        }
      ]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/risk/reduction/rules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newRule),
      });
      
      if (response.ok) {
        const data = await response.json();
        setRules([...rules, data]);
        setNewRule({
          name: '',
          triggerType: 'price',
          triggerValue: 0,
          action: 'reduce',
          quantity: '50%',
          enabled: true
        });
        toast.success('Rule created successfully');
      }
    } catch (err) {
      console.error('Failed to create rule:', err);
      toast.error('Failed to create rule');
    }
  };

  const handleUpdateRule = async (rule: RiskReductionRule) => {
    try {
      const response = await fetch(`/api/risk/reduction/rules/${rule.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(rule),
      });
      
      if (response.ok) {
        setRules(rules.map(r => r.id === rule.id ? rule : r));
        setEditingRule(null);
        toast.success('Rule updated successfully');
      }
    } catch (err) {
      console.error('Failed to update rule:', err);
      toast.error('Failed to update rule');
    }
  };

  const handleDeleteRule = async (id: string) => {
    if (!confirm('Are you sure you want to delete this rule?')) return;

    try {
      const response = await fetch(`/api/risk/reduction/rules/${id}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        setRules(rules.filter(rule => rule.id !== id));
        toast.success('Rule deleted successfully');
      }
    } catch (err) {
      console.error('Failed to delete rule:', err);
      toast.error('Failed to delete rule');
    }
  };

  const handleTestRule = async (id: string) => {
    try {
      const response = await fetch('/api/risk/reduction/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ruleId: id }),
      });
      
      if (response.ok) {
        const data = await response.json();
        toast.success(`Rule test successful: ${data.message}`);
      }
    } catch (err) {
      console.error('Failed to test rule:', err);
      toast.error('Failed to test rule');
    }
  };

  const handleToggleRule = async (id: string, enabled: boolean) => {
    try {
      const rule = rules.find(r => r.id === id);
      if (rule) {
        const updatedRule = { ...rule, enabled };
        await handleUpdateRule(updatedRule);
      }
    } catch (err) {
      console.error('Failed to toggle rule:', err);
      toast.error('Failed to toggle rule');
    }
  };

  const handleApplyTemplate = (template: RiskReductionTemplate) => {
    setNewRule({
      name: template.name,
      triggerType: template.triggerType,
      triggerValue: template.triggerValue,
      action: template.action,
      quantity: template.quantity,
      enabled: true
    });
    setShowTemplates(false);
    toast.success(`Applied template: ${template.name}`);
  };

  const calculateQuantity = async (quantity: string, symbol: string = 'AAPL') => {
    try {
      const response = await fetch('/api/risk/reduction/quantity/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quantity, symbol }),
      });
      
      if (response.ok) {
        const data = await response.json();
        setQuantityCalculation(data);
      }
    } catch (err) {
      console.error('Failed to calculate quantity:', err);
      // Mock calculation
      const isPercentage = quantity.includes('%');
      const value = parseFloat(quantity.replace('%', ''));
      
      if (isPercentage) {
        setQuantityCalculation({
          percentage: value,
          shares: Math.floor((value / 100) * 100), // Assuming 100 shares
          value: (value / 100) * 18500, // Assuming $185 per share
          remainingPosition: 100 - value
        });
      } else {
        setQuantityCalculation({
          percentage: (value / 100) * 100,
          shares: value,
          value: value * 185,
          remainingPosition: 100 - value
        });
      }
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
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Risk Reduction Rules</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Configure automated risk reduction triggers and actions
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowTemplates(!showTemplates)}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            Templates
          </button>
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            History
          </button>
          <button
            onClick={() => document.getElementById('new-rule-form')?.scrollIntoView({ behavior: 'smooth' })}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center"
          >
            <Plus size={16} className="mr-2" />
            New Rule
          </button>
        </div>
      </div>

      {/* Templates Modal */}
      {showTemplates && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white">Rule Templates</h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {templates.map((template) => (
                <div
                  key={template.id}
                  className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg cursor-pointer hover:border-blue-500 transition-colors"
                  onClick={() => handleApplyTemplate(template)}
                >
                  <h3 className="font-medium text-gray-900 dark:text-white mb-2">{template.name}</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">{template.description}</p>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    <div>Trigger: {template.triggerType} @ {template.triggerValue}</div>
                    <div>Action: {template.action} {template.quantity}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* History Modal */}
      {showHistory && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white flex items-center">
              <BarChart3 className="w-5 h-5 mr-2 text-blue-500" />
              Risk Reduction History
            </h2>
          </div>
          <div className="p-6">
            <div className="space-y-3">
              {history.map((item) => (
                <div key={item.id} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div>
                    <div className="font-medium text-gray-900 dark:text-white">{item.ruleName}</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      {item.symbol} • {item.action} {item.quantity}% • {new Date(item.timestamp).toLocaleString()}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      Trigger: {item.triggerValue} | Actual: {item.actualValue}
                    </div>
                  </div>
                  <div className="flex items-center">
                    {item.success ? (
                      <span className="px-2 py-1 text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200 rounded-full">
                        Success
                      </span>
                    ) : (
                      <span className="px-2 py-1 text-xs font-medium bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200 rounded-full">
                        Failed
                      </span>
                    )}
                  </div>
                </div>
              ))}
              {history.length === 0 && (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  No risk reduction actions have been executed yet
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Existing Rules */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white">Active Rules</h2>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            {rules.map((rule) => (
              <div key={rule.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                {editingRule?.id === rule.id ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Rule Name
                        </label>
                        <input
                          type="text"
                          value={editingRule.name}
                          onChange={(e) => setEditingRule({ ...editingRule, name: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Trigger Type
                        </label>
                        <select
                          value={editingRule.triggerType}
                          onChange={(e) => setEditingRule({ ...editingRule, triggerType: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                        >
                          {triggerTypes.map((type) => (
                            <option key={type.value} value={type.value}>{type.label}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Trigger Value
                        </label>
                        <input
                          type="number"
                          value={editingRule.triggerValue}
                          onChange={(e) => setEditingRule({ ...editingRule, triggerValue: parseFloat(e.target.value) })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Action
                        </label>
                        <select
                          value={editingRule.action}
                          onChange={(e) => setEditingRule({ ...editingRule, action: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                        >
                          {actionTypes.map((action) => (
                            <option key={action.value} value={action.value}>{action.label}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                    <div className="flex justify-end space-x-3">
                      <button
                        onClick={() => setEditingRule(null)}
                        className="px-3 py-1 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => handleUpdateRule(editingRule)}
                        className="px-3 py-1 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 flex items-center"
                      >
                        <Save size={14} className="mr-1" />
                        Save
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <button
                        onClick={() => handleToggleRule(rule.id, !rule.enabled)}
                        className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                          rule.enabled ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
                        }`}
                      >
                        <span
                          className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                            rule.enabled ? 'translate-x-5' : 'translate-x-0'
                          }`}
                        />
                      </button>
                      <div>
                        <h3 className="text-sm font-medium text-gray-900 dark:text-white">{rule.name}</h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {triggerTypes.find(t => t.value === rule.triggerType)?.label} at {rule.triggerValue} → {actionTypes.find(a => a.value === rule.action)?.label} {rule.quantity}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleTestRule(rule.id)}
                        className="px-3 py-1 text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400"
                      >
                        Test
                      </button>
                      <button
                        onClick={() => setEditingRule(rule)}
                        className="text-gray-400 hover:text-gray-500 dark:text-gray-500 dark:hover:text-gray-400"
                      >
                        <Edit2 size={16} />
                      </button>
                      <button
                        onClick={() => handleDeleteRule(rule.id)}
                        className="text-red-600 hover:text-red-700 dark:text-red-400"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
            {rules.length === 0 && (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                No risk reduction rules configured. Create your first rule below.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* New Rule Form */}
      <div id="new-rule-form" className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white">Create New Rule</h2>
        </div>
        <div className="p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Rule Name
                </label>
                <input
                  type="text"
                  value={newRule.name}
                  onChange={(e) => setNewRule({ ...newRule, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="e.g., Emergency Stop Loss"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Trigger Type
                </label>
                <select
                  value={newRule.triggerType}
                  onChange={(e) => setNewRule({ ...newRule, triggerType: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  {triggerTypes.map((type) => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {triggerTypes.find(t => t.value === newRule.triggerType)?.description}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Trigger Value
                </label>
                <input
                  type="number"
                  value={newRule.triggerValue}
                  onChange={(e) => setNewRule({ ...newRule, triggerValue: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  step="0.01"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Action
                </label>
                <select
                  value={newRule.action}
                  onChange={(e) => setNewRule({ ...newRule, action: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  {actionTypes.map((action) => (
                    <option key={action.value} value={action.value}>{action.label}</option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {actionTypes.find(a => a.value === newRule.action)?.description}
                </p>
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Quantity
                </label>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={newRule.quantity}
                    onChange={(e) => setNewRule({ ...newRule, quantity: e.target.value })}
                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    placeholder="e.g., 50% or 100"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => calculateQuantity(newRule.quantity || '50%')}
                    className="px-3 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400"
                  >
                    Calculate
                  </button>
                </div>
                {quantityCalculation && (
                  <div className="mt-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-md">
                    <div className="text-sm text-blue-800 dark:text-blue-200">
                      <div>Shares: {quantityCalculation.shares}</div>
                      <div>Value: ${quantityCalculation.value.toLocaleString()}</div>
                      <div>Remaining: {quantityCalculation.remainingPosition}%</div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                checked={newRule.enabled}
                onChange={(e) => setNewRule({ ...newRule, enabled: e.target.checked })}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label className="ml-2 block text-sm text-gray-700 dark:text-gray-300">
                Enable rule immediately
              </label>
            </div>

            <div className="bg-yellow-50 dark:bg-yellow-900/20 border-l-4 border-yellow-400 p-4">
              <div className="flex">
                <AlertTriangle className="h-5 w-5 text-yellow-400" />
                <div className="ml-3">
                  <p className="text-sm text-yellow-700 dark:text-yellow-200">
                    Rules will be executed automatically when conditions are met. Please review carefully before enabling.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex justify-end">
              <button
                type="submit"
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 flex items-center"
              >
                <Save size={16} className="mr-2" />
                Create Rule
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default RiskReductionRules;
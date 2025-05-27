import { useState, useEffect } from 'react';
import { AlertTriangle, Plus, Save, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { RiskReductionRule } from '../../types/risk';

const RiskReductionRules = () => {
  const [rules, setRules] = useState<RiskReductionRule[]>([]);
  const [newRule, setNewRule] = useState<Partial<RiskReductionRule>>({
    name: '',
    triggerType: 'price',
    triggerValue: 0,
    action: 'reduce',
    quantity: '50%',
    enabled: true
  });

  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = async () => {
    try {
      const response = await fetch('/api/risk/reduction/rules');
      const data = await response.json();
      setRules(data);
    } catch (err) {
      console.error('Failed to fetch rules:', err);
      toast.error('Failed to load risk reduction rules');
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
    } catch (err) {
      console.error('Failed to create rule:', err);
      toast.error('Failed to create rule');
    }
  };

  const handleDeleteRule = async (id: string) => {
    try {
      await fetch(`/api/risk/reduction/rules/${id}`, {
        method: 'DELETE',
      });
      setRules(rules.filter(rule => rule.id !== id));
      toast.success('Rule deleted successfully');
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
      const data = await response.json();
      toast.success(`Rule test successful: ${data.message}`);
    } catch (err) {
      console.error('Failed to test rule:', err);
      toast.error('Failed to test rule');
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Risk Reduction Rules</h1>
        <button
          onClick={() => document.getElementById('new-rule-form')?.scrollIntoView({ behavior: 'smooth' })}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center"
        >
          <Plus size={16} className="mr-2" />
          New Rule
        </button>
      </div>

      {/* Existing Rules */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 mb-6">
        <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Active Rules</h2>
        <div className="space-y-4">
          {rules.map((rule) => (
            <div key={rule.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-gray-900 dark:text-white">{rule.name}</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {rule.triggerType} trigger at {rule.triggerValue} - {rule.action} {rule.quantity}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleTestRule(rule.id)}
                    className="px-3 py-1 text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400"
                  >
                    Test
                  </button>
                  <button
                    onClick={() => handleDeleteRule(rule.id)}
                    className="text-red-600 hover:text-red-700 dark:text-red-400"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* New Rule Form */}
      <div id="new-rule-form" className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Create New Rule</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Rule Name
            </label>
            <input
              type="text"
              value={newRule.name}
              onChange={(e) => setNewRule({ ...newRule, name: e.target.value })}
              className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
              required
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Trigger Type
              </label>
              <select
                value={newRule.triggerType}
                onChange={(e) => setNewRule({ ...newRule, triggerType: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
              >
                <option value="price">Price Level</option>
                <option value="drawdown">Drawdown</option>
                <option value="volatility">Volatility</option>
                <option value="time">Time-based</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Trigger Value
              </label>
              <input
                type="number"
                value={newRule.triggerValue}
                onChange={(e) => setNewRule({ ...newRule, triggerValue: parseFloat(e.target.value) })}
                className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Action
              </label>
              <select
                value={newRule.action}
                onChange={(e) => setNewRule({ ...newRule, action: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
              >
                <option value="reduce">Reduce Position</option>
                <option value="close">Close Position</option>
                <option value="hedge">Add Hedge</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Quantity
              </label>
              <input
                type="text"
                value={newRule.quantity}
                onChange={(e) => setNewRule({ ...newRule, quantity: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                placeholder="e.g., 50% or 100"
                required
              />
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
                  Rules will be executed automatically when conditions are met. Please review carefully.
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
  );
};

export default RiskReductionRules;
import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { TrendingUp, ArrowUp, ArrowDown } from 'lucide-react';
import DashboardCard from '../../components/common/DashboardCard';
import { formatCurrency } from '../../utils/formatters';

const Performance = () => {
  // Sample performance data
  const performanceData = [
    { date: '2024-01', value: 100000 },
    { date: '2024-02', value: 105000 },
    { date: '2024-03', value: 108000 },
    { date: '2024-04', value: 112000 },
    { date: '2024-05', value: 115000 },
  ];

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Performance Analytics</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <DashboardCard
          title="Total Return"
          value="+15.00%"
          trend="up"
          icon={<TrendingUp className="text-blue-500" />}
        />
        <DashboardCard
          title="Winning Trades"
          value="68%"
          trend="up"
          icon={<ArrowUp className="text-green-500" />}
        />
        <DashboardCard
          title="Average Return"
          value="+2.3%"
          trend="up"
          icon={<TrendingUp className="text-blue-500" />}
        />
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-medium mb-4">Portfolio Performance</h2>
        <div className="h-[400px]">
          <LineChart
            width={800}
            height={350}
            data={performanceData}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="value" stroke="#2563eb" name="Portfolio Value" />
          </LineChart>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-medium mb-4">Performance Metrics</h2>
          <div className="space-y-4">
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Sharpe Ratio</span>
              <span className="font-medium">1.8</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Max Drawdown</span>
              <span className="font-medium text-red-600">-8.5%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Profit Factor</span>
              <span className="font-medium">2.1</span>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-medium mb-4">Strategy Performance</h2>
          <div className="space-y-4">
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Best Strategy</span>
              <span className="font-medium text-green-600">Momentum (+24.5%)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Worst Strategy</span>
              <span className="font-medium text-red-600">Mean Reversion (-5.2%)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Performance;
import React from 'react';
import { useParams } from 'react-router-dom';
import DashboardCard from '../../components/common/DashboardCard';
import PerformanceChart from '../../components/charts/PerformanceChart';

const StrategyDashboard: React.FC = () => {
  const { id } = useParams();

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Strategy Dashboard</h1>
        <span className="text-sm text-gray-500 dark:text-gray-400">Strategy ID: {id}</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <DashboardCard
          title="Total Returns"
          value="24.5%"
          trend="up"
          trendValue="3.2%"
          description="Past 30 days"
        />
        <DashboardCard
          title="Win Rate"
          value="68%"
          trend="up"
          trendValue="5%"
          description="Based on last 50 trades"
        />
        <DashboardCard
          title="Active Positions"
          value="3"
          trend="neutral"
          description="Currently open trades"
        />
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Performance History</h2>
        <div className="h-[400px]">
          <PerformanceChart timeRange="1m" />
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Strategy Statistics</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <p className="text-sm text-gray-500 dark:text-gray-400">Sharpe Ratio</p>
            <p className="text-xl font-semibold text-gray-900 dark:text-white">1.8</p>
          </div>
          <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <p className="text-sm text-gray-500 dark:text-gray-400">Max Drawdown</p>
            <p className="text-xl font-semibold text-gray-900 dark:text-white">-12.3%</p>
          </div>
          <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <p className="text-sm text-gray-500 dark:text-gray-400">Avg Trade Duration</p>
            <p className="text-xl font-semibold text-gray-900 dark:text-white">3.2 days</p>
          </div>
          <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <p className="text-sm text-gray-500 dark:text-gray-400">Total Trades</p>
            <p className="text-xl font-semibold text-gray-900 dark:text-white">156</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StrategyDashboard;
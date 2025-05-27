import React from 'react';
import { Wallet, DollarSign, PieChart, Settings } from 'lucide-react';
import DashboardCard from '../../components/common/DashboardCard';
import { formatCurrency } from '../../utils/formatters';

const Accounts = () => {
  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Account Management</h1>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <DashboardCard
          title="Account Balance"
          value={formatCurrency(125000)}
          change="+2.5%"
          trend="up"
          icon={<Wallet className="text-blue-500" />}
        />
        <DashboardCard
          title="Available Margin"
          value={formatCurrency(75000)}
          change="-5.2%"
          trend="down"
          icon={<DollarSign className="text-blue-500" />}
        />
        <DashboardCard
          title="Buying Power"
          value={formatCurrency(250000)}
          icon={<PieChart className="text-blue-500" />}
        />
        <DashboardCard
          title="Day Trades Available"
          value="3"
          icon={<Settings className="text-blue-500" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-medium mb-4">Account Details</h2>
          <div className="space-y-4">
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Account Type</span>
              <span className="font-medium">Margin</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Pattern Day Trader Status</span>
              <span className="font-medium">Eligible</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Margin Requirement</span>
              <span className="font-medium">25%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Account Currency</span>
              <span className="font-medium">USD</span>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-medium mb-4">Connected Exchanges</h2>
          <div className="space-y-4">
            {[
              { name: 'Interactive Brokers', status: 'Connected', lastSync: '2 mins ago' },
              { name: 'TD Ameritrade', status: 'Connected', lastSync: '5 mins ago' },
              { name: 'E*TRADE', status: 'Disconnected', lastSync: 'N/A' },
            ].map((exchange) => (
              <div key={exchange.name} className="flex items-center justify-between">
                <div>
                  <div className="font-medium">{exchange.name}</div>
                  <div className="text-sm text-gray-500">Last sync: {exchange.lastSync}</div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  exchange.status === 'Connected'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {exchange.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-medium mb-4">Recent Transactions</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead>
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {[
                { date: '2024-03-15', type: 'Deposit', description: 'ACH Transfer', amount: 10000 },
                { date: '2024-03-14', type: 'Fee', description: 'Commission', amount: -7.95 },
                { date: '2024-03-13', type: 'Withdrawal', description: 'Wire Transfer', amount: -5000 },
              ].map((transaction, index) => (
                <tr key={index}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">{transaction.date}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">{transaction.type}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">{transaction.description}</td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm text-right ${
                    transaction.amount >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {formatCurrency(transaction.amount)}
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

export default Accounts;
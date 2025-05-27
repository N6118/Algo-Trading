import React from 'react';
import { BarChart2, TrendingUp, TrendingDown, Search } from 'lucide-react';
import DashboardCard from '../../components/common/DashboardCard';

const Markets = () => {
  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Markets</h1>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            placeholder="Search markets..."
            className="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <DashboardCard
          title="S&P 500"
          value="4,185.25"
          change="+1.25%"
          trend="up"
          icon={<BarChart2 className="text-blue-500" />}
        />
        <DashboardCard
          title="NASDAQ"
          value="13,245.75"
          change="+0.85%"
          trend="up"
          icon={<BarChart2 className="text-blue-500" />}
        />
        <DashboardCard
          title="VIX"
          value="18.45"
          change="-2.30%"
          trend="down"
          icon={<BarChart2 className="text-blue-500" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-medium mb-4">Market Movers</h2>
          <div className="space-y-4">
            {[
              { symbol: 'AAPL', name: 'Apple Inc.', change: '+2.5%', price: '175.25' },
              { symbol: 'MSFT', name: 'Microsoft Corp.', change: '+1.8%', price: '285.45' },
              { symbol: 'GOOGL', name: 'Alphabet Inc.', change: '-0.5%', price: '2,450.75' },
            ].map((stock) => (
              <div key={stock.symbol} className="flex items-center justify-between">
                <div>
                  <div className="font-medium">{stock.symbol}</div>
                  <div className="text-sm text-gray-500">{stock.name}</div>
                </div>
                <div className="flex items-center space-x-4">
                  <span className="font-medium">${stock.price}</span>
                  <span className={stock.change.startsWith('+') ? 'text-green-600' : 'text-red-600'}>
                    {stock.change}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-medium mb-4">Market Sectors</h2>
          <div className="space-y-4">
            {[
              { name: 'Technology', change: '+1.8%', trend: 'up' },
              { name: 'Healthcare', change: '-0.5%', trend: 'down' },
              { name: 'Financials', change: '+1.2%', trend: 'up' },
            ].map((sector) => (
              <div key={sector.name} className="flex items-center justify-between">
                <span className="font-medium">{sector.name}</span>
                <div className="flex items-center">
                  {sector.trend === 'up' ? (
                    <TrendingUp size={16} className="text-green-600 mr-2" />
                  ) : (
                    <TrendingDown size={16} className="text-red-600 mr-2" />
                  )}
                  <span className={sector.change.startsWith('+') ? 'text-green-600' : 'text-red-600'}>
                    {sector.change}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Markets;
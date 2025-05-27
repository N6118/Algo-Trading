import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { ActiveTradesTable } from '../../components/trade/ActiveTradesTable';
import { useTradingData } from '../../context/TradingDataContext';

const ActiveTrades = () => {
  const { activeTrades } = useTradingData();
  
  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Active Trades</h1>
        <Link
          to="/trades/analysis"
          className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium"
        >
          <Plus size={16} className="mr-2" />
          New Trade Analysis
        </Link>
      </div>
      
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
        <div className="p-6">
          <ActiveTradesTable trades={activeTrades} />
        </div>
      </div>
    </div>
  );
};

export default ActiveTrades;
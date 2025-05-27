import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { AlertTriangle, TrendingDown, TrendingUp } from 'lucide-react';

const RiskDashboard: React.FC = () => {
  // Sample data for the risk metrics chart
  const riskData = [
    { date: '2023-01', var: 2.5, cvar: 3.2, drawdown: 1.8 },
    { date: '2023-02', var: 2.8, cvar: 3.5, drawdown: 2.1 },
    { date: '2023-03', var: 2.3, cvar: 3.0, drawdown: 1.5 },
    { date: '2023-04', var: 2.9, cvar: 3.7, drawdown: 2.3 },
    { date: '2023-05', var: 2.6, cvar: 3.3, drawdown: 1.9 },
  ];

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Risk Dashboard</h1>
      
      {/* Risk Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600">Value at Risk (VaR)</p>
              <p className="text-2xl font-bold">2.6%</p>
            </div>
            <AlertTriangle className="text-yellow-500 h-8 w-8" />
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600">Maximum Drawdown</p>
              <p className="text-2xl font-bold">-4.8%</p>
            </div>
            <TrendingDown className="text-red-500 h-8 w-8" />
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600">Risk-Adjusted Return</p>
              <p className="text-2xl font-bold">1.2</p>
            </div>
            <TrendingUp className="text-green-500 h-8 w-8" />
          </div>
        </div>
      </div>
      
      {/* Risk Metrics Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Risk Metrics Over Time</h2>
        <div className="h-[400px]">
          <LineChart
            width={800}
            height={350}
            data={riskData}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="var" stroke="#8884d8" name="VaR" />
            <Line type="monotone" dataKey="cvar" stroke="#82ca9d" name="CVaR" />
            <Line type="monotone" dataKey="drawdown" stroke="#ff7300" name="Drawdown" />
          </LineChart>
        </div>
      </div>
    </div>
  );
};

export default RiskDashboard;
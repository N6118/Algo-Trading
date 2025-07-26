import React, { useState, useEffect } from 'react';
import { Activity, BarChart3, Clock, DollarSign, TrendingUp, TrendingDown, Volume2 } from 'lucide-react';
import { useWebSocket } from '../../hooks/useWebSocket';
import { formatCurrency, formatNumber, formatPercentage } from '../../utils/formatters';

interface MarketDataPanelProps {
  symbol: string;
  includePrePost?: boolean;
  includeVolume?: boolean;
  includeFundamentals?: boolean;
  includeOptions?: boolean;
  includeDepth?: boolean;
}

interface MarketData {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  avgVolume: number;
  marketCap?: number;
  peRatio?: number;
  dividend?: number;
  high52Week?: number;
  low52Week?: number;
  marketStatus: 'OPEN' | 'CLOSED' | 'PRE_MARKET' | 'POST_MARKET';
  lastUpdate: string;
}

interface OptionChain {
  expirationDate: string;
  calls: OptionContract[];
  puts: OptionContract[];
}

interface OptionContract {
  strike: number;
  bid: number;
  ask: number;
  volume: number;
  openInterest: number;
  impliedVolatility: number;
}

interface MarketDepth {
  bids: { price: number; size: number }[];
  asks: { price: number; size: number }[];
}

const MarketDataPanel: React.FC<MarketDataPanelProps> = ({
  symbol,
  includePrePost = false,
  includeVolume = true,
  includeFundamentals = false,
  includeOptions = false,
  includeDepth = false
}) => {
  const [marketData, setMarketData] = useState<MarketData | null>(null);
  const [optionChain, setOptionChain] = useState<OptionChain[]>([]);
  const [marketDepth, setMarketDepth] = useState<MarketDepth | null>(null);
  const [corporateActions, setCorporateActions] = useState<any[]>([]);

  // WebSocket connection for real-time data
  const { isConnected, sendMessage } = useWebSocket(
    `ws://localhost:8080/api/ws/market/data/${symbol}`,
    {
      onMessage: (data) => {
        if (data.type === 'price_update') {
          setMarketData(prev => prev ? { ...prev, ...data.data } : data.data);
        } else if (data.type === 'depth_update') {
          setMarketDepth(data.data);
        }
      },
      onOpen: () => {
        // Subscribe to specific data types
        sendMessage({
          action: 'subscribe',
          types: [
            'price',
            includeVolume && 'volume',
            includePrePost && 'extended_hours',
            includeDepth && 'depth'
          ].filter(Boolean)
        });
      }
    }
  );

  useEffect(() => {
    fetchMarketData();
    if (includeOptions) fetchOptionChain();
    if (includeFundamentals) fetchCorporateActions();
  }, [symbol]);

  const fetchMarketData = async () => {
    try {
      const response = await fetch(`/api/market/data/${symbol}`);
      if (response.ok) {
        const data = await response.json();
        setMarketData(data);
      }
    } catch (err) {
      console.error('Failed to fetch market data:', err);
      // Mock data
      setMarketData({
        symbol,
        price: 150.25,
        change: 2.15,
        changePercent: 1.45,
        volume: 1250000,
        avgVolume: 1800000,
        marketCap: 2500000000,
        peRatio: 28.5,
        dividend: 0.88,
        high52Week: 180.50,
        low52Week: 120.30,
        marketStatus: 'OPEN',
        lastUpdate: new Date().toISOString()
      });
    }
  };

  const fetchOptionChain = async () => {
    try {
      const response = await fetch(`/api/market/options/${symbol}`);
      if (response.ok) {
        const data = await response.json();
        setOptionChain(data);
      }
    } catch (err) {
      console.error('Failed to fetch option chain:', err);
    }
  };

  const fetchCorporateActions = async () => {
    try {
      const response = await fetch(`/api/market/corporate-actions/${symbol}`);
      if (response.ok) {
        const data = await response.json();
        setCorporateActions(data);
      }
    } catch (err) {
      console.error('Failed to fetch corporate actions:', err);
    }
  };

  const getMarketStatusColor = (status: string) => {
    switch (status) {
      case 'OPEN': return 'text-green-600 dark:text-green-400';
      case 'CLOSED': return 'text-red-600 dark:text-red-400';
      case 'PRE_MARKET':
      case 'POST_MARKET': return 'text-yellow-600 dark:text-yellow-400';
      default: return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getPriceChangeColor = (change: number) => {
    if (change > 0) return 'text-green-600 dark:text-green-400';
    if (change < 0) return 'text-red-600 dark:text-red-400';
    return 'text-gray-600 dark:text-gray-400';
  };

  if (!marketData) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-4"></div>
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-2"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Main Price Panel */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mr-3">{symbol}</h2>
            <div className={`px-2 py-1 rounded-full text-xs font-medium ${
              marketData.marketStatus === 'OPEN' 
                ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
                : 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200'
            }`}>
              {marketData.marketStatus.replace('_', ' ')}
            </div>
          </div>
          <div className="flex items-center">
            <Activity className={`w-4 h-4 mr-2 ${isConnected ? 'text-green-500' : 'text-red-500'}`} />
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {isConnected ? 'Live' : 'Disconnected'}
            </span>
          </div>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div className="text-3xl font-bold text-gray-900 dark:text-white">
              {formatCurrency(marketData.price)}
            </div>
            <div className={`flex items-center text-sm ${getPriceChangeColor(marketData.change)}`}>
              {marketData.change > 0 ? <TrendingUp size={16} className="mr-1" /> : <TrendingDown size={16} className="mr-1" />}
              {formatCurrency(marketData.change)} ({formatPercentage(marketData.changePercent)})
            </div>
          </div>
          
          {includeVolume && (
            <div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Volume</div>
              <div className="text-lg font-semibold text-gray-900 dark:text-white">
                {formatNumber(marketData.volume)}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                Avg: {formatNumber(marketData.avgVolume)}
              </div>
            </div>
          )}
          
          <div>
            <div className="text-sm text-gray-500 dark:text-gray-400">52W Range</div>
            <div className="text-sm text-gray-900 dark:text-white">
              {formatCurrency(marketData.low52Week || 0)} - {formatCurrency(marketData.high52Week || 0)}
            </div>
          </div>
          
          <div>
            <div className="text-sm text-gray-500 dark:text-gray-400">Last Update</div>
            <div className="text-sm text-gray-900 dark:text-white">
              {new Date(marketData.lastUpdate).toLocaleTimeString()}
            </div>
          </div>
        </div>
      </div>

      {/* Fundamentals Panel */}
      {includeFundamentals && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4 flex items-center">
            <BarChart3 className="w-5 h-5 mr-2 text-blue-500" />
            Fundamentals
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Market Cap</div>
              <div className="text-lg font-semibold text-gray-900 dark:text-white">
                {marketData.marketCap ? `$${(marketData.marketCap / 1000000000).toFixed(1)}B` : 'N/A'}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-500 dark:text-gray-400">P/E Ratio</div>
              <div className="text-lg font-semibold text-gray-900 dark:text-white">
                {marketData.peRatio?.toFixed(1) || 'N/A'}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Dividend</div>
              <div className="text-lg font-semibold text-gray-900 dark:text-white">
                {marketData.dividend ? formatCurrency(marketData.dividend) : 'N/A'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Market Depth */}
      {includeDepth && marketDepth && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Market Depth</h3>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-medium text-green-600 dark:text-green-400 mb-2">Bids</h4>
              <div className="space-y-1">
                {marketDepth.bids.slice(0, 5).map((bid, index) => (
                  <div key={index} className="flex justify-between text-sm">
                    <span className="text-green-600 dark:text-green-400">{formatCurrency(bid.price)}</span>
                    <span className="text-gray-600 dark:text-gray-400">{formatNumber(bid.size)}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h4 className="text-sm font-medium text-red-600 dark:text-red-400 mb-2">Asks</h4>
              <div className="space-y-1">
                {marketDepth.asks.slice(0, 5).map((ask, index) => (
                  <div key={index} className="flex justify-between text-sm">
                    <span className="text-red-600 dark:text-red-400">{formatCurrency(ask.price)}</span>
                    <span className="text-gray-600 dark:text-gray-400">{formatNumber(ask.size)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Option Chain */}
      {includeOptions && optionChain.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Option Chain</h3>
          {optionChain.slice(0, 3).map((expiration, index) => (
            <div key={index} className="mb-6">
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Expiration: {new Date(expiration.expirationDate).toLocaleDateString()}
              </h4>
              <div className="overflow-x-auto">
                <table className="min-w-full text-xs">
                  <thead>
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <th className="text-left py-2 text-green-600 dark:text-green-400">Calls</th>
                      <th className="text-center py-2">Strike</th>
                      <th className="text-right py-2 text-red-600 dark:text-red-400">Puts</th>
                    </tr>
                  </thead>
                  <tbody>
                    {expiration.calls.slice(0, 5).map((call, callIndex) => {
                      const put = expiration.puts[callIndex];
                      return (
                        <tr key={callIndex} className="border-b border-gray-100 dark:border-gray-800">
                          <td className="py-1 text-green-600 dark:text-green-400">
                            {formatCurrency(call.bid)} x {formatCurrency(call.ask)}
                          </td>
                          <td className="py-1 text-center font-medium">
                            {formatCurrency(call.strike)}
                          </td>
                          <td className="py-1 text-right text-red-600 dark:text-red-400">
                            {put ? `${formatCurrency(put.bid)} x ${formatCurrency(put.ask)}` : '-'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Corporate Actions */}
      {corporateActions.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4 flex items-center">
            <Clock className="w-5 h-5 mr-2 text-purple-500" />
            Corporate Actions
          </h3>
          <div className="space-y-3">
            {corporateActions.map((action, index) => (
              <div key={index} className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-medium text-gray-900 dark:text-white">{action.type}</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">{action.description}</div>
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    {new Date(action.date).toLocaleDateString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default MarketDataPanel;
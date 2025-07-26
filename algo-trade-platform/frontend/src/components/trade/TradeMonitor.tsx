import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, DollarSign, Target, AlertTriangle } from 'lucide-react';
import { formatCurrency, formatPercentage } from '../../utils/formatters';

interface TradeMonitorProps {
  tradeId: string;
  symbol: string;
  entryPrice: number;
  quantity: number;
  direction: 'long' | 'short';
  stopLoss?: number;
  takeProfit?: number;
  rrTriggerEnabled?: boolean;
  rrTriggerThreshold?: number;
}

interface TradeMetrics {
  currentPrice: number;
  currentPnL: number;
  currentPnLPercent: number;
  currentStopLoss: number;
  riskAmount: number;
  rewardAmount: number;
  riskRewardRatio: number;
  rrTriggerActive: boolean;
  rrTriggerPrice: number;
}

const TradeMonitor: React.FC<TradeMonitorProps> = ({
  tradeId,
  symbol,
  entryPrice,
  quantity,
  direction,
  stopLoss,
  takeProfit,
  rrTriggerEnabled = false,
  rrTriggerThreshold = 1.5
}) => {
  const [metrics, setMetrics] = useState<TradeMetrics>({
    currentPrice: entryPrice,
    currentPnL: 0,
    currentPnLPercent: 0,
    currentStopLoss: stopLoss || 0,
    riskAmount: 0,
    rewardAmount: 0,
    riskRewardRatio: 0,
    rrTriggerActive: false,
    rrTriggerPrice: 0
  });
  
  const [webSocket, setWebSocket] = useState<WebSocket | null>(null);

  useEffect(() => {
    // Setup WebSocket connection for real-time updates
    const ws = new WebSocket(`ws://localhost:8080/api/ws/trades/${tradeId}/monitor`);
    
    ws.onopen = () => {
      console.log(`WebSocket connected for trade ${tradeId}`);
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      updateMetrics(data.currentPrice);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
      console.log('WebSocket connection closed');
    };
    
    setWebSocket(ws);
    
    // Initial calculation
    updateMetrics(entryPrice);
    
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [tradeId]);

  const updateMetrics = (currentPrice: number) => {
    const priceDiff = direction === 'long' 
      ? currentPrice - entryPrice 
      : entryPrice - currentPrice;
    
    const currentPnL = priceDiff * quantity;
    const currentPnLPercent = (priceDiff / entryPrice) * 100;
    
    const riskAmount = stopLoss 
      ? Math.abs(entryPrice - stopLoss) * quantity 
      : 0;
    
    const rewardAmount = takeProfit 
      ? Math.abs(takeProfit - entryPrice) * quantity 
      : 0;
    
    const riskRewardRatio = riskAmount > 0 ? rewardAmount / riskAmount : 0;
    
    // Calculate RR-Trigger
    const rrTriggerPrice = direction === 'long'
      ? entryPrice + (Math.abs(entryPrice - (stopLoss || entryPrice)) * rrTriggerThreshold)
      : entryPrice - (Math.abs(entryPrice - (stopLoss || entryPrice)) * rrTriggerThreshold);
    
    const rrTriggerActive = rrTriggerEnabled && (
      (direction === 'long' && currentPrice >= rrTriggerPrice) ||
      (direction === 'short' && currentPrice <= rrTriggerPrice)
    );
    
    // Update stop loss if RR-Trigger is active
    let currentStopLoss = stopLoss || 0;
    if (rrTriggerActive) {
      currentStopLoss = entryPrice; // Move stop to breakeven
    }
    
    setMetrics({
      currentPrice,
      currentPnL,
      currentPnLPercent,
      currentStopLoss,
      riskAmount,
      rewardAmount,
      riskRewardRatio,
      rrTriggerActive,
      rrTriggerPrice
    });
  };

  const getPnLColor = (pnl: number) => {
    if (pnl > 0) return 'text-green-600 dark:text-green-400';
    if (pnl < 0) return 'text-red-600 dark:text-red-400';
    return 'text-gray-600 dark:text-gray-400';
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white flex items-center">
          <Target className="w-5 h-5 mr-2 text-blue-500" />
          Trade Monitor - {symbol}
        </h3>
        <div className={`px-3 py-1 rounded-full text-sm font-medium ${
          direction === 'long' 
            ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
            : 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200'
        }`}>
          {direction.toUpperCase()}
        </div>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <div className="text-xs text-gray-500 dark:text-gray-400">Entry Price</div>
          <div className="text-lg font-semibold text-gray-900 dark:text-white">
            {formatCurrency(entryPrice)}
          </div>
        </div>
        
        <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <div className="text-xs text-gray-500 dark:text-gray-400">Current Price</div>
          <div className="text-lg font-semibold text-gray-900 dark:text-white">
            {formatCurrency(metrics.currentPrice)}
          </div>
        </div>
        
        <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <div className="text-xs text-gray-500 dark:text-gray-400">Current Stop Loss</div>
          <div className="text-lg font-semibold text-gray-900 dark:text-white">
            {formatCurrency(metrics.currentStopLoss)}
          </div>
          {metrics.rrTriggerActive && (
            <div className="text-xs text-green-600 dark:text-green-400">
              Moved to breakeven
            </div>
          )}
        </div>
        
        <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <div className="text-xs text-gray-500 dark:text-gray-400">Current P&L</div>
          <div className={`text-lg font-semibold ${getPnLColor(metrics.currentPnL)}`}>
            {formatCurrency(metrics.currentPnL)}
          </div>
          <div className={`text-xs ${getPnLColor(metrics.currentPnL)}`}>
            {formatPercentage(metrics.currentPnLPercent)}
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
          <div className="text-xs text-red-600 dark:text-red-400">Risk Amount</div>
          <div className="text-lg font-semibold text-red-700 dark:text-red-300">
            {formatCurrency(metrics.riskAmount)}
          </div>
        </div>
        
        <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
          <div className="text-xs text-green-600 dark:text-green-400">Reward Amount</div>
          <div className="text-lg font-semibold text-green-700 dark:text-green-300">
            {formatCurrency(metrics.rewardAmount)}
          </div>
        </div>
        
        <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
          <div className="text-xs text-blue-600 dark:text-blue-400">Risk/Reward Ratio</div>
          <div className="text-lg font-semibold text-blue-700 dark:text-blue-300">
            1:{metrics.riskRewardRatio.toFixed(2)}
          </div>
        </div>
      </div>
      
      {rrTriggerEnabled && (
        <div className={`p-4 rounded-lg border-l-4 ${
          metrics.rrTriggerActive 
            ? 'bg-green-50 dark:bg-green-900/20 border-green-400'
            : 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-400'
        }`}>
          <div className="flex items-center">
            <AlertTriangle className={`w-5 h-5 mr-2 ${
              metrics.rrTriggerActive ? 'text-green-500' : 'text-yellow-500'
            }`} />
            <div>
              <div className={`text-sm font-medium ${
                metrics.rrTriggerActive 
                  ? 'text-green-800 dark:text-green-200'
                  : 'text-yellow-800 dark:text-yellow-200'
              }`}>
                RR-Trigger {metrics.rrTriggerActive ? 'ACTIVE' : 'MONITORING'}
              </div>
              <div className={`text-xs ${
                metrics.rrTriggerActive 
                  ? 'text-green-700 dark:text-green-300'
                  : 'text-yellow-700 dark:text-yellow-300'
              }`}>
                Trigger Price: {formatCurrency(metrics.rrTriggerPrice)} 
                {metrics.rrTriggerActive && ' - Stop moved to breakeven'}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TradeMonitor;
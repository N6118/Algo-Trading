export interface Trade {
  id: string;
  symbol: string;
  direction: 'long' | 'short';
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  entryTime: string;
  exitTime?: string;
  pnl: number;
  stopLoss?: number;
  takeProfit?: number;
  risk: number;
  strategyId: string;
  strategyName: string;
  status: 'open' | 'closed' | 'pending';
}
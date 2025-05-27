export interface TradeHistory {
  id: string;
  strategyName: string;
  ssType: string;
  ssSignalType: string;
  symbol: string;
  entryQty: number;
  exitQty: number;
  entryPrice: number;
  exitPrice: number;
  pnl: number;
  charges: number;
  netPnl: number;
  netPnlPercent: number;
  entryDate: string;
  exitDate: string;
  status: string;
  comments: string;
}

export interface PerformanceMetrics {
  totalTrades: number;
  winRate: number;
  profitFactor: number;
  averageWin: number;
  averageLoss: number;
  largestWin: number;
  largestLoss: number;
  sharpeRatio: number;
  maxDrawdown: number;
  recoveryFactor: number;
}

export interface PnLData {
  date: string;
  grossPnL: number;
  netPnL: number;
  fees: number;
  commissions: number;
  trades: number;
}
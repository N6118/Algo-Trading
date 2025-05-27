export interface Strategy {
  id: string;
  name: string;
  type: string;
  symbols: string[];
  isActive: boolean;
  performance: number;
  signalCount: number;
  createdAt: string;
  lastUpdated: string;
  description?: string;
  parameters?: {
    timeframe?: string;
    lookbackPeriod?: number;
    signalThreshold?: number;
    expirySettings?: {
      type: 'Weekly' | 'Monthly';
      days: string[];
    };
    ssType?: 'Intraday' | 'Positional';
    tradingDays?: string[];
    timeSettings?: {
      startTime: string;
      endTime: string;
    };
    signalType?: ('Long' | 'Short')[];
    instrument?: 'FUT' | 'OPTION' | 'ETF' | 'Cash Equity';
    optionType?: 'CALL' | 'PUT';
    optionCategory?: 'ITM' | 'OTM' | 'FUT' | 'DOTM' | 'DITM';
    mode?: 'Live' | 'Virtual';
    exchange?: string;
    orderType?: 'Stop' | 'Stop Limit' | 'Market' | 'Limit';
    productType?: 'Margin' | 'Cash';
    baseValue?: number;
  };
  riskManagement?: {
    maxPositionSize?: number;
    stopLossPercent?: number;
    takeProfitPercent?: number;
    maxDrawdownPercent?: number;
  };
}
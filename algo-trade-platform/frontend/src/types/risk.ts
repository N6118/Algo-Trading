export interface RiskMetrics {
  totalExposure: number;
  netExposure: number;
  marginUtilization: number;
  buyingPower: number;
  dayTradesCount: number;
  remainingDayTrades: number;
  accountEquity: number;
  pdtRequirement: number;
  isPdtRestricted: boolean;
  marginCall: boolean;
  valueAtRisk: number;
  maxDrawdown: number;
}

export interface RiskAlert {
  id: string;
  type: 'warning' | 'danger' | 'info';
  message: string;
  timestamp: string;
  acknowledged: boolean;
}

export interface RiskSettings {
  maxStopLossPerTrade: number;
  maxStopLossTotal: number;
  maxPositionSize: number;
  maxLeverage: number;
  marginBuffer: number;
  riskReductionThreshold: number;
  autoHedgeEnabled: boolean;
  trailingStopEnabled: boolean;
  trailingStopPercent: number;
}

export interface RiskReductionRule {
  id: string;
  name: string;
  triggerType: string;
  triggerValue: number;
  action: string;
  quantity: number | string;
  enabled: boolean;
}
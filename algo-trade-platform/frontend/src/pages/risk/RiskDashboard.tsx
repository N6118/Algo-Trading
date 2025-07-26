import { useState, useEffect } from 'react';
import { 
  AlertTriangle, 
  Shield, 
  TrendingDown, 
  TrendingUp, 
  Activity,
  DollarSign,
  BarChart3,
  Clock,
  CheckCircle,
  XCircle,
  RefreshCw,
  Settings,
  Eye,
  Calendar
} from 'lucide-react';
import DashboardCard from '../../components/common/DashboardCard';
import { formatCurrency, formatPercentage, formatDateTime } from '../../utils/formatters';
import toast from 'react-hot-toast';

interface RiskMetrics {
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
  volatilityIndex: number;
  correlationRisk: number;
  concentrationRisk: number;
}

interface RiskAlert {
  id: string;
  type: 'warning' | 'danger' | 'info';
  title: string;
  message: string;
  timestamp: string;
  acknowledged: boolean;
  priority: 'high' | 'medium' | 'low';
}

interface PDTStatus {
  dayTradesUsed: number;
  dayTradesRemaining: number;
  rollingPeriodStart: string;
  rollingPeriodEnd: string;
  isCompliant: boolean;
  minimumEquity: number;
  currentEquity: number;
}

interface MarginUtilization {
  totalMargin: number;
  usedMargin: number;
  availableMargin: number;
  utilizationPercentage: number;
  maintenanceMargin: number;
  excessLiquidity: number;
}

interface SettlementInfo {
  pendingSettlements: Array<{
    symbol: string;
    quantity: number;
    tradeDate: string;
    settlementDate: string;
    value: number;
  }>;
  totalPendingValue: number;
}

const RiskDashboard = () => {
  const [riskMetrics, setRiskMetrics] = useState<RiskMetrics | null>(null);
  const [riskAlerts, setRiskAlerts] = useState<RiskAlert[]>([]);
  const [pdtStatus, setPdtStatus] = useState<PDTStatus | null>(null);
  const [marginUtilization, setMarginUtilization] = useState<MarginUtilization | null>(null);
  const [settlementInfo, setSettlementInfo] = useState<SettlementInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  useEffect(() => {
    fetchRiskData();
    setupWebSocketConnections();
    
    // Set up periodic refresh
    const interval = setInterval(() => {
      fetchRiskData();
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const fetchRiskData = async () => {
    try {
      setIsLoading(true);
      
      // Fetch risk dashboard data
      const dashboardRes = await fetch('/api/risk/dashboard');
      if (dashboardRes.ok) {
        const dashboardData = await dashboardRes.json();
        setRiskMetrics(dashboardData.metrics);
      }

      // Fetch risk alerts
      const alertsRes = await fetch('/api/risk/alerts');
      if (alertsRes.ok) {
        const alertsData = await alertsRes.json();
        setRiskAlerts(alertsData);
      }

      // Fetch PDT status
      const pdtRes = await fetch('/api/risk/pdt/status');
      if (pdtRes.ok) {
        const pdtData = await pdtRes.json();
        setPdtStatus(pdtData);
      }

      // Fetch margin utilization
      const marginRes = await fetch('/api/risk/margin/utilization');
      if (marginRes.ok) {
        const marginData = await marginRes.json();
        setMarginUtilization(marginData);
      }

      // Fetch settlement dates
      const settlementRes = await fetch('/api/risk/settlement/dates');
      if (settlementRes.ok) {
        const settlementData = await settlementRes.json();
        setSettlementInfo(settlementData);
      }

      setLastUpdated(new Date());
    } catch (err) {
      console.error('Failed to fetch risk data:', err);
      // Set mock data for development
      setRiskMetrics({
        totalExposure: 125000,
        netExposure: 85000,
        marginUtilization: 65.5,
        buyingPower: 250000,
        dayTradesCount: 2,
        remainingDayTrades: 1,
        accountEquity: 150000,
        pdtRequirement: 25000,
        isPdtRestricted: false,
        marginCall: false,
        valueAtRisk: 8500,
        maxDrawdown: -12.3,
        volatilityIndex: 18.5,
        correlationRisk: 0.75,
        concentrationRisk: 0.45
      });

      setRiskAlerts([
        {
          id: '1',
          type: 'warning',
          title: 'High Correlation Risk',
          message: 'Multiple positions show high correlation (>0.8). Consider diversification.',
          timestamp: new Date().toISOString(),
          acknowledged: false,
          priority: 'medium'
        },
        {
          id: '2',
          type: 'danger',
          title: 'Approaching Day Trade Limit',
          message: 'You have used 2 of 3 day trades in the rolling 5-day period.',
          timestamp: new Date().toISOString(),
          acknowledged: false,
          priority: 'high'
        }
      ]);

      setPdtStatus({
        dayTradesUsed: 2,
        dayTradesRemaining: 1,
        rollingPeriodStart: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
        rollingPeriodEnd: new Date().toISOString(),
        isCompliant: true,
        minimumEquity: 25000,
        currentEquity: 150000
      });

      setMarginUtilization({
        totalMargin: 100000,
        usedMargin: 65500,
        availableMargin: 34500,
        utilizationPercentage: 65.5,
        maintenanceMargin: 45000,
        excessLiquidity: 55000
      });

      setSettlementInfo({
        pendingSettlements: [
          {
            symbol: 'AAPL',
            quantity: 100,
            tradeDate: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
            settlementDate: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
            value: 18500
          }
        ],
        totalPendingValue: 18500
      });
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const setupWebSocketConnections = () => {
    // Risk dashboard updates
    const riskWs = new WebSocket('ws://localhost:8080/api/ws/risk/dashboard');
    riskWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setRiskMetrics(data.metrics);
    };

    // Risk alerts
    const alertsWs = new WebSocket('ws://localhost:8080/api/ws/risk/alerts');
    alertsWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setRiskAlerts(prev => [data, ...prev]);
      toast.error(`Risk Alert: ${data.title}`);
    };

    // PDT status updates
    const pdtWs = new WebSocket('ws://localhost:8080/api/ws/risk/pdt');
    pdtWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setPdtStatus(data);
    };

    // Margin updates
    const marginWs = new WebSocket('ws://localhost:8080/api/ws/risk/margin');
    marginWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMarginUtilization(data);
    };

    return () => {
      riskWs.close();
      alertsWs.close();
      pdtWs.close();
      marginWs.close();
    };
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchRiskData();
    toast.success('Risk data refreshed');
  };

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      const response = await fetch(`/api/risk/alerts/acknowledge/${alertId}`, {
        method: 'POST',
      });

      if (response.ok) {
        setRiskAlerts(alerts => 
          alerts.map(alert => 
            alert.id === alertId ? { ...alert, acknowledged: true } : alert
          )
        );
        toast.success('Alert acknowledged');
      }
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
      toast.error('Failed to acknowledge alert');
    }
  };

  const getRiskLevel = (value: number, thresholds: { low: number; medium: number }) => {
    if (value <= thresholds.low) return 'low';
    if (value <= thresholds.medium) return 'medium';
    return 'high';
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-600 dark:text-green-400';
      case 'medium': return 'text-yellow-600 dark:text-yellow-400';
      case 'high': return 'text-red-600 dark:text-red-400';
      default: return 'text-gray-600 dark:text-gray-400';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Risk Dashboard</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Monitor risk exposure and compliance status
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
            <span>Last updated:</span>
            <span className="font-medium text-gray-700 dark:text-gray-300">
              {lastUpdated.toLocaleTimeString()}
            </span>
          </div>
          <button 
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center space-x-2 text-sm text-blue-600 dark:text-blue-400 hover:text-blue-500 disabled:opacity-50"
          >
            <RefreshCw size={16} className={isRefreshing ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Risk Alerts */}
      {riskAlerts.filter(alert => !alert.acknowledged).length > 0 && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-center mb-3">
            <AlertTriangle className="w-5 h-5 text-red-500 mr-2" />
            <h3 className="text-lg font-medium text-red-800 dark:text-red-200">Active Risk Alerts</h3>
          </div>
          <div className="space-y-2">
            {riskAlerts.filter(alert => !alert.acknowledged).map((alert) => (
              <div key={alert.id} className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-md">
                <div>
                  <div className="font-medium text-gray-900 dark:text-white">{alert.title}</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">{alert.message}</div>
                </div>
                <button
                  onClick={() => handleAcknowledgeAlert(alert.id)}
                  className="px-3 py-1 text-sm font-medium text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                >
                  Acknowledge
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Risk Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <DashboardCard
          title="Value at Risk (VaR)"
          value={formatCurrency(riskMetrics?.valueAtRisk || 0)}
          change={`${riskMetrics?.maxDrawdown || 0}%`}
          trend={riskMetrics && riskMetrics.maxDrawdown < -10 ? 'down' : 'up'}
          icon={<Shield className="text-red-500" size={20} />}
        />
        
        <DashboardCard
          title="Total Exposure"
          value={formatCurrency(riskMetrics?.totalExposure || 0)}
          change={formatPercentage((riskMetrics?.totalExposure || 0) / (riskMetrics?.accountEquity || 1) * 100)}
          trend="neutral"
          icon={<BarChart3 className="text-blue-500" size={20} />}
        />
        
        <DashboardCard
          title="Margin Utilization"
          value={formatPercentage(riskMetrics?.marginUtilization || 0)}
          trend={riskMetrics && riskMetrics.marginUtilization > 80 ? 'down' : 'up'}
          icon={<DollarSign className="text-purple-500" size={20} />}
        />
        
        <DashboardCard
          title="Day Trades Remaining"
          value={`${riskMetrics?.remainingDayTrades || 0}/3`}
          trend={riskMetrics && riskMetrics.remainingDayTrades <= 1 ? 'down' : 'up'}
          icon={<Clock className="text-yellow-500" size={20} />}
        />
      </div>

      {/* PDT Status and Margin Utilization */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* PDT Rule Compliance */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white flex items-center">
              <Shield className="w-5 h-5 mr-2 text-blue-500" />
              PDT Rule Compliance
            </h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">Status</span>
                <div className="flex items-center">
                  {pdtStatus?.isCompliant ? (
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-500 mr-2" />
                  )}
                  <span className={`text-sm font-medium ${
                    pdtStatus?.isCompliant ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {pdtStatus?.isCompliant ? 'Compliant' : 'Non-Compliant'}
                  </span>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">Day Trades Used</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {pdtStatus?.dayTradesUsed || 0} / 3
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">Current Equity</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {formatCurrency(pdtStatus?.currentEquity || 0)}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">Minimum Required</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {formatCurrency(pdtStatus?.minimumEquity || 25000)}
                </span>
              </div>
              
              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Rolling Period: {pdtStatus && formatDateTime(pdtStatus.rollingPeriodStart)} - {pdtStatus && formatDateTime(pdtStatus.rollingPeriodEnd)}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Margin Utilization */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white flex items-center">
              <DollarSign className="w-5 h-5 mr-2 text-purple-500" />
              Reg-T Margin Utilization
            </h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">Total Margin</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {formatCurrency(marginUtilization?.totalMargin || 0)}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">Used Margin</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {formatCurrency(marginUtilization?.usedMargin || 0)}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">Available Margin</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {formatCurrency(marginUtilization?.availableMargin || 0)}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">Utilization</span>
                <span className={`text-sm font-medium ${
                  (marginUtilization?.utilizationPercentage || 0) > 80 ? 'text-red-600' : 'text-green-600'
                }`}>
                  {formatPercentage(marginUtilization?.utilizationPercentage || 0)}
                </span>
              </div>
              
              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${
                      (marginUtilization?.utilizationPercentage || 0) > 80 ? 'bg-red-500' : 'bg-blue-500'
                    }`}
                    style={{ width: `${Math.min(marginUtilization?.utilizationPercentage || 0, 100)}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Settlement Tracker */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white flex items-center">
            <Calendar className="w-5 h-5 mr-2 text-green-500" />
            Settlement Tracker (T+2)
          </h2>
        </div>
        <div className="p-6">
          {settlementInfo?.pendingSettlements.length ? (
            <div className="space-y-3">
              {settlementInfo.pendingSettlements.map((settlement, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div>
                    <div className="font-medium text-gray-900 dark:text-white">{settlement.symbol}</div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {settlement.quantity} shares • Trade: {formatDateTime(settlement.tradeDate)}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium text-gray-900 dark:text-white">
                      {formatCurrency(settlement.value)}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      Settles: {formatDateTime(settlement.settlementDate)}
                    </div>
                  </div>
                </div>
              ))}
              <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
                <div className="flex justify-between items-center">
                  <span className="font-medium text-gray-900 dark:text-white">Total Pending</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {formatCurrency(settlementInfo.totalPendingValue)}
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              No pending settlements
            </div>
          )}
        </div>
      </div>

      {/* Risk Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Exposure Breakdown */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white">Risk Exposure Breakdown</h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">Volatility Risk</span>
                <div className="flex items-center">
                  <span className={`text-sm font-medium ${
                    getRiskColor(getRiskLevel(riskMetrics?.volatilityIndex || 0, { low: 15, medium: 25 }))
                  }`}>
                    {riskMetrics?.volatilityIndex.toFixed(1)}%
                  </span>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">Correlation Risk</span>
                <div className="flex items-center">
                  <span className={`text-sm font-medium ${
                    getRiskColor(getRiskLevel(riskMetrics?.correlationRisk || 0, { low: 0.5, medium: 0.7 }))
                  }`}>
                    {riskMetrics?.correlationRisk.toFixed(2)}
                  </span>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">Concentration Risk</span>
                <div className="flex items-center">
                  <span className={`text-sm font-medium ${
                    getRiskColor(getRiskLevel(riskMetrics?.concentrationRisk || 0, { low: 0.3, medium: 0.5 }))
                  }`}>
                    {riskMetrics?.concentrationRisk.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white">Quick Actions</h2>
          </div>
          <div className="p-6">
            <div className="space-y-3">
              <button className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium">
                <Settings className="w-4 h-4 mr-2" />
                Risk Settings
              </button>
              
              <button className="w-full flex items-center justify-center px-4 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md text-sm font-medium">
                <Eye className="w-4 h-4 mr-2" />
                View All Alerts
              </button>
              
              <button className="w-full flex items-center justify-center px-4 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md text-sm font-medium">
                <Activity className="w-4 h-4 mr-2" />
                Risk Report
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RiskDashboard;
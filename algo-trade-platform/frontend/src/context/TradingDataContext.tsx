import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { Strategy } from '../types/strategy';
import { Trade } from '../types/trade';

interface TradingDataContextType {
  strategies: Strategy[];
  activeStrategies: Strategy[];
  activeTrades: Trade[];
  dailyPnL: number;
  weeklyPnL: number;
  monthlyPnL: number;
  allTimePnL: number;
  performanceHistory: {
    date: string;
    value: number;
  }[];
  isLoading: boolean;
  error: string | null;
  refreshData: () => Promise<void>;
}

const TradingDataContext = createContext<TradingDataContextType | undefined>(undefined);

export const useTradingData = () => {
  const context = useContext(TradingDataContext);
  if (context === undefined) {
    throw new Error('useTradingData must be used within a TradingDataProvider');
  }
  return context;
};

interface TradingDataProviderProps {
  children: ReactNode;
}

export const TradingDataProvider = ({ children }: TradingDataProviderProps) => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [activeTrades, setActiveTrades] = useState<Trade[]>([]);
  const [performanceHistory, setPerformanceHistory] = useState<{ date: string; value: number }[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // PnL values
  const [dailyPnL, setDailyPnL] = useState(1250.75);
  const [weeklyPnL, setWeeklyPnL] = useState(4820.32);
  const [monthlyPnL, setMonthlyPnL] = useState(12450.87);
  const [allTimePnL, setAllTimePnL] = useState(84320.55);
  
  const generateMockData = useCallback(() => {
    // Mock strategies data with better validation
    const mockStrategies: Strategy[] = [
      {
        id: 'strategy-1',
        name: 'AAPL Momentum',
        type: 'momentum',
        symbols: ['AAPL'],
        isActive: true,
        performance: 12.45,
        signalCount: 2,
        createdAt: '2023-04-15T08:30:00Z',
        lastUpdated: new Date().toISOString(),
        description: 'Momentum-based strategy for AAPL stock',
        parameters: {
          timeframe: '1d',
          lookbackPeriod: 20,
          signalThreshold: 2.0
        }
      },
      {
        id: 'strategy-2',
        name: 'SPY-QQQ Correlation',
        type: 'correlation',
        symbols: ['SPY', 'QQQ'],
        isActive: true,
        performance: 8.32,
        signalCount: 0,
        createdAt: '2023-03-10T14:22:00Z',
        lastUpdated: new Date().toISOString(),
        description: 'Correlation trading between SPY and QQQ'
      },
      {
        id: 'strategy-3',
        name: 'TSLA Mean Reversion',
        type: 'mean_reversion',
        symbols: ['TSLA'],
        isActive: false,
        performance: -3.21,
        signalCount: 0,
        createdAt: '2023-05-05T09:15:00Z',
        lastUpdated: new Date().toISOString(),
        description: 'Mean reversion strategy for TSLA'
      },
      {
        id: 'strategy-4',
        name: 'Tech Sector Breakout',
        type: 'breakout',
        symbols: ['MSFT', 'GOOG', 'META', 'AMZN'],
        isActive: true,
        performance: 15.78,
        signalCount: 1,
        createdAt: '2023-02-20T11:45:00Z',
        lastUpdated: new Date().toISOString(),
        description: 'Breakout strategy for tech stocks'
      },
      {
        id: 'strategy-5',
        name: 'Gold-Silver Ratio',
        type: 'correlation',
        symbols: ['GLD', 'SLV'],
        isActive: true,
        performance: 5.67,
        signalCount: 0,
        createdAt: '2023-04-28T16:10:00Z',
        lastUpdated: new Date().toISOString(),
        description: 'Gold-Silver ratio trading strategy'
      }
    ];
    
    // Mock active trades data with better validation
    const mockTrades: Trade[] = [
      {
        id: 'trade-1',
        symbol: 'AAPL',
        direction: 'long',
        quantity: 100,
        entryPrice: 182.75,
        currentPrice: 187.32,
        entryTime: '2023-06-01T09:32:15Z',
        pnl: 457.00,
        stopLoss: 175.50,
        takeProfit: 195.00,
        risk: 725.00,
        strategyId: 'strategy-1',
        strategyName: 'AAPL Momentum',
        status: 'open'
      },
      {
        id: 'trade-2',
        symbol: 'SPY',
        direction: 'long',
        quantity: 50,
        entryPrice: 437.82,
        currentPrice: 442.15,
        entryTime: '2023-06-02T10:15:30Z',
        pnl: 216.50,
        stopLoss: 430.00,
        takeProfit: 450.00,
        risk: 390.00,
        strategyId: 'strategy-2',
        strategyName: 'SPY-QQQ Correlation',
        status: 'open'
      },
      {
        id: 'trade-3',
        symbol: 'MSFT',
        direction: 'long',
        quantity: 25,
        entryPrice: 325.40,
        currentPrice: 332.18,
        entryTime: '2023-06-03T14:42:10Z',
        pnl: 169.50,
        stopLoss: 318.00,
        takeProfit: 340.00,
        risk: 185.00,
        strategyId: 'strategy-4',
        strategyName: 'Tech Sector Breakout',
        status: 'open'
      },
      {
        id: 'trade-4',
        symbol: 'META',
        direction: 'short',
        quantity: 20,
        entryPrice: 283.75,
        currentPrice: 278.50,
        entryTime: '2023-06-03T15:10:45Z',
        pnl: 105.00,
        stopLoss: 290.00,
        takeProfit: 270.00,
        risk: 125.00,
        strategyId: 'strategy-4',
        strategyName: 'Tech Sector Breakout',
        status: 'open'
      },
      {
        id: 'trade-5',
        symbol: 'GLD',
        direction: 'long',
        quantity: 40,
        entryPrice: 182.30,
        currentPrice: 184.75,
        entryTime: '2023-06-04T09:25:50Z',
        pnl: 98.00,
        stopLoss: 179.50,
        takeProfit: 187.00,
        risk: 112.00,
        strategyId: 'strategy-5',
        strategyName: 'Gold-Silver Ratio',
        status: 'open'
      }
    ];
    
    // Generate more realistic performance history
    const mockPerformanceHistory = Array.from({ length: 30 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (29 - i));
      
      // Create more realistic performance data with volatility
      const baseValue = 100000;
      const trend = i * 500; // Upward trend
      const volatility = Math.sin(i * 0.5) * 2000; // Some cyclical movement
      const randomNoise = (Math.random() - 0.5) * 1000; // Random noise
      
      return {
        date: date.toISOString().split('T')[0],
        value: Math.max(baseValue + trend + volatility + randomNoise, 90000) // Ensure minimum value
      };
    });
    
    return { mockStrategies, mockTrades, mockPerformanceHistory };
  }, []);
  
  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const { mockStrategies, mockTrades, mockPerformanceHistory } = generateMockData();
      
      setStrategies(mockStrategies);
      setActiveTrades(mockTrades);
      setPerformanceHistory(mockPerformanceHistory);
    } catch (err) {
      console.error('Error fetching trading data:', err);
      setError('Failed to fetch trading data. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  }, [generateMockData]);
  
  // Fetch data on component mount
  useEffect(() => {
    fetchData();
  }, [fetchData]);
  
  // Filter active strategies
  const activeStrategies = strategies.filter(strategy => strategy.isActive);
  
  const refreshData = useCallback(async () => {
    await fetchData();
  }, [fetchData]);
  
  return (
    <TradingDataContext.Provider value={{
      strategies,
      activeStrategies,
      activeTrades,
      dailyPnL,
      weeklyPnL,
      monthlyPnL,
      allTimePnL,
      performanceHistory,
      isLoading,
      error,
      refreshData
    }}>
      {children}
    </TradingDataContext.Provider>
  );
};
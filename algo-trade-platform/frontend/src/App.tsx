import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

import MainLayout from './layouts/MainLayout';
import AuthLayout from './layouts/AuthLayout';

// Auth Pages
import Login from './pages/auth/Login';
import UserProfile from './pages/auth/UserProfile';

// Dashboard Pages
import MainDashboard from './pages/dashboard/MainDashboard';
import StrategyDashboard from './pages/dashboard/StrategyDashboard';

// Strategy Pages
import StrategyList from './pages/strategy/StrategyList';
import StrategyEditor from './pages/strategy/StrategyEditor';
import CorrelationStrategy from './pages/strategy/CorrelationStrategy';

// Trade Pages
import ActiveTrades from './pages/trade/ActiveTrades';
import TradeDetail from './pages/trade/TradeDetail';
import PreTradeAnalysis from './pages/trade/PreTradeAnalysis';

// Risk Pages
import RiskDashboard from './pages/risk/RiskDashboard';
import RiskSettings from './pages/risk/RiskSettings';

// Reporting Pages
import DealsReport from './pages/reporting/DealsReport';
import PnLReport from './pages/reporting/PnLReport';

// Additional Pages
import Performance from './pages/performance/Performance';
import Markets from './pages/markets/Markets';
import Accounts from './pages/accounts/Accounts';

import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { TradingDataProvider } from './context/TradingDataContext';

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <TradingDataProvider>
          <Router>
            <Toaster position="top-right" />
            <Routes>
              <Route path="/auth" element={<AuthLayout />}>
                <Route path="login" element={<Login />} />
              </Route>
              <Route path="/" element={<MainLayout />}>
                <Route index element={<MainDashboard />} />
                <Route path="profile" element={<UserProfile />} />
                <Route path="strategy">
                  <Route index element={<StrategyList />} />
                  <Route path="new" element={<StrategyEditor />} />
                  <Route path="edit/:id" element={<StrategyEditor />} />
                  <Route path="correlation" element={<CorrelationStrategy />} />
                  <Route path="dashboard/:id" element={<StrategyDashboard />} />
                </Route>
                <Route path="trades">
                  <Route index element={<ActiveTrades />} />
                  <Route path=":id" element={<TradeDetail />} />
                  <Route path="analysis" element={<PreTradeAnalysis />} />
                </Route>
                <Route path="risk">
                  <Route index element={<RiskDashboard />} />
                  <Route path="settings" element={<RiskSettings />} />
                </Route>
                <Route path="reports">
                  <Route path="deals" element={<DealsReport />} />
                  <Route path="pnl" element={<PnLReport />} />
                </Route>
                <Route path="performance" element={<Performance />} />
                <Route path="markets" element={<Markets />} />
                <Route path="accounts" element={<Accounts />} />
              </Route>
            </Routes>
          </Router>
        </TradingDataProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
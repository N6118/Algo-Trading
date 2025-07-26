import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  BarChart2, 
  Briefcase, 
  ChevronDown, 
  Clock, 
  Cpu, 
  LayoutDashboard, 
  LineChart, 
  Settings,
  FileText,
  TrendingUp, 
  Users
} from 'lucide-react';

interface SidebarProps {
  open: boolean;
  setOpen: (open: boolean) => void;
}

interface MenuItem {
  name: string;
  icon: JSX.Element;
  path: string;
  children?: { name: string; path: string }[];
}

const Sidebar = ({ open, setOpen }: SidebarProps) => {
  const location = useLocation();
  const [expandedMenu, setExpandedMenu] = useState<string | null>(null);
  
  const menuItems: MenuItem[] = [
    {
      name: 'Dashboard',
      icon: <LayoutDashboard size={20} />,
      path: '/',
    },
    {
      name: 'Strategies',
      icon: <Cpu size={20} />,
      path: '/strategy',
      children: [
        { name: 'All Strategies', path: '/strategy' },
        { name: 'Create New', path: '/strategy/new' },
        { name: 'Correlation Strategy', path: '/strategy/correlation' },
      ],
    },
    {
      name: 'Trades',
      icon: <TrendingUp size={20} />,
      path: '/trades',
      children: [
        { name: 'Active Trades', path: '/trades' },
        { name: 'Pre-Trade Analysis', path: '/trades/analysis' },
      ],
    },
    {
      name: 'Performance',
      icon: <LineChart size={20} />,
      path: '/performance',
    },
    {
      name: 'Markets',
      icon: <BarChart2 size={20} />,
      path: '/markets',
    },
    {
      name: 'Accounts',
      icon: <Briefcase size={20} />,
      path: '/accounts',
    },
    {
      name: 'History',
      icon: <Clock size={20} />,
      path: '/history',
    },
    {
      name: 'Reports',
      icon: <FileText size={20} />,
      path: '/reports',
      children: [
        { name: 'Deals Report', path: '/reports/deals' },
        { name: 'P&L Report', path: '/reports/pnl' },
      ],
    },
  ];
  
  const toggleExpanded = (name: string) => {
    if (expandedMenu === name) {
      setExpandedMenu(null);
    } else {
      setExpandedMenu(name);
    }
  };
  
  const isActive = (path: string) => {
    return location.pathname === path;
  };
  
  return (
    <div 
      className={`${
        open ? 'translate-x-0' : '-translate-x-full'
      } fixed inset-y-0 left-0 z-30 w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-auto lg:w-72`}
    >
      <div className="flex flex-col h-full">
        <div className="h-16 flex items-center px-6 border-b border-gray-200 dark:border-gray-700">
          <Link to="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary-600 rounded-md flex items-center justify-center">
              <TrendingUp size={20} className="text-white" />
            </div>
            <span className="text-xl font-bold text-gray-900 dark:text-white">AlgoTrader</span>
          </Link>
        </div>
        
        <div className="flex-1 overflow-y-auto py-4">
          <ul className="space-y-1 px-3">
            {menuItems.map((item) => (
              <li key={item.name}>
                {item.children ? (
                  <div>
                    <button
                      onClick={() => toggleExpanded(item.name)}
                      className={`flex items-center justify-between w-full px-3 py-2 text-sm rounded-md ${
                        location.pathname.startsWith(item.path)
                          ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400'
                          : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                      }`}
                    >
                      <div className="flex items-center">
                        <span className="mr-3">{item.icon}</span>
                        <span>{item.name}</span>
                      </div>
                      <ChevronDown
                        size={16}
                        className={`transform transition-transform ${
                          expandedMenu === item.name ? 'rotate-180' : ''
                        }`}
                      />
                    </button>
                    
                    {expandedMenu === item.name && (
                      <ul className="mt-1 ml-8 space-y-1">
                        {item.children.map((child) => (
                          <li key={child.name}>
                            <Link
                              to={child.path}
                              className={`block px-3 py-2 text-sm rounded-md ${
                                isActive(child.path)
                                  ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400'
                                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                              }`}
                            >
                              {child.name}
                            </Link>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                ) : (
                  <Link
                    to={item.path}
                    className={`flex items-center px-3 py-2 text-sm rounded-md ${
                      isActive(item.path)
                        ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                  >
                    <span className="mr-3">{item.icon}</span>
                    <span>{item.name}</span>
                  </Link>
                )}
              </li>
            ))}
          </ul>
        </div>
        
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <Link
            to="/settings"
            className="flex items-center px-3 py-2 text-sm rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <Settings size={20} className="mr-3" />
            <span>Settings</span>
          </Link>
          
          <div className="mt-4">
            <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">System Status</div>
            <div className="flex items-center">
              <div className="w-2 h-2 rounded-full bg-green-500 mr-2"></div>
              <span className="text-sm text-gray-600 dark:text-gray-300">All systems operational</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;